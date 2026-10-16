# PROGRESS: 量子纠错的最新进展

（已验证发现将按轮次追加在这里）

## [iter 1] 2025–2026 量子纠错最重要的进展与里程碑
- **Google Willow「below threshold」**：表面码实现中，逻辑错误率随物理 qubit 数增加而**下降**（纠错首次跑赢噪声累积）。来源说法冲突待核：[mylistingo](https://mylistingo.com/quantum-computing-error-correction-milestone-2026/) 称"少于 1000 个物理 qubit"（2026-07），[developersmatrix](https://developersmatrix.com/blog/quantum-computing-advancements-2026) 称 Willow = **105 个物理 qubit**（2026-08）。(冲突，iter 2 核实)
- **国际联合团队逻辑 qubit 里程碑**（2026-05-20 宣布）：超导平台，**玻色编码 + 表面码混合**，逻辑 qubit 错误率低于其构成物理 qubit（越过 break-even）。来源：[quantumaiinsiders](https://quantumaiinsiders.com/error-corrected-logical-qubit-milestone/)
- **横向对比**（developersmatrix 表格）：Willow 105 物理 qubit / below threshold；IBM Heron 133 物理 qubit（2-qubit 门错误率 0.05–0.1%）；Quantinuum H2 56 个离子阱 qubit；Microsoft 拓扑 qubit 处于早期。
- 行业含义：路线图从"堆物理 qubit 数量"转向"扩逻辑 qubit"。

## [iter 2] 核实 Willow 物理 qubit 数量（冲突裁决）
- **裁决：105 个物理 qubit**。Nature 论文 "Quantum error correction below the surface code threshold"（arXiv:2408.13687，2024-12-09 宣布）。[computeatlas](https://computeatlas.net/blog/deep-dive-google-willow)、[itechguides](https://www.itechguides.com/unveiling-willow-googles-latest-quantum-chip-innovation-explained/) 交叉一致。
- 精确数据：distance-7 表面码用 101/105 qubit，逻辑错误率 **0.143% ± 0.003% / 纠错周期**，抑制因子 **Λ = 2.14 ± 0.02**（码距每+2），逻辑 qubit 寿命 = 最佳物理 qubit 的 **2.4×**。
- iter 1 的 "<1000 物理 qubit" 说法判定为**不准确**（可能混淆了"达 10⁻⁶ 逻辑错误率需 ~1500 个物理 qubit 的 distance-27 码"这一目标值）。
- **边界澄清**：below-threshold ≠ fault-tolerant。Willow 未展示纠错后的双 qubit 逻辑门；distance-7 占满 101/105 qubit → 同一时间只能承载 1 个逻辑 qubit。
