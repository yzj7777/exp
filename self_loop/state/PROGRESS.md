# PROGRESS: 无限循环挖掘课题

## [iter 0] bootstrap —— 会话 1 的成果整理（工具搭建期已有发现，作为循环起点种子）

### A. 工具全景（2026-10-16 已搜索验证）
- **Ralph Wiggum 技术**（Geoffrey Huntley, 2025）："Ralph is a Bash loop" —— `while :; do cat PROMPT.md | claude ; done`。已产品化为 Claude Code **官方插件 `ralph-loop`**：Stop hook 拦截退出 + 原样重发提示词，`--completion-promise` + `--max-iterations` 双终止条件。案例：3 个月自主循环产出可编译语言 Cursed（LLVM 后端）。
  - https://awesomeclaude.ai/ralph-wiggum
  - https://ai-checker.webcoda.com.au/articles/ralph-wiggum-technique-claude-code-autonomous-loops-2026
  - https://blog.sivaramp.com/blog/claude-code-the-ralph-wiggum-approach/
- **Claude Code 内置**（v2.1+）：`/goal`（v2.1.139+，独立小模型 Haiku 每轮读 transcript 判定条件，**默认无轮数上限**）、`/loop`（固定间隔/自节奏重发 prompt）、`/batch`（并行 worktree）；2.1.234+ 用量限额重置后**默认自动续跑**（`autoContinueAtUsageLimit`）。
  - https://vibeready.sh/blog/loop-engineering-claude-code/
  - https://ranjankumar.in/ralph-loop-claude-code-goal-autonomous-coding
  - https://aicatchup.com/news/claude-code-desktop-auto-continue
- **Stop hook 原语**：打印 `{"decision":"block","reason":"..."}` 阻止收尾并重注入指令；`stop_hook_active` 防递归；默认 block cap = 8（`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` 可调）。
  - https://dev.to/maddy30445r/claude-code-stop-hooks-making-the-agent-finish-its-homework-hmd
  - https://www.agentic-patterns.com/patterns/stop-hook-auto-continue-pattern/
- **框架级原语**：AutoGen termination conditions（MaxMessageTermination / TextMentionTermination 等）；LangGraph `recursion_limit`（超限报图循环错误，社区 issue #6731）。
- **"直到极限上下文"的解法**：
  - **Letta (MemGPT)**：三层记忆（core/archival/recall）+ 自动 compaction + **heartbeat**（无需用户输入自行继续）+ sleep-time compute。https://chatforest.com/reviews/letta-memgpt-stateful-agent-framework/
  - **fresh-context + 状态落盘**（AGENTS.md 模式，"stateless but iterative"）：每轮全新上下文 + 进度写盘，解决上下文溢出。https://addyosmani.com/blog/self-improving-agents/
- **研究型 Agent**（循环内嵌于研究流程）：**GPT Researcher**（plan→search→read→reflect→**iterate**，递归树状 depth/breadth 探索，DeepResearchGym #1，https://gptr.dev/）、**Stanford STORM**（多视角提问→大纲→带引用长文）、Agent Laboratory、AI Scientist（https://blog.gatsbi.com/wordsmith/best-open-source-ai-research-agents/）。
- **失控/空转的治理**：genkitx-misc 三件套（loop 检测 = tool-call 指纹哈希、contextCompression、softFail，https://medium.com/@pavel.jbanov/stop-your-ai-agents-from-crashing-looping-and-burning-through-tokens-59caf4b3eb34）；学术：《When Agents Do Not Stop》统计了 68 个无界反馈路径缺陷，主因=反馈路径无强终止边界（https://arxiv.org/html/2607.01641v1）。
- **辅助**：claude-auto-retry（npm，限额重置后 tmux 自动发 continue，https://github.com/anthropics/claude-code/issues/35744）。

### B. 本工具自身的诞生（meta 发现）
- **self_loop 就是该课题的一个完整实现**：固定提示词（PROTOCOL.md，每轮原样执行）+ 状态机（tick.sh + state/ 三文件）+ 回合内自动迭代 + `ask_user` 跨回合心跳。"直到极限上下文"通过**回合滚动**实现：撞墙即滚入新回合，磁盘状态无损。
- 已在演示课题"量子纠错"上跑通 **2 轮全自动迭代**（含 1 处来源冲突的交叉裁决：Willow=105 qubit，arXiv:2408.13687），示例见 `self_loop/examples/quantum-error-correction-demo/`。
