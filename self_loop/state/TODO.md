# TODO: 无限循环挖掘课题

> **课题原文（用户 2026-10-16 第一次提示词，锁定不得擅改）：**
> "仔细搜索有没有工具能够让agent工具反复提交相同的提示词 回答完成后自动再次发送提示词 让它无限研究挖掘某个课题 直到极限上下文"

## Open questions
- [ ] 全景地图：穷尽所有能实现"agent 回答完自动重发同一提示词、无限循环挖掘"的工具/框架/机制（已知起点见 PROGRESS iter 0：Ralph/ralph-loop、/goal、Stop hook、AutoGen、LangGraph、Letta、GPT Researcher、STORM…），逐项给出：机制原理 / 触发方式 / 终止条件 / 上下文管理方式
- [ ] "再次发送"的实现层深挖：hook 拦截、while 循环重注入、termination condition、heartbeat、cron 各自如何触发重发；谁（用户/脚本/第二个模型/平台）在判定"该继续"
- [ ] "直到极限上下文"的四种工程路线对比与失效模式：auto-compact / subagent 分治 / 外部记忆（Letta-MemGPT、Mem0、Zep）/ fresh-context+状态落盘
- [ ] 防失控机制：饱和判定、重复动作检测（tool-call fingerprint）、token/轮数预算、block cap、rate-limit 自动续跑 —— 各成熟工具怎么实现
- [ ] 实战配方：每种方案的最小可运行配置（命令级）+ 成本/质量/可靠性权衡表
- [ ] 商业托管型 deep research（ChatGPT/Gemini/Perplexity Deep Research、Manus）的内部循环机制与自研方案的差异
