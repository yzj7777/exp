# 需求翻译官

一个面向产品功能需求澄清的交互式 Agent 原型。用户用自然语言描述想法，原型按识别到的场景调整访谈顺序和提问措辞，对笼统回答进行一次针对性追问，并生成带有待确认事项的需求草稿。

## 目录结构

```text
.
├── index.html                # 根路径跳转到项目展示页
├── README.md                 # 项目入口、运行和测试说明
├── web/                      # 展示页与可交互 Demo
│   ├── showcase.html         # 交互式项目介绍页（主展示入口）
│   ├── index.html            # 需求访谈 Demo
│   ├── agent-core.js         # 本地规则驱动访谈逻辑
│   ├── app.js                # Demo 页面交互与需求文档生成
│   └── *.css / showcase.js   # 页面样式与展示交互
├── docs/
│   ├── TODO.md               # 完整任务与完成状态
│   ├── PROJECT.md            # 项目、技术方案与评测设计
│   ├── SUBMISSION.md         # 比赛创意提交材料工作稿
│   ├── 比赛要求逐项核查.md   # 赛事要求对照和内部预审
│   ├── examples/             # 真实原始想法整理出的需求草稿
│   ├── evaluation/
│   │   ├── cases/            # 完整端到端 Agent 角色模拟案例
│   │   └── 评测方案与初步结果.md
│   ├── reference/            # 用户提供的赛事模板 PDF 参考
│   └── competition-submission-check.md
├── tests/                    # 规则引擎测试与评测样例
├── scripts/                  # PPT 生成脚本与依赖清单
└── deliverables/             # 比赛项目 PPT 成品
```

## 本地运行

无需安装依赖：

```bash
python3 -m http.server 4173 --bind 0.0.0.0
```

打开 `http://localhost:4173/` 或 `http://localhost:4173/web/showcase.html` 进入交互式项目介绍页；`http://localhost:4173/web/index.html` 直接进入访谈 Demo。

## 测试

```bash
node tests/agent-core.test.js
node tests/evaluate-agent.js
```

## 比赛 PPT

成品位于 `deliverables/需求翻译官-比赛项目介绍.pptx`，按 `docs/reference/` 中参赛者提供的模板 PDF 结构重建；生成脚本与版式说明见 `scripts/build_presentation.py`、`docs/PPT制作说明.md`。PDF 附录页以图像保留，第 2–4 页为原生可编辑内容。

## 当前实现边界

当前为纯前端、规则驱动原型，`web/agent-core.js` 使用关键词和规则进行场景分类、问题排序、有限追问和补充归类。用户可以跳过问题（标为待确认）、修改已录入画像字段；导出草稿会记录信息来源与待确认状态。尚未接入大语言模型、openJiuwen / WorkSwarm、后端或持久化服务，不具备开放式语义推理或复杂冲突检测能力。访谈仅保留在当前页面会话，刷新后清空。规则匹配可能不准确，生成草稿需由用户复核。比赛材料应如实说明实际能力；提交格式请以官方赛事页面及平台要求为准。
