# exp

## 调研：让 agent 自己找工作赚钱 → 给自己充值 → 多余的钱存起来，可行吗？

- 主报告：[`docs/self-funding-agent-feasibility.md`](docs/self-funding-agent-feasibility.md)
- 毛利模型（为什么亏不在推理成本而在单量）：`python3 poc/margin_model.py`
- 资金拓扑与权限围栏（四池 + mandate + 幂等 + 单向储蓄）：
  - `python3 poc/policy_engine.py`　演示 7 个场景（含 prompt injection 掏空钱包）
  - `python3 poc/policy_engine.py --test`　8 条安全不变量断言

一句话结论：**闭环能跑通（收款/充值/储蓄都已产品化），但「合法 + 完全无人 + 净赚钱」三者现在不能同时成立；截至 2026-10 没有公开可核验案例证明某个 agent 的收入持续覆盖了它自己的运行成本。**
