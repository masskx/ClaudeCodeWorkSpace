#!/usr/bin/env python3
"""H10/H12：汇总 2D CNN 的损失函数消融（CE / 加权 CE / Focal，3 个种子）。
用法：python3 collect_loss_ablation.py <复跑目录> <HSI-Learning 仓库路径> <输出目录>
复跑目录需有：results/2d_cnn_40/IP（种子 42 的 CE 基线，来自 H06 的复跑）、results/ch15/{ce,weighted,focal}_seed{42,1334,1335}/IP
（CE 种子 42 复用 2d_cnn_40，因为命令完全相同）。
输出：loss_ablation.json、10-loss-ablation.png（左：OA/AA 均值±标准差并叠加每个种子的点；右：三个稀有类的逐种子召回）。"""
import sys, os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUN, REPO, OUT = sys.argv[1:4]
for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
sys.path.insert(0, os.path.join(REPO, "src"))
from hsi_learning.data import DATASET_SPECS
names = list(DATASET_SPECS["IP"].class_names)
SEEDS = [42, 1334, 1335]


def path(loss, seed):
    if loss == "ce" and seed == 42:
        return os.path.join(RUN, "results/2d_cnn_40/IP")
    return os.path.join(RUN, f"results/ch15/{loss}_seed{seed}/IP")


res = {}
for loss in ("ce", "weighted", "focal"):
    runs = []
    for s in SEEDS:
        d = path(loss, s)
        m = json.load(open(os.path.join(d, "metrics.json")))
        cm = np.load(os.path.join(d, "confusion_matrix.npy"))
        runs.append({"seed": s, "OA": m["oa"] * 100, "AA": m["aa"] * 100, "Kappa": m["kappa"], "best_epoch": m["best_epoch"],
                     "recall": (np.diag(cm) / cm.sum(1)).tolist()})
    res[loss] = runs
json.dump({"class_names": names, "runs": res}, open(os.path.join(OUT, "loss_ablation.json"), "w"), ensure_ascii=False, indent=1)

summ = {}
for loss, runs in res.items():
    summ[loss] = {k: (float(np.mean([r[k] for r in runs])), float(np.std([r[k] for r in runs], ddof=1))) for k in ("OA", "AA", "Kappa")}
print(json.dumps(summ, indent=1))

fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [1, 1.25]})
labs = {"ce": "交叉熵（基线）", "weighted": "加权交叉熵", "focal": "Focal (γ=2)"}
x = np.arange(2); w = 0.26
for j, (loss, col) in enumerate([("ce", "#2878d6"), ("weighted", "#ec6a34"), ("focal", "#1aa97b")]):
    for i, k in enumerate(("OA", "AA")):
        m, sd = summ[loss][k]
        a1.bar(i + (j - 1) * w, m, w, yerr=sd, capsize=3, color=col, alpha=0.85, label=labs[loss] if i == 0 else None)
        a1.scatter([i + (j - 1) * w] * 3, [r[k] for r in res[loss]], color="k", s=10, zorder=3)
        a1.text(i + (j - 1) * w, m + sd + 1.2, f"{m:.1f}", ha="center", fontsize=8)
a1.set_xticks(x); a1.set_xticklabels(["OA", "AA"]); a1.set_ylim(60, 104); a1.set_ylabel("%（黑点=每个种子）")
a1.set_title("三种损失：均值 ± 标准差（3 个种子）"); a1.legend(frameon=False, loc="lower right", fontsize=8)
rare = [0, 6, 8]
width = 0.08; xs = np.arange(len(rare))
for j, (loss, col) in enumerate([("ce", "#2878d6"), ("weighted", "#ec6a34"), ("focal", "#1aa97b")]):
    for k, s in enumerate(SEEDS):
        a2.bar(xs + (j * 3 + k - 4) * width, [res[loss][k]["recall"][c] for c in rare], width, color=col, alpha=0.45 + 0.25 * k,
               label=f"{labs[loss]} 种子 {s}" if True else None)
a2.set_xticks(xs); a2.set_xticklabels([f"{names[c]}\n(测试样本 {n})" for c, n in zip(rare, (37, 22, 16))])
a2.set_ylabel("召回率"); a2.set_title("三个稀有类的逐种子召回：同一设置换个种子，结果会整个翻转")
a2.legend(frameon=False, fontsize=6.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.12))
for s_ in ("top", "right"):
    a1.spines[s_].set_visible(False); a2.spines[s_].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "10-loss-ablation.png"), dpi=165)
