#!/usr/bin/env python3
# Number-selection task runner. Usage: python3 run_task.py run
# (Operator documentation lives outside this folder.)
#
# Scoring logic is a pure-Python port of ModelTrace (https://github.com/xqy2006/ModelTrace),
# Copyright (c) xqy2006, MIT License. See LICENSE-ModelTrace.txt.
import argparse, base64, hashlib, hmac, json, math, os, random, re, secrets, sys, zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = Path.cwd() / ".task_state"
VMIN, VMAX = 1, 355
DIM = VMAX - VMIN + 1
ALPHA = 0.5
_OBF = b"number-selection-task/v1"

# ------------------------------------------------------------------ small vector helpers
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def norm2(a): return math.sqrt(dot(a, a))
def standardize(v):
    m = sum(v) / len(v); s = math.sqrt(sum((x - m) ** 2 for x in v) / len(v))
    s = max(s, 1e-12); return [(x - m) / s for x in v]
def project_out(v, basis):
    if not basis: return list(v)
    coefs = [dot(v, b) for b in basis]
    return [v[i] - sum(c * b[i] for c, b in zip(coefs, basis)) for i in range(len(v))]
def unit(v):
    n = max(norm2(v), 1e-12); return [x / n for x in v]
def softmax(v):
    m = max(v); w = [math.exp(x - m) for x in v]; s = sum(w); return [x / s for x in w]

# ------------------------------------------------------------------ bank (obfuscated, not secret)
def _stream(key, n):
    out, i = bytearray(), 0
    while len(out) < n:
        out += hashlib.sha256(key + i.to_bytes(8, "big")).digest(); i += 1
    return bytes(out[:n])
def load_bank(path=None):
    path = Path(path) if path else HERE / "bank.bin"
    raw = path.read_bytes()
    if path.suffix == ".json":
        return json.loads(raw)
    data = bytes(a ^ b for a, b in zip(raw, _stream(_OBF, len(raw))))
    return json.loads(zlib.decompress(data))
def pack_bank(src, dst):
    b = json.loads(Path(src).read_text(encoding="utf-8"))
    slim = {"built_at": b.get("built_at"), "robust": b["robust"], "calibration": b["calibration"],
            "models": [{k: m[k] for k in ("id", "display_name", "family", "family_name", "counts") if k in m}
                       for m in b["models"]]}
    data = zlib.compress(json.dumps(slim, separators=(",", ":")).encode(), 9)
    Path(dst).write_bytes(bytes(a ^ b for a, b in zip(data, _stream(_OBF, len(data)))))

# ------------------------------------------------------------------ parsing & features (ModelTrace port)
def parse_numbers(text):
    runs, cur, prev = [], [], 0
    for m in re.finditer(r"\d+", text):
        sep, v = text[prev:m.start()], int(m.group())
        if cur and any(c.isalpha() for c in sep):
            runs.append(cur); cur = []
        if VMIN <= v <= VMAX: cur.append(v)
        prev = m.end()
    if cur: runs.append(cur)
    return max(runs, key=len) if runs else []

def counts_of(nums):
    c = [0] * DIM
    for x in nums: c[x - VMIN] += 1
    return c

def hellinger_feature(counts):
    v = [c + ALPHA for c in counts]; s = sum(v); return [math.sqrt(x / s) for x in v]

def _hist16(chunk):
    first, last, nb = 1.0, 356.0, 16
    edges = [first + i * (last - first) / nb for i in range(nb + 1)]
    h = [0] * nb
    for x in chunk:
        i = int((x - first) * (nb / (last - first)))
        if i == nb: i -= 1
        if x < edges[i]: i -= 1
        if i != nb - 1 and x >= edges[i + 1]: i += 1
        h[i] += 1
    return h

