# 大模型「型号识别 / 量化检测 / 掺水降智」检测工具调研

> 调研日期：2026-10-16。Star 数和最后推送日期来自当天的 GitHub API。
> 说明：这个领域变化很快，不少工具的作者本身就在经营中转站或聚合平台，下文中「⚠️利益相关」标出的就是这种情况。

---

## 0. 先说结论

| 想弄清楚的问题 | 首选工具 | 原理 | 可信度 |
|---|---|---|---|
| **这到底是哪个模型/哪个版本？** | ModelTrace、meow-llm-detector、hlwy-ai-checker、lm-detector | 让模型生成「随机数/短答案」，比较输出的统计分布（指纹） | 区分不同模型家族和版本：**较强** |
| **中转站有没有掉包、注入提示词、虚报 token、阉割功能？** | Veridrop、api-relay-audit、claude-detector（anthropic.mom）、RelayScope、relaycheck | 协议字段、SSE 事件、thinking 签名、usage 对账、隐藏 prompt 探测 | 抓「假货」和「协议造假」：**较强** |
| **是否量化（FP8/INT4…）？** | Model Equality Testing（MMD）、attest（logprob JSD）、Kimi Vendor Verifier、Artificial Analysis Endpoint Accuracy Index；本地模型用 llama.cpp KLD | 与参考部署对比输出分布或 logprobs、跑基准看精度保留率 | 黑盒条件下**偏弱**；有 logprobs 或自建参考时才可靠 |
| **官方本身有没有悄悄降智（长期漂移）？** | Marginlab Claude Code Tracker、AIStupidLevel、isitnerfed.org；自测用 lm-evaluation-harness / Inspect / OpenBench | 固定题库定期重复跑，配合统计显著性检验 | 能看到**趋势**，单次测试噪声很大 |

**核心难点**：学术研究（Cai et al., 2025, UC Berkeley）指出，只看文本输出的方法（文本分类器、问模型「你是谁」、MMD、跑基准）**很难识别量化替换**，也会被「随机部分掉包」和「识别出检测题后放行真模型」绕过。logprobs 对比最灵敏，但很多 API 不提供 logprobs，还会受推理非确定性干扰。
→ 所以要**把多种方法组合起来、多个时段反复测**，并且尽量拿**官方直连**作为对照基准。

---

## 1. 型号/版本识别（LLM 指纹）

