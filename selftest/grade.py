import json
key = {i["id"]: i for i in json.load(open("selftest/answers_key.json"))}
mine = json.load(open("selftest/my_answers.json"))
ok = 0
for k, it in key.items():
    good = mine.get(k) == it["ans"]
    ok += good
    print(f"{'✅' if good else '❌'} {k:9s} mine={mine.get(k)!r:<40} truth={it['ans']!r}")
print(f"\nScore: {ok}/{len(key)}")