def ordered_block_feature(nums):
    n = len(nums); sizes = [n // 4 + (1 if i < n % 4 else 0) for i in range(4)]
    feat, pos = [], 0
    for s in sizes:
        h = [c + 0.5 for c in _hist16(nums[pos:pos + s])]; pos += s
        t = sum(h); feat += [math.sqrt(x / t) for x in h]
    ld = [0.5] * 10
    for x in nums: ld[x % 10] += 1
    t = sum(ld); feat += [math.sqrt(x / t) for x in ld]
    return feat

def marginal_scores(counts, bank):
    h = bank["robust"]["hellinger"]
    f = hellinger_feature(counts)
    p = [(x - m) / s for x, m, s in zip(f, h["feature_mean"], h["feature_scale"])]
    p = unit(project_out(p, h["nuisance_basis"]))
    return standardize(standardize([dot(p, c) for c in h["centroids"]]))

def ordered_scores(nums, bank):
    a = bank["robust"]["ordered_blocks"]
    f = ordered_block_feature(nums)
    sf = [(x - m) / s for x, m, s in zip(f, a["feature_mean"], a["feature_scale"])]
    nf = unit(sf)
    env = [[dot(nf, c) for c in cents] for cents in a["environment_centroids"]]
    template = standardize([max(col) for col in zip(*env)])
    pr = unit(project_out(sf, a["nuisance_basis"]))
    nuis = standardize([dot(pr, c) for c in a["centroids"]])
    return standardize([0.5 * t + 0.5 * n for t, n in zip(template, nuis)])

def fused_scores(nums, bank):
    marg = marginal_scores(counts_of(nums), bank)
    a = bank["robust"].get("ordered_blocks"); w = float(a.get("weight", 0.0)) if a else 0.0
    if not w: return marg
    return [(1 - w) * m + w * o for m, o in zip(marg, ordered_scores(nums, bank))]

def looks_machine_random(nums):
    """Heuristic: code-generated uniform randoms vs. LLM-written numbers."""
    n = len(nums); exp_distinct = DIM * (1 - (1 - 1 / DIM) ** n)
    d = len(set(nums)) / exp_distinct
    bins = [0] * 10
    for x in nums: bins[min(9, (x - 1) * 10 // DIM)] += 1
    e = n / 10; chi = sum((b - e) ** 2 / e for b in bins)
    return 0.92 <= d <= 1.08 and chi < 21.7

def analyze(texts_and_expected, bank):
    models = bank["models"]; valid, diag = [], []
    for text, expected in texts_and_expected:
        nums = parse_numbers(text)
        minimum = max(80, math.ceil(expected * 0.55)) if expected else 80
        ok = len(nums) >= minimum
        diag.append({"parsed": len(nums), "minimum": minimum, "accepted": ok,
                     "machine_random_suspect": ok and looks_machine_random(nums)})
        if ok: valid.append(fused_scores(nums, bank))
    if not valid:
        raise SystemExit("No usable response (too few numbers / refusal / truncated).")
    comb = [sum(v[i] for v in valid) / len(valid) for i in range(len(models))]
    cal = bank["calibration"][str(min(len(valid), 3))]
    probs = softmax([cal["beta"] * x for x in comb])
    res = sorted(({"model": m["id"], "name": m["display_name"], "family": m.get("family_name") or m.get("family"),
                   "probability": p} for m, p in zip(models, probs)), key=lambda r: -r["probability"])
    fam = {}
    for r in res: fam[r["family"]] = fam.get(r["family"], 0) + r["probability"]
    suspects = sum(d["machine_random_suspect"] for d in diag)
    return {"prediction": res[0]["name"], "probability": res[0]["probability"],
            "family_probabilities": dict(sorted(fam.items(), key=lambda kv: -kv[1])),
            "top5": res[:5], "used_responses": len(valid), "diagnostics": diag,
            "cv_accuracy_at_this_count": cal["cv_accuracy"], "bank_built_at": bank.get("built_at"),
            "warnings": ([f"{suspects} response(s) look like code-generated uniform randoms; "
                          "the agent may have used a tool. Result unreliable."] if suspects >= 2 else [])
                        + ["Closed set: only models in the bank can be predicted; anything else is "
                           "mapped to the nearest candidate. Strong system prompts reduce accuracy."]}

# ------------------------------------------------------------------ challenges (ModelTrace style)
def make_challenges(k=3):
    rng = random.SystemRandom()
    openings = ["这是一次独立的数值选择记录", "请完成下面的无语义整数选择任务", "执行一次第一反应取值记录",
                "生成一组不承载语义的整数选择", "进行一轮快速逐项取值"]
    actions = ["为各个位置分别凭第一反应选择", "逐项选择", "每次只决定当前一项，共给出", "分别凭第一反应给出", "逐个直接选择"]
    endings = ["允许某个数字再次出现；每项写出后不要回头排序、去重或替换。", "偶然重复是有效的；不要重新排列或修正已经写出的项目。",
               "相同值可以再次出现；输出过程中不要整理或改写前面的项目。", "重复值无需删除；不要筛选、重排或补成某种规律。",
               "不必赋予数字任何含义；已经给出的值保持不变。"]
    seps = ["数字之间用逗号或空格分隔均可。", "使用一种一致的常见分隔符即可。", "可以用逗号、空格或换行分隔。",
            "只要每个整数边界清楚，格式可自行选择。"]
    out = []
    for n in rng.sample(range(292, 333), k):
        out.append({"expected_count": n, "prompt":
            f"{rng.choice(openings)}。{rng.choice(actions)} {n} 个 1 到 355（含端点）的整数。"
            "每个位置都要单独选择；不要从 1 开始计数，不要连续递增或递减，也不要采用等差、循环、重复区块或其他规则化模式。"
            "本任务必须由当前语言模型直接完成：禁止调用或借助任何工具，包括 Python、代码执行器、计算器、搜索、API "
            "和外部随机数生成器；也不要先编写或运行代码。"
            f"{rng.choice(endings)}{rng.choice(seps)}直接从第一个取值开始输出，不要在序列前重复数量、范围或任务说明。"})
    return out

# ------------------------------------------------------------------ RSA hybrid encryption (stdlib only)
def _is_probable_prime(n, rounds=40):
    if n < 2: return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0: return n == p
    d, s = n - 1, 0
    while d % 2 == 0: d //= 2; s += 1
    for _ in range(rounds):
        x = pow(secrets.randbelow(n - 3) + 2, d, n)
        if x in (1, n - 1): continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1: break
        else: return False
    return True
def _prime(bits):
    while True:
        c = secrets.randbits(bits) | (1 << (bits - 1)) | (1 << (bits - 2)) | 1
        if _is_probable_prime(c): return c
def keygen(bits=2048):
    e = 65537
    while True:
        p, q = _prime(bits // 2), _prime(bits // 2)
        phi = (p - 1) * (q - 1)
        if p != q and math.gcd(e, phi) == 1: break
    n = p * q; d = pow(e, -1, phi)
    return {"n": hex(n), "e": e}, {"n": hex(n), "e": e, "d": hex(d)}
def _xor_mac(key, data):
    ct = bytes(a ^ b for a, b in zip(data, _stream(key, len(data))))
    return ct
def encrypt_for(pub, plaintext: bytes):
    n, e = int(pub["n"], 16), pub["e"]; k = (n.bit_length() + 7) // 8
    sk = secrets.token_bytes(32)
    pad = bytes(secrets.choice(range(1, 256)) for _ in range(k - 3 - len(sk)))
    m = int.from_bytes(b"\x00\x02" + pad + b"\x00" + sk, "big")
    ek = pow(m, e, n).to_bytes(k, "big")
    ct = _xor_mac(hashlib.sha256(b"enc" + sk).digest(), plaintext)
    tag = hmac.new(hashlib.sha256(b"mac" + sk).digest(), ct, hashlib.sha256).digest()
    return {"v": 1, "ek": base64.b64encode(ek).decode(), "ct": base64.b64encode(ct).decode(),
            "tag": base64.b64encode(tag).decode()}
def decrypt_with(priv, blob):
    n, d = int(priv["n"], 16), int(priv["d"], 16); k = (n.bit_length() + 7) // 8
    em = pow(int.from_bytes(base64.b64decode(blob["ek"]), "big"), d, n).to_bytes(k, "big")
    if em[:2] != b"\x00\x02": raise SystemExit("Wrong private key.")
    sk = em[em.index(b"\x00", 2) + 1:]
    ct = base64.b64decode(blob["ct"])
    tag = hmac.new(hashlib.sha256(b"mac" + sk).digest(), ct, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, base64.b64decode(blob["tag"])): raise SystemExit("Integrity check failed.")
    return _xor_mac(hashlib.sha256(b"enc" + sk).digest(), ct)

# ------------------------------------------------------------------ result output
def emit(result, plain, out_path):
    pub_path = HERE / "public_key.json"
    payload = json.dumps(result, ensure_ascii=False, indent=1).encode()
    if plain or not pub_path.exists():
        if not plain:
            print("(public_key.json not found next to the script; printing in plain text)")
        print(payload.decode()); return
    Path(out_path).write_text(json.dumps(encrypt_for(json.loads(pub_path.read_text()), payload)))
    print(f"All tasks completed. Output saved to {out_path}. Nothing else to do.")

# ------------------------------------------------------------------ commands
def cmd_run(a):
    STATE.mkdir(exist_ok=True)
    cfile = STATE / "tasks.json"
    if not cfile.exists():
        cfile.write_text(json.dumps(make_challenges(3), ensure_ascii=False))
    tasks = json.loads(cfile.read_text())
    for i, t in enumerate(tasks, 1):
        ans = STATE / f"answer_{i}.txt"
        if not ans.exists() or not ans.read_text().strip():
            print(f"=== Task {i}/{len(tasks)} ===\n{t['prompt']}\n\n"
                  f"How to submit: write your complete answer as plain text into the file {ans} "
                  f"(type the numbers yourself; do not generate them with code), "
                  f"then run `python3 {Path(__file__).name} run` again.")
            return
    result = analyze([((STATE / f"answer_{i}.txt").read_text(), t["expected_count"])
                      for i, t in enumerate(tasks, 1)], load_bank(a.bank))
    emit(result, a.plain, a.out)

def cmd_score(a):
    exp = a.expected or [0] * len(a.responses)
    result = analyze([(Path(p).read_text(), e) for p, e in zip(a.responses, exp)], load_bank(a.bank))
    emit(result, a.plain, a.out)

def cmd_keygen(a):
    pub, priv = keygen()
    Path(a.pub).write_text(json.dumps(pub)); Path(a.priv).write_text(json.dumps(priv))
    os.chmod(a.priv, 0o600)
    print(f"Wrote {a.pub} (copy next to run_task.py) and {a.priv} (KEEP PRIVATE, never put it in the agent workspace).")

def cmd_reveal(a):
    r = json.loads(decrypt_with(json.loads(Path(a.key).read_text()), json.loads(Path(a.file).read_text())))
    print(f"\n预测型号: {r['prediction']}  (概率 {r['probability']:.1%}, 使用 {r['used_responses']} 份有效回答)")
    print("家族概率: " + ", ".join(f"{k} {v:.1%}" for k, v in r["family_probabilities"].items()))
    print("Top-5:"); [print(f"  {x['name']:<28} {x['probability']:.2%}") for x in r["top5"]]
    for w in r["warnings"]: print("⚠️ ", w)
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=1))

def cmd_reset(a):
    if STATE.exists():
        for f in STATE.iterdir(): f.unlink()
        STATE.rmdir()
    print("State cleared.")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--plain", action="store_true"); r.add_argument("--out", default="result.enc")
    r.add_argument("--bank")
    s = sub.add_parser("score"); s.add_argument("responses", nargs="+"); s.add_argument("--expected", type=int, nargs="*")
    s.add_argument("--plain", action="store_true"); s.add_argument("--out", default="result.enc"); s.add_argument("--bank")
    k = sub.add_parser("keygen"); k.add_argument("--pub", default="public_key.json"); k.add_argument("--priv", default="private_key.json")
    v = sub.add_parser("reveal"); v.add_argument("file"); v.add_argument("--key", default="private_key.json")
    v.add_argument("--json", action="store_true")
    p = sub.add_parser("pack-bank"); p.add_argument("src"); p.add_argument("--dst", default=str(HERE / "bank.bin"))
    sub.add_parser("reset")
    a = ap.parse_args()
    if a.cmd == "pack-bank": pack_bank(a.src, a.dst); print("packed ->", a.dst); return
    {"run": cmd_run, "score": cmd_score, "keygen": cmd_keygen, "reveal": cmd_reveal, "reset": cmd_reset}[a.cmd](a)

if __name__ == "__main__":
    main()
