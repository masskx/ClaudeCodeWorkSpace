#!/usr/bin/env python3
"""H11：汇总小样本（ProtoNet）与开集（MSP / 距离）的复跑结果并画图。
用法：python3 collect_fewshot_openset.py <复跑目录> <输出目录>
读取（均由课程脚本 scripts/train_protonet.py、scripts/train_openset.py 产生）：
  results/protonet/{metrics,history,split}.json|npz           （种子 42）
  results/openset/metrics.json（种子 42）、results/openset_s{1..4}/metrics.json
输出：11-protonet-kshot.png、11-openset-seeds.png、fewshot_openset_summary.json。"""
import sys, os, json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUN, OUT = sys.argv[1], sys.argv[2]
for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
summary = {}

# ---------- ProtoNet ----------
m = json.load(open(os.path.join(RUN, "results/protonet/metrics.json")))
h = json.load(open(os.path.join(RUN, "results/protonet/history.json")))
acc = {int(k): np.array(v["accuracies"]) for k, v in m["kshot"].items()}
summary["protonet"] = {"kshot_mean": {k: float(v.mean()) for k, v in acc.items()},
                       "kshot_episode_std": {k: float(v.std(ddof=1)) for k, v in acc.items()},
                       "n_episodes": int(len(acc[1])),
                       "paired_diff_5_minus_1": [float((acc[5] - acc[1]).mean()), float((acc[5] - acc[1]).std(ddof=1) / np.sqrt(len(acc[1])))],
                       "paired_diff_10_minus_5": [float((acc[10] - acc[5]).mean()), float((acc[10] - acc[5]).std(ddof=1) / np.sqrt(len(acc[1])))],
                       "episodes_10_better_worse_tie_than_5": [int((acc[10] > acc[5]).sum()), int((acc[10] < acc[5]).sum()), int((acc[10] == acc[5]).sum())],
                       "annotation_budget": m["annotation_budget"], "best_val": m["best_val"],
                       "val_accuracy_at_episodes": dict(zip(h["episode"], h["val_accuracy"]))}
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.6), gridspec_kw={"width_ratios": [1, 1.1]})
rng = np.random.default_rng(0)
for i, k in enumerate((1, 5, 10)):
    a1.scatter(i + rng.uniform(-0.18, 0.18, len(acc[k])), acc[k] * 100, s=14, alpha=0.6, color=["#2878d6", "#ec6a34", "#1aa97b"][i])
    a1.hlines(acc[k].mean() * 100, i - 0.3, i + 0.3, color="k", lw=2)
    a1.text(i + 0.33, acc[k].mean() * 100, f"{acc[k].mean()*100:.1f}", va="center", fontsize=10)
a1.axhline(20, ls="--", color="#999", lw=1); a1.text(2.45, 21.5, "随机猜（5 类）= 20%", ha="right", fontsize=8, color="#666")
a1.set_xticks([0, 1, 2]); a1.set_xticklabels(["1-shot", "5-shot", "10-shot"]); a1.set_ylim(0, 105); a1.set_ylabel("单个 episode 的准确率（%）")
a1.set_title(f"同一个冻结的 encoder，{len(acc[1])} 个 episode（每个 25 个 query）")
loss = np.array(h["loss"]); k = 20
a2.plot(np.arange(1, len(loss) + 1), loss, color="#cfd8e3", lw=0.8, label="每个 episode 的损失")
a2.plot(np.arange(k, len(loss) + 1), np.convolve(loss, np.ones(k) / k, mode="valid"), color="#2878d6", lw=2, label=f"{k} 个 episode 滑动平均")
a2b = a2.twinx(); a2b.plot(h["episode"], np.array(h["val_accuracy"]) * 100, "o-", color="#ec6a34", label="验证任务准确率（右轴）")
a2.set_xlabel("训练 episode"); a2.set_ylabel("损失"); a2b.set_ylabel("%"); a2b.set_ylim(0, 100)
a2.set_title("元训练过程"); h1, l1 = a2.get_legend_handles_labels(); h2, l2 = a2b.get_legend_handles_labels(); a2.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="center right")
for s_ in ("top", "right"): a1.spines[s_].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "11-protonet-kshot.png"), dpi=165); plt.close()

# ---------- Open-set ----------
runs = {}
for name, path in [("42", "results/openset")] + [(str(s), f"results/openset_s{s}") for s in (1, 2, 3, 4)]:
    p = os.path.join(RUN, path, "metrics.json")
    if os.path.exists(p): runs[name] = json.load(open(p))
rows = []
for name, r in runs.items():
    rows.append({"seed": name, "known_accuracy": r["known_accuracy"], "msp_auroc": r["msp"]["auroc"], "dist_auroc": r["distance"]["auroc"],
                 "msp_unknown_recall": r["msp"]["unknown_recall"], "dist_unknown_recall": r["distance"]["unknown_recall"],
                 "msp_known_false_rejection": r["msp"]["known_false_rejection"], "dist_known_false_rejection": r["distance"]["known_false_rejection"]})
summary["openset"] = rows
if rows:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4))
    x = np.arange(len(rows)); w = 0.36
    for ax, (k1, k2, ttl) in zip((a1, a2), [("msp_auroc", "dist_auroc", "未知分数的排序能力：AUROC（越高越好，0.5=乱排）"),
                                             ("msp_unknown_recall", "dist_unknown_recall", "在 95% 已知接受率的阈值下：未知召回")]):
        ax.bar(x - w / 2, [r[k1] for r in rows], w, color="#2878d6", label="MSP（1−最大 softmax）")
        ax.bar(x + w / 2, [r[k2] for r in rows], w, color="#ec6a34", label="到最近原型的距离")
        for xi, r in zip(x, rows):
            ax.text(xi - w / 2, r[k1] + 0.015, f"{r[k1]:.2f}", ha="center", fontsize=8); ax.text(xi + w / 2, r[k2] + 0.015, f"{r[k2]:.2f}", ha="center", fontsize=8)
        ax.set_xticks(x); ax.set_xticklabels([f"种子 {r['seed']}" for r in rows]); ax.set_ylim(0, 1.22); ax.set_title(ttl, fontsize=10)
        for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
    a1.axhline(0.5, ls="--", color="#999", lw=1); a1.legend(frameon=False, fontsize=8, loc="upper right")
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "11-openset-seeds.png"), dpi=165); plt.close()
json.dump(summary, open(os.path.join(OUT, "fewshot_openset_summary.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(summary["protonet"], ensure_ascii=False)[:800]); print(json.dumps(rows, ensure_ascii=False)[:1500])
