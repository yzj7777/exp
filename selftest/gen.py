"""Generate a seeded, objectively-gradable capability probe set (no model-identity probes)."""
import json, random, string, datetime
SEED = 20261016
r = random.Random(SEED)
items = []
# 1-3 multiplication
for i in range(3):
    a, b = r.randint(1000, 9999), r.randint(1000, 9999)
    items.append({"id": f"mul{i}", "q": f"{a} * {b} = ?", "ans": a*b})
# 4-5 modular exponent
for i in range(2):
    b, e, m = r.randint(2, 50), r.randint(10, 60), r.choice([97, 101, 113, 127])
    items.append({"id": f"modexp{i}", "q": f"{b}^{e} mod {m} = ?", "ans": pow(b, e, m)})
# 6-7 letter counting in random string
for i in range(2):
    s = "".join(r.choice("abcdefr") for _ in range(48)); c = r.choice("abr")
    items.append({"id": f"count{i}", "q": f"How many '{c}' in: {s}", "ans": s.count(c)})
# 8-9 weekday
for i in range(2):
    d = datetime.date(r.randint(1900, 2100), r.randint(1, 12), r.randint(1, 28))
    items.append({"id": f"weekday{i}", "q": f"Weekday of {d.isoformat()}? (English name)", "ans": d.strftime("%A")})
# 10 sorting
lst = [r.randint(-500, 500) for _ in range(12)]
items.append({"id": "sort", "q": f"Sort ascending: {lst}", "ans": sorted(lst)})
# 11 reverse word
w = "".join(r.choice(string.ascii_lowercase) for _ in range(17))
items.append({"id": "reverse", "q": f"Reverse the string: {w}", "ans": w[::-1]})
# 12 primes count
lo = r.randint(1000, 5000)
items.append({"id": "primes", "q": f"How many primes in [{lo}, {lo+100}]?",
              "ans": sum(all(n % p for p in range(2, int(n**.5)+1)) for n in range(lo, lo+101))})
# 13 logic: knights & knaves style via boolean eval
vals = {k: r.choice([True, False]) for k in "PQRS"}
expr = "((P and not Q) or (R != S)) and not (Q and R) or (S and P and not R)"
items.append({"id": "bool", "q": f"With {vals}, evaluate: {expr}", "ans": eval(expr, {}, vals)})
# 14 base conversion
n = r.randint(10**6, 10**7)
items.append({"id": "hex", "q": f"Convert {n} to hexadecimal (lowercase, no 0x)", "ans": format(n, "x")})
# 15 needle in haystack (context recall)
words = ["alpha","bravo","delta","echo","kilo","lima","oscar","tango","zulu","nova"]
hay = [" ".join(r.choice(words) for _ in range(12)) + "." for _ in range(150)]
key = "".join(r.choice(string.digits) for _ in range(8)); pos = r.randint(30, 120)
hay.insert(pos, f"The secret code is {key}.")
open("selftest/haystack.txt", "w").write("\n".join(hay))
items.append({"id": "needle", "q": "Read selftest/haystack.txt: what is the secret code? On which line (1-based)?",
              "ans": {"code": key, "line": pos + 1}})
json.dump(items, open("selftest/answers_key.json", "w"), indent=1)
for it in items:
    print(it["id"], "|", it["q"])
