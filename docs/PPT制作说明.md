# 《需求翻译官》比赛项目 PPT 制作说明

## 文件与来源

- 成品：`deliverables/需求翻译官-比赛项目介绍.pptx`
- 生成脚本：`scripts/build_presentation.py`
- 生成依赖：`scripts/requirements-presentation.txt`
- 模板参考：参赛者提供的 `docs/reference/openJiuwen-创意大赛提交模板-参考.pdf`

用户提供的是 7 页 PDF 参考模板，而非可直接编辑的 `.pptx` 源文件。当前 PPT **按该 PDF 的内容顺序、A4 横版比例和版式制作**：

1. 封面：沿用模板封面视觉，覆盖模板占位标题并替换项目标题；
2. 创意名称、创意描述、所属主题、应用场景；
3. 创意方案构想：方案详情、方案优势、技术依赖；
4. DEMO/示意图：按模板要求展示触发时机、用户输入输出和关键路径；
5. 模板附录：赛题方向详细参考；
6. 模板附录：评分标准；
7. 模板附录：Thank you。

**可编辑性说明：** 第 2–4 页为原生 PowerPoint 文本框和图形；第 1 页使用模板 PDF 封面图作底图并叠加项目文字；第 5–7 页为原 PDF 对应附录页的页面图像，所以这三页文字不是可单独编辑的对象。若之后取得官方可编辑 PPTX，可把前三页的内容迁移进原版并保留官方附录。

## 官方模板文件核验

此前公开搜索官方赛事列表和准确模板名称，没有找到可核验的官方 `.pptx` 下载直链。现在参赛者提供了 PDF 版模板，因此本成品改为**参考该 PDF 模板重制**；不能声称下载或编辑了原生官方 `.pptx` 文件。公开官方赛事列表：[openJiuwen 智能体创新大赛](https://competition.gitcode.com/competition)。

## 成品内容与事实边界

- 创意描述和应用场景按提交模板必填项组织；主题选“办公”。
- 第 4 页演示路径结合网页 Demo，但其中“会议协作”的对话为示意案例，不伪称真实用户访谈。
- 规则样例结果注明为人工编写的固定样例，不代表真实准确率或用户成效。
- 当前网页仍为规则驱动原型，没有接入大语言模型 API、后端服务或 WorkSwarm；PPT 对此有明确说明。
- 页面上“用户需求、目标、价值影响”等尚未验证的内容都以待确认或计划表述。

## 重新生成

在仓库根目录安装依赖后运行：

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements-presentation.txt
.venv/bin/python scripts/build_presentation.py
```