| 工具 | Star | 说明 |
|---|---|---|
| **[xqy2006/ModelTrace](https://github.com/xqy2006/ModelTrace)** | ~1.7k | 发 3 条「长整数随机生成」挑战，用 Hellinger 距离和有序块特征比对统一指纹库，给出模型家族和**具体版本**的概率（如区分 Opus 4.6 与 5.0）。用 SVD 投影抵消 system prompt 的影响。可本地运行，也有 GitHub Pages 手动版（直接在 ChatGPT/Claude 网页里粘贴挑战题）。附带 Codex 插件 *ModelTrace Guard*，可在任务过程中持续监测。在 Claude Code 这类系统提示很强的环境里准确率会下降。 |
| **[Ikaleio/lm-detector](https://github.com/Ikaleio/lm-detector)** | ~360 | 把 ModelTrace 做成产品：Web 和 Bun CLI 共用算法与正式数据库，补上了排序器、验证器和校准。 |
| **[chen-006/meow-llm-detector](https://github.com/chen-006/meow-llm-detector)** | ~1.5k | 用一组短问题的回答分布做指纹比对，提供 32/64/128 次几个档位（GPT 新基准推荐 128 次）；有 Windows 便携包和[在线版](https://meowllm.top/)。会自动更新维护者提供的基准，适合中转站用户日常自测。 |
| **[hanlinwenyuan/hlwy-ai-checker](https://github.com/hanlinwenyuan/hlwy-ai-checker)** | ~760 | 基于概率分布的「AI 鉴别器」：用官方 Plus/Pro 账号或高价渠道建基准，再与待测渠道比对**一致性**，每题重复 50–500 次做统计。成本很低（百次测试约 0.1 元）。社区提供共享基准（LINUX DO）。为应对中转站屏蔽固定检测提示词，在提示词里加入了随机字符。 |
| **[ToseaAI/llm-fingerprint-detector](https://github.com/ToseaAI/llm-fingerprint-detector)** | 36 | 论文《One Token Is Enough》(arXiv:2607.10252) 的 TS 实现，零依赖库 + CLI。用 100–400 次单 token 回答的分布算 JS 散度，可以先 `fingerprint` 官方端点，再 `verify` 待测端点；退出码适合放进 CI。有[浏览器在线版](https://tosea.ai/free-tools/llm-api-fingerprint-checker)（Key 不出浏览器）。作者明确提醒：**两边的 system prompt 必须一致**，否则差异会和换了一个模型一样大。 |
| **[pasquini-dario/LLMmap](https://github.com/pasquini-dario/LLMmap)** | ~480 | USENIX Security 2025 论文，主动探针 + 开放集分类器，用约 8 次交互识别 LLM 版本，学术上的代表作。 |
| [litemars/LLM-Fingerprinter](https://github.com/litemars/LLM-Fingerprinter) | 21 | 多层行为探针 + 集成分类，输出家族/版本/unknown。 |
| **[unclecode/modelprint](https://github.com/unclecode/modelprint)** | 130 | 「看管道而不看人格」：用 tokenizer 计数（各家 tokenizer 不同）、模板开销、错误码格式、finish_reason 词表、响应头、上下文上限二分、**logprob 几何（可提示量化或替换过的权重）**等基础设施探针。纯浏览器，[modelprint.ai](https://modelprint.ai)。 |
| [kiyoakii/is-gpt-nerfed](https://github.com/kiyoakii/is-gpt-nerfed) | ~250 | Codex 专用的「缩水检测器」（macOS）：读取 Codex 日志，发现静默换模型、降低推理档、换成隐藏内部模型、缩小上下文；定期 fork 会话做 ModelTrace 随机数指纹。 |
| [wangchao0708/TraceOne](https://github.com/wangchao0708/TraceOne) | 11 | Codex 模型溯源，一次提问识别 5 款模型的行为指纹。 |

**注意**：指纹库是**闭集**，库里没有的模型也会被归到「最像」的候选。指纹一致说明行为相同，**不等于**能证明供应商在主观上作假（也可能是上游路由变化或服务降级）。

---

## 2. 中转站「掺水 / 掉包 / 注入 / 计费」综合审计

| 工具 | Star | 主要检测项 |
|---|---|---|
| **[canarybyte/veridrop](https://github.com/canarybyte/veridrop)**（[veridrop.app](https://veridrop.app)） | ~640 | 拿官方基线做**字段级、协议级、加密级**比对：真伪、能力是否被剥离（PDF/Tool Use/Thinking/长上下文）、usage 合规、思维签名验证；有中转站红黑榜，可自托管，AGPL。 |
| **[toby-bridges/api-relay-audit](https://github.com/toby-bridges/api-relay-audit)** | ~880 | 本地 13 步审计，单文件 `audit.py` 零依赖：用差值法测 token 注入（实际 input_tokens − 预期）、隐藏 prompt 提取、身份替换、越狱、上下文截断二分、**工具调用改写（包名被换成 typosquat）**、错误泄漏、SSE 流完整性、延迟方差。⚠️作者在社交媒体上推荐过特定中转站。 |
| **[7836246/claude-detector](https://github.com/7836246/claude-detector)**（test.anthropic.mom） | 56 | Claude 专用，19 个黑盒探针：model 回显、msg_ ID 格式、count_tokens 独立重算对账、stop_sequences/max_tokens 行为、toolu_ ID、SSE 事件顺序、Anthropic 响应头、多模态/PDF、缓存等；输出 6 级真伪判定和 5 种来源渠道（官方/订阅/云平台/中转/逆向）。 |
| [Lecheeel/RelayScope](https://github.com/Lecheeel/RelayScope) | 1 | 假模型、降质、**缓存倍率被暗改**、usage 异常；可模拟 Codex / Claude Code 客户端配置。 |
| [jayson-yxj/relaycheck](https://github.com/jayson-yxj/relaycheck) | 1 | 掉包、虚报计费（隐藏思维链计费）、tokenizer 指纹、参数透传、文首/文末双标记测上下文截断；只读，结果可复现。 |
| [som1ng/API-QuickCheck](https://github.com/som1ng/API-QuickCheck) | 6 | 24 项探针，其中 **thinking 签名回传验签**是少数能给出加密级结论的检查；也支持批量测 Key。 |
| [mintesnot-teshome/llm-verify](https://github.com/mintesnot-teshome/llm-verify) | 41 | 32 个取证提示词；支持「有官方 Key 的对照比较」和「只测可疑端点」两种模式；会交叉比较多个模型名背后是否其实是同一个模型。 |
| [ahmedakaev/attest](https://github.com/ahmedakaev/attest) | 2 | 分级检测：system_fingerprint、seed 确定性 → logprob JSD（**用于量化检测**）→ 语义相似度 → MMD 置换检验；另有计费核对和「部分路由」下界估计。 |
| [dufeisolo/model-check-core](https://github.com/dufeisolo/model-check-core)（[model-check.org](https://model-check.org)） | 4 | 13 项：协议识别、回显、指纹、流式、输出控制、system 指令、工具、多模态、推理参数、usage、缓存。 |
| [october-coder/api-check](https://github.com/october-coder/api-check) | ~930 | 纯前端 API 测试工具（可用性、模型列表、延迟），偏向「能不能用」，不做深度鉴真。 |
| [cocodot2026/cocodot-llmprobe](https://github.com/cocodot2026/cocodot-llmprobe) | 2 | 多平台一键横评，可选用强模型当裁判打分。⚠️作者经营中转站。 |
| [bi-boo/claude-model-fingerprint](https://github.com/bi-boo/claude-model-fingerprint) | 79 | Claude Code Skill，让模型「自省」判断是否为真 Claude、是否有多层封装。可作参考，但自述类证据较弱。 |
| 在线站：[hvoy.ai](https://hvoy.ai)、iffs.cn、[apitest.bashige.com](https://github.com/bashigestudio/apitest) | — | 输入 URL + Key 即可检测。hvoy 会模拟 Claude Code 端口；bashige 10 维评分。⚠️部分站点带有中转站推荐或导流。 |

---

## 3. 量化程度检测（最难的部分）

### 3.1 黑盒 API（只能拿到输出）

- **Model Equality Testing**（Gao, Liang, Guestrin, ICLR 2025）· [i-gao/model-equality-testing](https://github.com/i-gao/model-equality-testing)
  用 Hamming 核的 MMD 双样本检验对比 API 与参考权重的输出分布，每个提示平均约 10 个样本就能有中位数 77.4% 的检出功效，可以检测量化、水印和微调。实测 31 个 Llama 端点中有 11 个与 Meta 原版权重的分布不一致。还附带 100 万条补全的数据集。**需要能在本地跑参考权重（开源模型）。**
- **Rank-Based Uniformity Test**（arXiv:2506.06975）：对 4bit 的检出明显好于 8bit（8bit 很难检出）。
- **Cai et al. 2025《Are You Getting What You Pay For?》**（arXiv:2504.04715）：文本分类器区分全精度和量化版的准确率约 50%（等于瞎猜），「你是谁」提问完全无效；**logprob 是最强的信号**，但受 API 是否开放和推理非确定性限制；作者最终主张用 TEE 硬件证明。
- **工具里的实现**：attest（logprob JSD 等级）、modelprint（logprob 几何 δ）。前提是端点返回 `logprobs`。

### 3.2 开源模型的供应商（Kimi、DeepSeek、GLM、Qwen、gpt-oss…）

- **[MoonshotAI/K2-Vendor-Verifier](https://github.com/MoonshotAI/K2-Vendor-Verifier)**（~590★）/ **[Kimi-Vendor-Verifier](https://github.com/MoonshotAI/Kimi-Vendor-Verifier)**（~180★）：官方出品，用同一批工具调用提示比较各供应商。K2VV 发现同一款 K2 最好的节点 token 完全正确率 99.3%，最差只有约 64%。KVV 扩展到 OCRBench、MMMU Pro、AIME2025、工具调用、参数生效检查，专门抓过度量化或配置错误。
- **Artificial Analysis Endpoint Accuracy Index**：自托管参考部署，把各供应商端点的得分表示为参考的百分比（BFCL 工具调用、HLE、长上下文三项），附 95% 置信区间；同时要求供应商如实申报量化精度。
- **OpenRouter Exacto / Auto Exacto**：基于真实流量的工具调用遥测加基准选择供应商。OpenRouter 的数据显示**单靠量化对工具调用质量没有可测影响，主要问题出在 tool-call parser**，这一点和社区的直觉不同。
- **Epoch AI《Why benchmarking is hard》**：GPQA-Diamond 上，「选哪家供应商」是影响分数最大的变量。
- **[groq/openbench](https://github.com/groq/openbench)**（~820★）：与供应商无关的开源评测基础设施（OpenRouter Exacto 的基准底座）。

### 3.3 本地 / 白盒（能拿到权重）

- **llama.cpp `perplexity --kl-divergence`**：先用 FP16 生成 logits 基准，再测量化模型的 Mean KLD、Δp 分位数、Same top-p 比例。这是衡量量化损失的标准做法。
- **[PrimeIntellect-ai/toploc](https://github.com/PrimeIntellect-ai/toploc)**：可验证推理，对隐藏层 top-k 做局部敏感哈希，能检出模型、提示词、**精度**被改动（论文实验中 100% 检出）；但需要供应商配合输出证明，而且检测不到投机解码（speculative decoding）。

---

## 4. 长期「降智」监控（官方是否悄悄削弱）

- **Marginlab Claude Code Tracker**（marginlab.ai/trackers/claude-code）：每天用 Claude Code CLI 跑 SWE-Bench-Pro 子集，按伯努利模型计算 95% CI，分日/周/月阈值判定是否显著退化。
- **AIStupidLevel**（[aistupidlevel.info](https://aistupidlevel.info)，MIT 开源）：24 小时监测 20 多个模型，每题跑 5 次取中位数，用 CUSUM / Page-Hinkley 做变点检测，另有上下文腐化（Context Rot）基准。
- **isitnerfed.org**：众包投票加性能曲线。
- **自建**：[EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness)（14k★）、[UK AISI Inspect](https://github.com/UKGovernmentBEIS/inspect_ai)（3k★）、OpenBench，用固定题库加统计检验。
- 不依赖工具的土办法：「鹈鹕骑自行车 SVG」这类固定难题做主观对比（如 gpttesticu、chatgpt-jiangzhi-test），成本低但很主观。

---

## 5. 实操建议

1. **先建基准**：用官方直连（或你信任的渠道）对同一模型跑 ModelTrace / hlwy / meow / Tosea 等，生成参考指纹。
2. **三层组合测试**：
   - 协议和计费层：Veridrop 或 api-relay-audit 或 claude-detector，抓注入、伪造字段、token 虚报、能力阉割。
   - 身份层：用指纹工具判断家族和版本。
   - 能力层：跑几道你自己的、**不公开**的难题（公开检测题可能被识别后放行真模型），必要时用 lm-eval 或 Inspect 做统计检验。
3. **分多个时段重复测**：有些平台只在高峰期降级，或者只把一部分请求路由到便宜模型（随机部分掉包会显著削弱单次检测的效果）。
4. **system prompt 要一致**：注入的系统提示本身就会让指纹产生和换模型一样大的偏移。这本身也是一种异常信号。
5. **量化问题优先看 logprobs**：端点支持 logprobs 时，用 attest 或 modelprint 做分布对比；开源模型就自己部署参考做 MMD，或直接看 KVV / Artificial Analysis 的供应商榜。
6. **安全**：一律用**临时 Key**，测完删除；在线检测站会让 Key 经过对方服务器，优先选本地运行或纯浏览器的工具（Tosea、modelprint、ModelTrace Pages 版）。
7. **理解结论的边界**：所有黑盒检测都只是**证据，不是证明**。「不符」可能是掉包，也可能是上游路由、参数（温度）或客户端限制（例如有些 Claude Max 分组只允许 Claude Code 客户端调用）造成的。

---

## 参考论文

- Gao et al. *Model Equality Testing: Which Model Is This API Serving?* ICLR 2025, arXiv:2410.20247
- Cai et al. *Are You Getting What You Pay For? Auditing Model Substitution in LLM APIs*, arXiv:2504.04715
- *Auditing Black-Box LLM APIs with a Rank-Based Uniformity Test*, arXiv:2506.06975
- Pasquini et al. *LLMmap: Fingerprinting for Large Language Models*, USENIX Security 2025, arXiv:2407.15847
- Bruckner. *One Token Is Enough*, arXiv:2607.10252
- Ong et al. *TOPLOC: A Locality Sensitive Hashing Scheme for Trustless Verifiable Inference*, arXiv:2501.16007

---

## 附录：没有 API、只能在对话框里测的型号识别工具（2026-10-16 补充）

| 工具 | 使用方式 | 能识别到什么程度 | 主要限制 |
|---|---|---|---|
| [xqy2006/ModelTrace](https://github.com/xqy2006/ModelTrace) 的 GitHub Pages 手动版 / [ModelTrace-Portable](https://github.com/wssz527/ModelTrace-Portable)（单文件 HTML） | 复制 3 条挑战发给待测对话，再把完整回答粘贴回工具，归因在浏览器本地计算 | 家族加具体版本（指纹库约 17 个 GPT/Claude 型号） | 闭集：库外模型也会被归到最像的候选；有强 system prompt 的 Agent 环境里准确率下降 |
| [pasquini-dario/LLMmap](https://github.com/pasquini-dario/LLMmap)（USENIX Sec'25） | `python main_interactive.py`，按提示把约 8 个探针问题的回答粘贴进去；带预训练的开放集模型 | 家族/版本（开放集，可以输出「未知」） | 预训练库偏旧，新模型要自己用 `add_new_template.py` 扩充 |
| [locuslab/llm-idiosyncrasies](https://github.com/locuslab/llm-idiosyncrasies) | 收集一批回答，用预训练的 LLM2vec 分类器分类 | 只到厂商家族（ChatGPT/Claude/Grok/Gemini/DeepSeek 五分类，约 97%） | 分不出版本；需要 24GB 显卡；分类器训练于 2025 年初 |
| 知识截止探针：[nexync/dated_data](https://github.com/nexync/dated_data)、按月份递进提问的事件测验 | 按月份询问带日期的事件，看准确率从哪个月开始下降 | 只能估出截止月份，可以作为辅助证据缩小候选 | 不能单独定型；而且官方公布的截止日期和实际探测结果可能不一致 |
| Glitch token 探针（[GlitchMiner](https://github.com/wooozihui/GlitchMiner)、under-trained tokens 研究） | 让模型复述特定异常 token，看它是否复述失败 | 推断 tokenizer 所属家族 | 主要对旧版 tokenizer 有效（如 cl100k、Claude 2），新模型基本已修复 |

**结论**：在没有 API 的情况下，只有 ModelTrace（手动版）和 LLMmap（交互版）能做到**家族加版本**级别的识别，其余工具只能识别家族或作为辅助证据。**没有任何工具能测出参数量或量化精度。**
