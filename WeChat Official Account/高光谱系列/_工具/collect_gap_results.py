#!/usr/bin/env python3
"""H12：汇总迷你 Capstone（HybridSN 拉平 vs 全局平均池化）的全部运行，并画图。
用法：python3 collect_gap_results.py <复跑目录> <输出目录>
读取（复跑目录下 results/）：
  40 epoch（预注册）：hybridsn_C(种子42基线) / hyb_base_s1334 / hyb_base_s1335；hyb_gap_s42 / s1334 / s1335
  120 epoch（事后追加，探索性）：hyb_base_s{42,1334,1335}_e120；hyb_gap_s{42,1334,1335}_e120（缺失的跳过）
输出：hybridsn_gap_summary.json、12-gap-results.png。"""
import sys, os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUN, OUT = sys.argv[1], sys.argv[2]
for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
SEEDS = [42, 1334, 1335]


def load(d):
    p = os.path.join(RUN, "results", d, "IP")
    if not os.path.exists(os.path.join(p, "metrics.json")): return None
    m = json.load(open(os.path.join(p, "metrics.json"))); h = json.load(open(os.path.join(p, "training_history.json")))
    va = np.array(h["val_acc"]); ve = np.array(h["val_epoch"]) if "val_epoch" in h else np.arange(1, len(va) + 1)
    return {"OA": m["oa"] * 100, "AA": m["aa"] * 100, "Kappa": m["kappa"], "best_epoch": int(ve[int(va.argmax())]), "epochs": len(h["train_loss"]),
            "train_loss": h["train_loss"], "train_acc": h["train_acc"]}


dirs = {("base", 40): {42: "hybridsn_C", 1334: "hyb_base_s1334", 1335: "hyb_base_s1335"},
        ("gap", 40): {s: f"hyb_gap_s{s}" for s in SEEDS},
        ("base", 120): {s: f"hyb_base_s{s}_e120" for s in SEEDS},
        ("gap", 120): {s: f"hyb_gap_s{s}_e120" for s in SEEDS}}
res = {k: {s: load(d) for s, d in v.items()} for k, v in dirs.items()}
summary = {}
for (cfg, ep), runs in res.items():
    ok = {s: r for s, r in runs.items() if r}
    summary[f"{cfg}_{ep}"] = {"seeds": {str(s): {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k not in ("train_loss", "train_acc")} for s, r in ok.items()}}
    if ok:
        for k in ("OA", "AA", "Kappa"):
            v = [r[k] for r in ok.values()]; summary[f"{cfg}_{ep}"][k + "_mean_sd"] = [float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else None]
for ep in (40, 120):
    b, g = res[("base", ep)], res[("gap", ep)]
    common = [s for s in SEEDS if b.get(s) and g.get(s)]
    if common:
        summary[f"paired_diff_gap_minus_base_{ep}"] = {k: [round(g[s][k] - b[s][k], 3) for s in common] for k in ("OA", "AA")}
        summary[f"paired_diff_gap_minus_base_{ep}"]["seeds"] = common
json.dump(summary, open(os.path.join(OUT, "hybridsn_gap_summary.json"), "w"), ensure_ascii=False, indent=1)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [1.25, 1]})
groups = [("base", 40, "拉平 40 epoch\n（预注册基线）", "#2878d6"), ("gap", 40, "全局池化 40 epoch\n（预注册改进）", "#ec6a34"),
          ("base", 120, "拉平 120 epoch\n（事后追加）", "#8fb4e8"), ("gap", 120, "全局池化 120 epoch\n（事后追加）", "#f4b38f")]
x = 0; ticks = []; labels = []
for metric in ("OA", "AA"):
    for cfg, ep, lab, col in groups:
        vals = [r[metric] for r in res[(cfg, ep)].values() if r]
        if not vals: x += 1; continue
        a1.bar(x, np.mean(vals), 0.8, color=col, label=lab if metric == "OA" else None)
        a1.scatter([x] * len(vals), vals, color="k", s=12, zorder=3)
        a1.text(x, np.max(vals) + 1.2, f"{np.mean(vals):.1f}", ha="center", fontsize=8)
        x += 1
    ticks.append(x - 2.5); labels.append(metric); x += 1
a1.set_xticks(ticks); a1.set_xticklabels(labels); a1.set_ylim(50, 118); a1.set_ylabel("%（黑点=每个种子；纵轴从 50 开始）")
a1.set_title("协议 C 下 HybridSN：拉平 vs 全局平均池化"); a1.legend(frameon=False, fontsize=8, loc="upper center", ncol=4)
for cfg, col, lab in [("base", "#2878d6", "拉平"), ("gap", "#ec6a34", "全局池化")]:
    for ep, ls in [(40, "-"), (120, "--")]:
        r = res[(cfg, ep)].get(42)
        if r: a2.plot(np.arange(1, len(r["train_loss"]) + 1), r["train_loss"], ls, color=col, label=f"{lab}，{ep} epoch（种子 42）")
a2.set_yscale("log"); from matplotlib.ticker import FuncFormatter; a2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}")); a2.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: "")); a2.set_xlabel("epoch"); a2.set_ylabel("训练损失（对数轴）"); a2.set_title("训练损失：全局池化的版本明显更慢"); a2.legend(frameon=False, fontsize=8)
for s_ in ("top", "right"): a1.spines[s_].set_visible(False); a2.spines[s_].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "12-gap-results.png"), dpi=165)
print(json.dumps({k: v for k, v in summary.items() if k.endswith("mean_sd") or k.startswith("paired") or "_" in k and k.split("_")[0] in ("base", "gap")}, ensure_ascii=False)[:3000])
