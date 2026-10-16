#!/usr/bin/env python3
"""self-funding agent 的毛利模型：一台"自己找工作、自己充值"的 agent 到底赚不赚钱。

只依赖标准库。直接运行：
    python3 poc/margin_model.py
所有数字来自 2026-10 公开资料（见 docs/self-funding-agent-feasibility.md 的引用表）：
  - agent 零工市场单价：$8-$35 集中区间（dealwork.ai / Toku / ugig 实测），个别到 $200
  - 报价踩踏：$15-$20 的标单实际以 $4.50-$5.00 成交（Toku 实测）
  - 平台抽成：MoltJobs 5%、dealwork 10%、Toku/ugig 15-20%
  - 中标所需报价数：3-7 个报价（dealwork）到 10-30 个（Toku），$5 任务 188 次报价
  - 模型价格（2026）：Sonnet 级 $3/$15 每百万 token（标准价），DeepSeek V4-Pro 输出 $0.87/MTok
  - 一次 agent 交付的 token 量：本模型默认 60k input / 25k output（含检索、写作、返工）
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass
class Pricing:
    """推理成本参数（$/百万 token）。"""

    in_per_mtok: float = 3.0
    out_per_mtok: float = 15.0
    cache_in_per_mtok: float = 0.30
    cache_ratio: float = 0.55  # 长系统提示 + 工具定义可命中缓存的比例

    def cost_usd(self, tok_in: float, tok_out: float) -> float:
        cached = tok_in * self.cache_ratio
        fresh = tok_in - cached
        return (
            fresh / 1e6 * self.in_per_mtok
            + cached / 1e6 * self.cache_in_per_mtok
            + tok_out / 1e6 * self.out_per_mtok
        )


@dataclass
class Gig:
    """一次接活-交付-收款循环。"""

    listed_price: float = 20.0        # 平台标价
    bid_undercut: float = 0.32        # 成交价 / 标价（踩踏后）
    bids_to_win: float = 6.0          # 需要投多少次标才中一单
    bid_tokens: tuple = (4_000, 900)  # 每次投标的搜索+写标书 token
    work_tokens: tuple = (60_000, 25_000)
    rework_rate: float = 0.25         # 交付被打回、需重做的比例
    rework_tokens: tuple = (25_000, 12_000)
    platform_fee: float = 0.10
    nonpayment_rate: float = 0.08     # 交付了但钱没到（agent 市场的常态）
    gas_per_tx: float = 0.001         # Base 上 x402/USDC 结算，fraction of a cent
    pricing: Pricing = field(default_factory=Pricing)

    @property
    def gross(self) -> float:
        return self.listed_price * self.bid_undercut * (1 - self.platform_fee)

    @property
    def expected_gross(self) -> float:
        return self.gross * (1 - self.nonpayment_rate)

    @property
    def bid_cost(self) -> float:
        return self.pricing.cost_usd(*self.bid_tokens)

    @property
    def work_cost(self) -> float:
        return self.pricing.cost_usd(*self.work_tokens) + self.gas_per_tx

    @property
    def rework_cost(self) -> float:
        if self.rework_rate <= 0:
            return 0.0
        return self.rework_rate * self.pricing.cost_usd(*self.rework_tokens)

    @property
    def cost_per_win(self) -> float:
        """中一单的真实成本 = 投标成本 * bids_to_win + 交付 + 返工。"""
        return self.bid_cost * self.bids_to_win + self.work_cost + self.rework_cost

    @property
    def margin_per_win(self) -> float:
        return self.expected_gross - self.cost_per_win

    def render(self, title: str = "") -> str:
        lines = []
        if title:
            lines.append(f"  ▶ {title}")
        lines += [
            f"    中标后到手毛利      ${self.expected_gross:8.4f}"
            f"   (标价 ${self.listed_price:.2f} × 折价 {self.bid_undercut:.0%}"
            f" × 扣平台 {self.platform_fee:.0%} × 到账概率 {1 - self.nonpayment_rate:.0%})",
            f"    投标沉没成本        ${self.bid_cost * self.bids_to_win:8.4f}"
            f"   ({self.bids_to_win:.0f} 次 × ${self.bid_cost:.4f})",
            f"    交付推理成本        ${self.work_cost:8.4f}"
            f"   ({self.work_tokens[0] + self.work_tokens[1]:,} tok)",
            f"    返工成本            ${self.rework_cost:8.4f}"
            f"   ({self.rework_rate:.0%} 概率被打回)",
            f"    每单净贡献          ${self.margin_per_win:8.4f}"
            f"   {'✅ 有毛利' if self.margin_per_win > 0 else '❌ 亏钱'}",
        ]
        return "\n".join(lines)


@dataclass
class IdleBurn:
    """不做活时的固定燃烧：心跳、上下文维护、健康检查、VPS。"""

    turns_per_day: int = 48          # 每天醒来看一次有没有活
    tokens_per_turn: tuple = (12_000, 400)
    vps_per_day: float = 0.02        # $0.6/月 级别的小机器
    pricing: Pricing = field(default_factory=Pricing)

    @property
    def per_day(self) -> float:
        inflow = self.pricing.cost_usd(self.tokens_per_turn[0], 0) * self.turns_per_day
        outflow = self.pricing.cost_usd(0, self.tokens_per_turn[1]) * self.turns_per_day
        return inflow + outflow + self.vps_per_day


def break_even_price(cost_per_win: float, platform_fee: float, undercut: float,
                     nonpayment: float) -> float:
    """要让净贡献 ≥ 0，成交单价至少要多少（换算回平台标价）。"""
    net = (1 - platform_fee) * (1 - nonpayment) * undercut
    return cost_per_win / net


def cheap_pricing() -> Pricing:
    """把模型换成 DeepSeek 级开源权重 API，成本立刻掉一个数量级。"""
    return Pricing(in_per_mtok=0.28, out_per_mtok=0.87, cache_in_per_mtok=0.0036, cache_ratio=0.7)


def main() -> None:
    print("=" * 78)
    print("场景 A：agent 零工市场（dealwork / Toku / ugig 实测参数），用 Sonnet 级模型")
    print("=" * 78)
    g = Gig()
    print(g.render("$20 标价的通用任务（研究/整理/文档）"))
    idle = IdleBurn()
    per_day_from_wins = g.margin_per_win
    wins_per_day = 3.0
    print(f"\n    假设每天中标 {wins_per_day:.0f} 单（现实中几乎不可能，见文末单量敏感性表）")
    print(f"    干活贡献              ${per_day_from_wins * wins_per_day:+.3f}/天")
    print(f"    空转燃烧（心跳+VPS）    → 成本  -${idle.per_day:.3f}/天")
    print(f"    日净利                    ${per_day_from_wins * wins_per_day - idle.per_day:+.3f}/天")

    print("\n" + "=" * 78)
    print("场景 B：同一批活，但价格被踩到地板（Toku 实测：$15-20 标价以 $4.5-5 成交）")
    print("=" * 78)
    print(replace(g, listed_price=15.0, bid_undercut=0.30, bids_to_win=18.0).render("$15 标价，18 次投标抢 1 单"))

    print("\n" + "=" * 78)
    print("场景 C：换成中国开源权重模型（DeepSeek V4-Pro 级 $0.28/$0.87 per MTok）")
    print("=" * 78)
    print(replace(g, pricing=cheap_pricing()).render("同样的活，仅推理成本下降"))
    print("\n  注：模型降级会同时拉低交付质量 → 返工率与被打回率上升，本表未建模，是主要不确定项。")

    print("\n" + "=" * 78)
    print("场景 D：不走平台，自己挂 x402 端点（无平台抽成，但要自己获客）")
    print("=" * 78)
    d = replace(g, listed_price=0.01, bid_undercut=1.0, bids_to_win=1.0,
                work_tokens=(200_000, 3_000), rework_rate=0.0,
                platform_fee=0.0, nonpayment_rate=0.0, pricing=cheap_pricing())
    print(d.render("每条 $0.01 的订阅式数据/摘要端点，一次调用摊薄全量上下文"))
    print("    → 单次几乎零边际成本，但 962 次访问 / 962 个不同 IP / 0 次付费（真实自述账本）")
    print("    → 卡点是需求侧，不是成本侧。")

    print("\n" + "=" * 78)
    print("盈亏平衡：每单成本 vs 需要的成交单价")
    print("=" * 78)
    print(f"{'每单成本':>10} | {'Sonnet级需标价':>16} | {'DeepSeek级需标价':>18}")
    for cost in (0.25, 0.5, 1.0, 2.0, 5.0):
        son = break_even_price(cost, g.platform_fee, g.bid_undercut, g.nonpayment_rate)
        deep = break_even_price(cost * 0.18, 0.10, 0.55, 0.05)
        print(f"${cost:9.2f} | ${son:15.2f} | ${deep:17.2f}")

    print("\n" + "=" * 78)
    print("真正的约束不是毛利率，是日单量：单量敏感性（Sonnet 级模型，$20 标价场景）")
    print("=" * 78)
    print(f"{'中标/天':>8} | {'来源（公开实测）':<26} | {'日净利':>10} | {'覆盖 $5 充值档位需':>16}")
    rows = [
        (0.0,  "MoltJobs：7 个 $5 挂单，0 单结算"),
        (0.05, "dealwork 实测：两周 7 单"),
        (0.11, "自述账本：9 天 $23，1 个买家"),
        (0.5,  "乐观：agent 每天中 1 单、每周休 3 天"),
        (3.0,  "幻想：需要稳定客源 + 人做验收"),
    ]
    for wins, why in rows:
        net = g.margin_per_win * wins - idle.per_day
        days_for_5usd = "∞（永远打不平）" if net <= 0 else f"${5 / net:8.1f} 天攒出 $5"
        print(f"{wins:8.2f} | {why:<26} | ${net:+8.3f} | {days_for_5usd}")

    print("""
判读（这才是结论）：
  · 单位毛利在 2026 年为正：一次 85k token 的交付，Sonnet 级 ~$0.47、DeepSeek 级 ~$0.03，
    而踩价后的 agent 零工单价仍有 $4-$6。所以"能不能赚到钱"不是模型能力问题。
  · 但 agent 零工市场是"卖方无限、买方几乎没有"的结构：$5 的任务 188 次报价、
    两周合计 7 单、挂单不结算 —— 期望日收入 < 期望日燃烧。
  · 因此"自己充值"在数学上等价于：每天必须稳定中标 ≥ 0.5 单，或把单价做到 $50+ 的
    非零工市场（订阅、bounty、企业 API）。零工市场这条路目前养不活自己。
  · 反过来说，把心跳从 48 次/天降到 4 次 + 用缓存把空转成本压到 < $0.1/天，
    生存门槛就从 0.5 单/天 降到 ~0.03 单/天 —— 降燃烧比抓收入更容易，先做这个。
""")


if __name__ == "__main__":
    main()
