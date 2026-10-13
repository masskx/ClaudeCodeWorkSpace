#!/usr/bin/env python3
"""汇总 H06：1D/2D/3D CNN 的复跑结果，并画"逐类召回率"对比图。
用法：python3 collect_cnn_results.py <复跑目录(含 results/*)> <HSI-Learning 仓库路径> <输出目录>
读取每次运行的 confusion_matrix.npy / metrics.json / training_history.json，
输出 06-per-class-recall.png 与 cnn_repro_summary.json（复跑数 vs 课程记录数）。
复跑数字来自本机 CPU 上重新执行课程的 scripts/train_{1d,2d,3d}_cnn.py，种子、划分与课程一致。"""
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

# 课程记录数（docs/benchmark.md 协议 C）
course = {
    "1d_cnn_15": (61.10, 44.64, 0.5424), "1d_cnn_60": (75.27, 60.15, 0.7147),
    "2d_cnn_10": (70.01, 49.18, 0.6469), "2d_cnn_40": (95.83, 87.04, 0.9525),
    "3d_cnn_10": (59.82, 31.90, 0.5170), "3d_cnn_40": (94.55, 76.53, 0.9377),
}
summary, recalls = {}, {}
for k, (coa, caa, ckp) in course.items():
    d = os.path.join(RUN, "results", k, "IP")
    m = json.load(open(os.path.join(d, "metrics.json")))
    h = json.load(open(os.path.join(d, "training_history.json")))
    cm = np.load(os.path.join(d, "confusion_matrix.npy"))
    rec = np.diag(cm) / np.maximum(cm.sum(1), 1)
    recalls[k] = (rec, cm.sum(1))
    epochs = len(h["train_loss"])
    summary[k] = {"repro_OA": round(m["oa"] * 100, 2), "repro_AA": round(m["aa"] * 100, 2),
                  "repro_Kappa": round(m["kappa"], 4), "best_epoch": m["best_epoch"], "epochs": epochs,
                  "course_OA": coa, "course_AA": caa, "course_Kappa": ckp,
                  "params": m.get("total_params"),
                  "per_class_recall": [round(float(r), 3) for r in rec], "test_support": [int(s) for s in cm.sum(1)]}
json.dump({"class_names": names, "runs": summary}, open(os.path.join(OUT, "cnn_repro_summary.json"), "w"),
          ensure_ascii=False, indent=1)

fig, ax = plt.subplots(figsize=(13, 6.2))
x = np.arange(16); w = 0.27
for i, (k, lab, col) in enumerate([("1d_cnn_60", "1D CNN (60 epochs)", "#2878d6"),
                                    ("2d_cnn_40", "2D CNN (40 epochs)", "#ec6a34"),
                                    ("3d_cnn_40", "3D CNN (40 epochs)", "#1aa97b")]):
    ax.bar(x + (i - 1) * w, recalls[k][0], w, label=lab, color=col)
sup = recalls["2d_cnn_40"][1]
ax.set_xticks(x)
ax.set_xticklabels([f"{j+1} {names[j]} (n={sup[j]})" for j in range(16)], fontsize=8, rotation=40, ha="right")
ax.set_ylabel("召回率（该类测试样本中被找对的比例）")
ax.set_ylim(0, 1.05)
ax.axhline(1, color="#bbb", lw=0.6)
ax.set_title("同一协议（10/10/80，seed 42）下三种卷积的逐类召回率——稀有类才是差距所在", fontsize=12)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.42), ncol=3, frameon=False)
for s in ("top", "right"): ax.spines[s].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "06-per-class-recall.png"), dpi=170)
print(json.dumps({k: (v["repro_OA"], v["repro_AA"], v["best_epoch"], v["epochs"]) for k, v in summary.items()}))
