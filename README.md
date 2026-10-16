# self_loop —— 让 agent 无限循环挖掘课题的工具

把「同一提示词反复注入 → 每轮研究 → 发现落盘 → 自动下一轮」固化成一个
**协议（PROTOCOL.md）+ 状态机（tick.sh + state/）** 的自包含工具。
在支持多工具调用的 agent 会话里（如 Arena），它会一直挖到**信息饱和**或用户叫停；
上下文撞墙不是终点 —— 状态全在磁盘，撞墙就滚入新回合，循环无损继续。

## 新窗口加载（30 秒）

1. 开新会话（同一仓库、同一分支）
2. 对 agent 说一句话：**「读取 self_loop/LOAD.md 并严格按它执行」**
3. 之后每个回合结束会弹出【继续挖下一轮】【停止并写报告】【换方向】——点"继续"就转下去，
   直到 agent 判定饱和自动写 `self_loop/state/REPORT.md`，或你随时叫停

**当前课题**（记录在 `state/TODO.md`，= 本工具诞生时的原始提示词，可换成任意课题）：
> 仔细搜索有没有工具能够让agent工具反复提交相同的提示词 回答完成后自动再次发送提示词 让它无限研究挖掘某个课题 直到极限上下文

## 文件结构

```
self_loop/
├── LOAD.md            ★ 新会话加载入口（agent 的启动契约，先读这个）
├── PROTOCOL.md        固定提示词（每轮原样执行的完整规则）
├── tick.sh            状态机加载器：每轮开头渲染 迭代号/下一问/最近发现
├── state/             循环的记忆（git 追踪，跨窗口跨回合无损）
│   ├── TODO.md        课题原文 + 开放问题队列
│   ├── PROGRESS.md    已验证发现（iter 0 = 会话 1 的成果种子）
│   └── ITERATIONS.md  逐轮日志（审计轨迹）
├── examples/          演示课题"量子纠错"的完整 2 轮运行样例
└── claude-code-kit/   模式 B：Claude Code CLI 版（headless 循环 + Stop hook）
```

## 工作原理（为什么是"无限"）

- **回合内**：tick → 取下一问 → web_search/fetch_page → 落盘 → 立即下一轮，全自动，无需人介入。
- **回合间**：agent 无法给自己发消息（平台限制），所以用 `ask_user` 一键心跳；
  新回合先 `tick.sh` 从磁盘恢复 = 零记忆损失。
- **终点**：信息饱和（TODO 耗尽 或 连续 2 轮零新发现）→ 自动写 REPORT.md。
  防空转：禁止重复已覆盖问题；不编造来源；冲突需 ≥2 独立来源裁决。

## 模式 B（可选）：Claude Code CLI 版

`self_loop/claude-code-kit/` —— 给 Claude Code 2.1+ 用的同一套机制：
`research-loop.sh`（headless while 循环，fresh-context + 状态落盘）与
`hooks/ralph-stop.sh` + `enable-stop-hook.sh`（交互式 Stop hook，= 官方 ralph-loop 插件机制）。
需要 `ANTHROPIC_API_KEY` 且机器可访问 api.anthropic.com。
