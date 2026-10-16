#!/usr/bin/env bash
# SelfLoop tick — 每轮迭代开始时加载的"固定视图"。
# 让每一轮的起点上下文小且一致：迭代号、下一个问题、最近发现、最近日志。
set -euo pipefail
cd "$(dirname "$0")/state"
TODO="TODO.md"; PROG="PROGRESS.md"; ITER="ITERATIONS.md"
[ -f "$PROG" ] || : > "$PROG"
[ -f "$ITER" ] || : > "$ITER"
[ -f "$TODO" ] || : > "$TODO"

n=$(grep -c '^## Iteration' "$ITER" 2>/dev/null || true); n=${n:-0}
f=$(grep -c '^## ' "$PROG" 2>/dev/null || true); f=${f:-0}
b=$(wc -c < "$PROG" 2>/dev/null || true); b=${b:-0}
open=$(grep -c '^- \[ \]' "$TODO" 2>/dev/null || true); open=${open:-0}

echo "=== SELFLOOP · 即将开始 Iteration $n（磁盘已有 $n 条记录 iter 0..$((n-1))；发现 $f 块 / ${b}B；开放问题 $open 个）==="
echo
echo "--- 课题原文 ---"
sed -n '1,6p' "$TODO" | grep -m1 '课题原文' -A1 | tail -1 || true
echo
echo "--- 下一个问题（TODO 首个未勾选项）---"
q=$(awk '/^## Open questions/{f=1;next} f && /^\- \[ \]/{print; exit}' "$TODO")
echo "${q:-（TODO 为空 —— 按协议：判断是否饱和，或补充新子问题）}"
echo
echo "--- PROGRESS 末尾 15 行 ---"
tail -15 "$PROG" 2>/dev/null || true
echo
echo "--- 最近 3 轮日志 ---"
grep '^## Iteration' "$ITER" | tail -3 || echo "(无)"
