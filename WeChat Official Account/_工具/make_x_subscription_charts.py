#!/usr/bin/env python3
"""第 17 篇（X Subscription 全家桶）的两张数据图。
用法：python3 make_x_subscription_charts.py <输出目录，如 17-.../imgs>
图 1：每档“每 1 倍用量”折合多少美元（月付）。月付价格与用量倍数来自第三方整理（cellcog.ai、explainx 等转述官方页），
      官方公告只确认了“每档至少是同级 Cursor 套餐 2 倍的 Grok 编码用量”，倍数本身我没能在官方页核实；Plus 不含 Grok Bot 与 Cursor 云端代理，档与档并不完全同口径。
图 2：两种典型用户的账单变化（示意，不是实测）。数字来自：官方称 SuperGrok+Cursor Pro+X Premium+ 原价合计 $90/月（30+20+40）；
      Cursor Pro 原含约 $20 第三方模型用量，转入后第三方模型按 API 标价另付（The New Stack、Substack 转述）。
配色：蓝 #2878d6 / 橙 #ec6a34（已用 dataviz 的 validate_palette.js 验证：相邻 ΔE 24.9，对比度通过）。"""
import sys, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False, "text.parse_math": False})
BLUE, ORANGE, INK, MUTED, GRID = "#2878d6", "#ec6a34", "#0b0b0b", "#52514e", "#e4e3df"

# ---------- 图 1 ----------
tiers = ["Plus", "Premium", "Super", "Ultra"]
price = [8, 30, 100, 200]
mult = [1, 4, 15, 50]
per = [p / m for p, m in zip(price, mult)]
fig, ax = plt.subplots(figsize=(8.6, 4.4), facecolor="#fcfcfb")
ax.set_facecolor("#fcfcfb")
bars = ax.barh(tiers[::-1], per[::-1], color=BLUE, height=0.55)
for b, t, p, m, v in zip(bars, tiers[::-1], price[::-1], mult[::-1], per[::-1]):
    ax.text(v + 0.15, b.get_y() + b.get_height() / 2, f"${v:.2f}  （${p} ÷ {m} 倍）", va="center", fontsize=10, color=INK)
ax.set_xlim(0, 11.5)
ax.set_xlabel("每 1 倍用量折合的月费（美元）", color=MUTED)
ax.set_title("越贵的档，每单位用量越便宜：Ultra 比 Plus 便宜一半", fontsize=12, color=INK, loc="left")
ax.xaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.tick_params(axis="y", length=0, labelsize=11); ax.tick_params(axis="x", labelcolor=MUTED)
fig.text(0.01, 0.01, "用量倍数（以 Plus=1 倍）：Premium 4、Super 15、Ultra 50，来自第三方整理，官方页未逐项核实；Plus 不含 Grok Bot。", fontsize=7.5, color=MUTED)
plt.tight_layout(rect=(0, 0.04, 1, 1)); plt.savefig(os.path.join(OUT, "01-chart-price-per-usage.png"), dpi=200); plt.close()

# ---------- 图 2 ----------
labels = ["三个都订\n现在", "三个都订\n转入 Premium", "只在 Cursor 里用\nClaude/GPT\n现在", "只在 Cursor 里用\nClaude/GPT\n转入 Premium"]
sub = [90, 30, 20, 30]
api = [0, 0, 0, 20]
fig, ax = plt.subplots(figsize=(8.8, 4.8), facecolor="#fcfcfb")
ax.set_facecolor("#fcfcfb")
xs = [0, 1, 2.6, 3.6]
ax.bar(xs, sub, 0.62, color=BLUE, label="套餐订阅费")
ax.bar(xs, api, 0.62, bottom=sub, color=ORANGE, label="第三方模型按 API 标价另付", edgecolor="#fcfcfb", linewidth=2)
for x, s, a in zip(xs, sub, api):
    ax.text(x, s + a + 2.5, f"${s + a}", ha="center", fontsize=11, color=INK, fontweight="bold")
    if a: ax.text(x, s + a / 2, f"+${a}", ha="center", va="center", fontsize=9, color="white")
    ax.text(x, s / 2, f"${s}", ha="center", va="center", fontsize=9, color="white")
ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=8.5, color=INK)
ax.set_ylim(0, 108); ax.set_ylabel("每月美元", color=MUTED)
ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.legend(frameon=False, loc="upper right", fontsize=9)
ax.set_title("同一个“全家桶”，对两类人完全是两笔账（示意）", fontsize=12, color=INK, loc="left")
fig.text(0.01, 0.01, "左：SuperGrok $30 + Cursor Pro $20 + X Premium+ $40 = $90（官方口径）。右：Cursor Pro 含约 $20 第三方模型用量，转入 Premium 后另付（The New Stack 转述的算例）。", fontsize=7, color=MUTED)
plt.tight_layout(rect=(0, 0.04, 1, 1)); plt.savefig(os.path.join(OUT, "02-chart-bill-scenarios.png"), dpi=200); plt.close()
print("ok")
