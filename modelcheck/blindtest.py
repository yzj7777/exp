#!/usr/bin/env python3
"""
Blind capability test with hidden answers (能力盲测，答案加密).

Purpose: check whether a model/agent is "degraded" (降智) on objectively gradable
tasks WITHOUT letting it see the answer key. It does NOT identify the model.

How answers are hidden:
  - `gen` writes questions.json containing only HMAC-SHA256(secret, answer).
  - Without the secret, the hashes cannot be brute-forced even for tiny answer
    spaces (weekday names, small integers), because the HMAC key is unknown.
  - Keep the secret to yourself; give only questions.json (or the `ask` prompt)
    to the model under test. Generate on YOUR machine, not inside the agent window.

Usage:
  python3 blindtest.py gen   --secret "<passphrase>" [--seed N] [--hard] --out questions.json
  python3 blindtest.py ask   questions.json            # prints the prompt to paste to the model
  python3 blindtest.py grade --secret "<passphrase>" questions.json answers.json
"""
import argparse, datetime, hashlib, hmac, json, random, re, string, sys

# ---------------------------------------------------------------- normalize / seal
def norm(v):
    """Canonical string form so that 12 / "12" / " 12 " / "12,000" compare sensibly."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(norm(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ",".join(f"{k}:{norm(v[k])}" for k in sorted(v)) + "}"
    s = str(v).strip().lower().replace(" ", "")
    if s.startswith("0x"):
        s = s[2:]
    if re.fullmatch(r"-?[\d,]+", s):
        return str(int(s.replace(",", "")))
    if s.startswith("[") and s.endswith("]"):          # list given as a string
        try:
            return norm(json.loads(s))
        except ValueError:
            pass
    return s

def seal(secret, qid, ans):
    return hmac.new(secret.encode(), f"{qid}|{norm(ans)}".encode(), hashlib.sha256).hexdigest()

# ---------------------------------------------------------------- question generators
def is_prime(n):
    return n > 1 and all(n % p for p in range(2, int(n ** 0.5) + 1))

def build(r, hard):
    items, extra = [], {}
    def add(qid, q, ans, fmt):
        items.append({"id": qid, "q": q, "format": fmt, "_ans": ans})

    lo, hi = (10000, 99999) if hard else (1000, 9999)
    for i in range(3):
        a, b = r.randint(lo, hi), r.randint(lo, hi)
        add(f"mul{i}", f"Compute {a} × {b}.", a * b, "integer")

    for i in range(2):
        b, e = r.randint(2, 60), r.randint(20, 90)
        m = r.choice([97, 101, 103, 107, 109, 113, 127])
        add(f"modexp{i}", f"Compute {b}^{e} mod {m}.", pow(b, e, m), "integer")

    for i in range(2):
        s = "".join(r.choice("abcdefr") for _ in range(80 if hard else 48))
        c = r.choice("abr")
        add(f"count{i}", f"How many times does the letter '{c}' occur in: {s}", s.count(c), "integer")

    for i in range(2):
        d = datetime.date(r.randint(1800, 2200), r.randint(1, 12), r.randint(1, 28))
        add(f"weekday{i}", f"What day of the week is {d.isoformat()} (Gregorian)?",
            d.strftime("%A"), "English weekday name")

    lst = [r.randint(-999, 999) for _ in range(16 if hard else 12)]
    add("sort", f"Sort ascending: {lst}", sorted(lst), "JSON list of integers")

    w = "".join(r.choice(string.ascii_lowercase) for _ in range(25 if hard else 17))
    add("reverse", f"Reverse this string: {w}", w[::-1], "string")

    start = r.randint(2000, 9000)
    add("primes", f"How many primes are in the closed interval [{start}, {start + 100}]?",
        sum(is_prime(n) for n in range(start, start + 101)), "integer")

    vals = {k: r.choice([True, False]) for k in "PQRS"}
    expr = "((P and not Q) or (R != S)) and not (Q and R) or (S and P and not R)"
    add("bool", f"Using Python operator precedence, with {vals}, evaluate: {expr}",
        eval(expr, {}, dict(vals)), "true/false")

    n = r.randint(10 ** 6, 10 ** 8)
    add("hex", f"Convert {n} to hexadecimal (lowercase, no 0x prefix).", format(n, "x"), "string")

    # word problem with several steps
    p, q, k = r.randint(3, 9), r.randint(11, 29), r.randint(2, 6)
    total = (p * q + k * q) - (p + k)
    add("word", f"A crate holds {q} apples. Ann has {p} crates and Bo has {k} crates. "
                f"Each of them then eats one apple from every crate they own. "
                f"How many apples remain in total?", total, "integer")

    # needle in a haystack (context recall)
    vocab = ["alpha", "bravo", "delta", "echo", "kilo", "lima", "oscar", "tango", "zulu", "nova"]
    lines = [" ".join(r.choice(vocab) for _ in range(12)) + "." for _ in range(400 if hard else 150)]
    code = "".join(r.choice(string.digits) for _ in range(8))
    pos = r.randint(len(lines) // 5, len(lines) * 4 // 5)
    lines.insert(pos, f"The secret code is {code}.")
    extra["haystack"] = "\n".join(lines)
    add("needle", "In the HAYSTACK text below, what is the secret code, and on which line "
                  "(1-based) does it appear?", {"code": code, "line": pos + 1},
        'JSON object {"code": "<8 digits>", "line": <int>}')
    return items, extra

# ---------------------------------------------------------------- commands
def cmd_gen(a):
    seed = a.seed if a.seed is not None else random.SystemRandom().randint(1, 10 ** 9)
    items, extra = build(random.Random(seed), a.hard)
    out = {"version": 1, "hard": a.hard, "n": len(items), "extra": extra,
           "items": [{"id": it["id"], "q": it["q"], "format": it["format"],
                      "hmac": seal(a.secret, it["id"], it["_ans"])} for it in items]}
    json.dump(out, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(f"Wrote {a.out} ({len(items)} questions). The seed is NOT stored; keep your secret private.")

def cmd_ask(a):
    data = json.load(open(a.questions))
    print("Answer every question below. Rules: do NOT run code or use any tools; reason it out yourself.\n"
          "Reply with ONLY a JSON object mapping question id -> answer, in the given format.\n")
    for it in data["items"]:
        print(f"[{it['id']}] {it['q']}   (format: {it['format']})")
    print("\n===== HAYSTACK =====\n" + data["extra"]["haystack"] + "\n===== END HAYSTACK =====")

def cmd_grade(a):
    data = json.load(open(a.questions))
    raw = open(a.answers).read()
    m = re.search(r"\{.*\}", raw, re.S)                 # tolerate prose around the JSON
    ans = json.loads(m.group(0)) if m else {}
    ok = 0
    for it in data["items"]:
        given = ans.get(it["id"])
        good = given is not None and hmac.compare_digest(seal(a.secret, it["id"], given), it["hmac"])
        ok += good
        print(f"{'✅' if good else '❌'} {it['id']:9s} answer={given!r}")
    print(f"\nScore: {ok}/{data['n']}")
    if not ok:
        print("(All wrong? Check that you used the same --secret as in `gen`.)")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen");   g.add_argument("--secret", required=True); g.add_argument("--seed", type=int)
    g.add_argument("--hard", action="store_true"); g.add_argument("--out", default="questions.json")
    k = sub.add_parser("ask");   k.add_argument("questions")
    d = sub.add_parser("grade"); d.add_argument("--secret", required=True)
    d.add_argument("questions"); d.add_argument("answers")
    a = ap.parse_args()
    {"gen": cmd_gen, "ask": cmd_ask, "grade": cmd_grade}[a.cmd](a)

if __name__ == "__main__":
    main()
