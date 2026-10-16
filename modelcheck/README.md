# modelcheck

## 1. `blindtest.py`：能力盲测，答案用 HMAC 加密

用来检查模型有没有「降智」，**不识别型号**。

```bash
# 在你自己的电脑上生成题目（不要在被测的 agent 窗口里生成）
python3 blindtest.py gen --secret "只有你知道的口令" --hard --out questions.json

# 得到要发给被测模型的完整提示
python3 blindtest.py ask questions.json > prompt.txt

# 把模型回复的 JSON 存成 answers.txt，然后判分
python3 blindtest.py grade --secret "只有你知道的口令" questions.json answers.txt
```

- `questions.json` 里只存 `HMAC-SHA256(口令, 答案)`，**不存明文答案，也不存随机种子**。没有口令就无法反推答案，连「星期几」这种只有 7 种可能的答案也穷举不出来。
- 每次 `gen` 默认使用新的随机种子，题目不会重复，被测模型没法背题。
- `ask` 会要求模型不用工具作答，但这一点无法强制；agent 如果偷偷跑代码，算术类题目就失去了测试意义（大海捞针和应用题受影响较小）。
- 题型共 16 道：大数乘法、模幂、字母计数、星期推算、排序、字符串反转、区间素数计数、布尔求值、进制转换、多步应用题，以及长文本里的大海捞针（`--hard` 模式约 400 行）。

## 2. 测你自己的 API 端点 / 中转站的真实型号

你有 Base URL 和 Key 时，可以用公开工具的自动模式（以下命令需在你本地有外网的环境运行）：

```bash
# a) 型号指纹（家族 + 版本），用浏览器打开本地页面 http://127.0.0.1:7860/
git clone https://github.com/xqy2006/ModelTrace && cd ModelTrace
python -m pip install -r requirements.txt && python start.py

# b) 中转站审计：注入、截断、工具调用改写、计费、SSE 流
curl -fsSL https://raw.githubusercontent.com/toby-bridges/api-relay-audit/master/audit.py -o audit.py
python audit.py --key "$KEY" --url "$BASE_URL" --output report.md

# c) 与官方基准做单 token 分布比对：先对官方端点 fingerprint，再对待测端点 verify
npx llm-fingerprint-detector fingerprint --base-url https://api.openai.com/v1 --model "$MODEL" --out ref.json
npx llm-fingerprint-detector verify --base-url "$BASE_URL" --model "$MODEL" --reference ref.json
```

所有黑盒方法都只能提供证据，不能当作证明；参数量和量化精度用这些方法测不出来。
