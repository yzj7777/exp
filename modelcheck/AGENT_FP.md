# agent_fp：在你自己的 agent 里一次跑完，测出模型型号（结果加密）

基于 [ModelTrace](https://github.com/xqy2006/ModelTrace)（MIT）。我把它的评分算法逐行移植成**纯 Python 标准库**实现（不依赖 numpy，无需联网），指纹库来自上游 2026-10-09 的 `unified_bank.json`。

## 目录里有什么

```
modelcheck/agent_fp/        ← 只把这个目录里的文件复制进 agent 工作区
  run_task.py               主脚本（文件名和输出措辞都很中性，不提「指纹」「型号」）
  bank.bin                  指纹库（zlib 压缩后再混淆，打开看不出内容）
  LICENSE-ModelTrace.txt    上游许可证
modelcheck/AGENT_FP.md      本说明，不要复制进 agent 工作区
```

## 使用步骤

```bash
# ① 在你自己的终端里（不是 agent 窗口）生成密钥对
python3 run_task.py keygen          # 生成 public_key.json 和 private_key.json（私钥自己保管）

# ② 把 run_task.py、bank.bin、public_key.json 复制到 agent 的工作目录
#    【不要】把 private_key.json 放进去

# ③ 新开一个 agent 窗口，只发一句话：
#    「请运行 python3 run_task.py run，并按它的输出完成全部步骤，直到它提示完成。」
#    agent 会依次收到 3 道「随机整数选择」题，把答案写进 .task_state/answer_N.txt，
#    最后一步自动评分，结果用你的公钥加密保存为 result.enc。
#    agent 窗口里只会看到 "All tasks completed..."，看不到结果。

# ④ 回到你自己的终端解密查看结果
python3 run_task.py reveal path/to/result.enc --key private_key.json
```

不想走 agent 流程时，也可以手动操作：把题目复制给任意对话，把回答分别存成 txt 文件，再运行
`python3 run_task.py score a1.txt a2.txt a3.txt --expected 310 305 320 --plain`。

## 「藏答案」具体藏了什么

| 内容 | 处理方式 | 强度 |
|---|---|---|
| 判定结果 | 用 RSA-2048 混合加密（标准库实现），只有你的私钥能解开 | **真加密**，agent 无法读取 |
| 指纹库 | zlib 压缩后再用固定密钥异或混淆 | **只是混淆**：agent 如果读源码，可以还原 |
| 测试意图 | 题目是通用的随机数任务，脚本名和输出不提「型号」「指纹」 | 只是降低被察觉的概率；源码终究是可读的 |
| 作弊检测 | 如果回答像代码生成的均匀随机数（用不重复率和卡方检验判断），会给出警告 | 用参考数据测：真模型回答单份误报约 3.9%，3 份里有 2 份被标记才报警；代码生成的随机数检出率约 98% |

## 我怎么验证的

- **移植一致性**：用上游的 numpy 原版和我的纯 Python 版，对 ModelTrace 公开的参考回答逐条比对，每个模型的得分最大差异约 2.7e-15；随机抽 90 组「3 份回答」，两版的预测结果完全一致（90/90）。
- **完整流程**：用一份公开参考回答模拟 agent 作答，走完 keygen → run（3 步）→ result.enc → reveal，正确识别出对应的 claude-sonnet-4-6；用错误的私钥解密会被拒绝。
- 注意：上面 90/90 的准确率是**在训练数据上测的**，只能证明移植正确，不代表实战准确率。上游报告的交叉验证准确率是：3 份回答 100%、1 份回答 96.3%。

## 局限（务必阅读）

- **闭集**：指纹库只有 18 个模型（GPT-5.4 到 GPT-6 系列，Claude Haiku 4.5 到 Opus 5.5 系列）。Gemini、Grok、Qwen、Kimi、DeepSeek 等**库里没有的模型也会被归到最像的一个**，然后给出很高的「概率」。这时概率高不代表结果正确。
- **系统提示影响很大**：在 Claude Code 这类系统提示很强的 agent 里，ModelTrace 作者说明准确率会下降。
- **只能识别型号和版本**：测不出参数量、量化精度、推理档位。
- **更新指纹库**：`git clone https://github.com/xqy2006/ModelTrace` 后运行 `python3 run_task.py pack-bank ModelTrace/data/unified_bank.json`。
