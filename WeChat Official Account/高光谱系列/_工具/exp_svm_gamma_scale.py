#!/usr/bin/env python3
"""实验：SVM 的 gamma 网格要和特征尺度匹配。
同一个 train2/val 划分（课程 ch03 的设置：80/20 分层后，再把训练集切 75/25，种子 11）：
 (a) 原始 DN 特征 + 教科书网格 gamma∈[1e-4,1e-1]
 (b) 先标准化（StandardScaler，只在 train2 上拟合）+ 同样的教科书网格
用法：python3 exp_svm_gamma_scale.py <仓库路径> <输出目录>"""
import sys, os, json
import numpy as np
from scipy.io import loadmat
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
REPO, OUT = sys.argv[1], sys.argv[2]
for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
cube = loadmat(os.path.join(REPO, "dataset/Indian_pines_corrected.mat"))["indian_pines_corrected"].astype(np.float32)
gt = loadmat(os.path.join(REPO, "dataset/Indian_pines_gt.mat"))["indian_pines_gt"]
X = cube.reshape(-1, 200); y = gt.ravel(); l = y > 0
Xtr, Xte, ytr, yte = train_test_split(X[l], y[l], test_size=0.2, random_state=11, stratify=y[l])
X2, Xv, y2, yv = train_test_split(Xtr, ytr, test_size=0.25, random_state=11, stratify=ytr)
Cs = [0.1, 1, 10, 100]; Gs = [1e-4, 1e-3, 1e-2, 1e-1]
def grid(A, B):
    out = np.zeros((4, 4))
    for i, c in enumerate(Cs):
        for j, g in enumerate(Gs):
            out[i, j] = accuracy_score(yv, SVC(C=c, gamma=g, cache_size=2048).fit(A, y2).predict(B))
    return out
ga = grid(X2, Xv)
sc = StandardScaler().fit(X2); gb = grid(sc.transform(X2), sc.transform(Xv))
major = (yv == np.bincount(yv).argmax()).mean()
print("majority-class share in val:", round(major, 4))
print("raw grid:\n", np.round(ga * 100, 1)); print("scaled grid:\n", np.round(gb * 100, 1))
# 标准化后，gamma='scale' 的值
print("gamma='scale' raw:", 1 / (200 * X2.var()), " scaled:", 1 / (200 * sc.transform(X2).var()))
json.dump({"raw": ga.tolist(), "scaled": gb.tolist(), "majority": float(major)}, open(os.path.join(OUT, "gamma_scale_experiment.json"), "w"))
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8), constrained_layout=True)
for ax, G, t in [(axes[0], ga, "(a) 原始 DN 特征 + 教科书网格"), (axes[1], gb, "(b) 先标准化 + 同一个网格")]:
    im = ax.imshow(G * 100, cmap="Blues", vmin=0, vmax=100)
    for i in range(4):
        for j in range(4): ax.text(j, i, f"{G[i,j]*100:.1f}", ha="center", va="center", color="white" if G[i, j] > 0.6 else "#0b0b0b", fontsize=11)
    ax.set_xticks(range(4)); ax.set_xticklabels([f"{g:g}" for g in Gs]); ax.set_yticks(range(4)); ax.set_yticklabels([f"C={c:g}" for c in Cs])
    ax.set_xlabel("gamma"); ax.set_title(t, fontsize=11.5)
fig.suptitle(f"验证集准确率（%）；多数类（Soybean-mintill）占验证集的 {major*100:.1f}%", fontsize=11)
fig.savefig(os.path.join(OUT, "04-gamma-scale-experiment.png"), dpi=130)
