#!/usr/bin/env python3
"""实验：同一个 SVM，随机划分 vs 空间分块划分，结果差多少？
用法：python3 exp_split_leakage.py <HSI-Learning 仓库路径> <输出目录>
设置沿用课程 notebooks/02 的 SVM（RBF，C=100，gamma='scale'，原始 200 波段），随机划分为 80/20 分层。
空间分块划分：把图像切成 10×10 像素的方块，随机挑约 20% 的方块当测试区，其余方块的标注像素当训练。
重复 3 个随机种子。AA 只对测试集里出现过的类别求平均（见文章说明）。"""
import sys, os, json, time
import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, cohen_kappa_score, recall_score

REPO, OUT = sys.argv[1], sys.argv[2]
for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
cube = loadmat(os.path.join(REPO, "dataset/Indian_pines_corrected.mat"))["indian_pines_corrected"].astype(np.float32)
gt = loadmat(os.path.join(REPO, "dataset/Indian_pines_gt.mat"))["indian_pines_gt"]
H, W, B = cube.shape
rows, cols = np.nonzero(gt)
X = cube[rows, cols]; y = gt[rows, cols]

def metrics(yt, yp):
    present = np.unique(yt)
    oa = accuracy_score(yt, yp)
    aa = recall_score(yt, yp, labels=present, average="macro", zero_division=0)
    kp = cohen_kappa_score(yt, yp)
    return oa, aa, kp, len(present)

res = {"random": [], "block": []}
BS = 10
nbr, nbc = int(np.ceil(H / BS)), int(np.ceil(W / BS))
block_id = (rows // BS) * nbc + (cols // BS)
maps = {}
for seed in (11, 12, 13):
    t = time.time()
    tr, te = train_test_split(np.arange(len(y)), test_size=0.2, stratify=y, random_state=seed)
    m = SVC(C=100, kernel="rbf", cache_size=2048).fit(X[tr], y[tr])
    res["random"].append(metrics(y[te], m.predict(X[te])) + (len(tr), len(te)))
    rng = np.random.RandomState(seed)
    ub = np.unique(block_id); test_blocks = set(rng.choice(ub, size=int(round(0.2 * len(ub))), replace=False))
    is_te = np.array([b in test_blocks for b in block_id]); tr2, te2 = np.nonzero(~is_te)[0], np.nonzero(is_te)[0]
    m2 = SVC(C=100, kernel="rbf", cache_size=2048).fit(X[tr2], y[tr2])
    res["block"].append(metrics(y[te2], m2.predict(X[te2])) + (len(tr2), len(te2)))
    if seed == 11:
        maps["rand"] = (tr, te); maps["block"] = (tr2, te2)
    print(seed, "random", [round(v, 4) for v in res["random"][-1][:3]], "block", [round(v, 4) for v in res["block"][-1][:3]], f"{time.time()-t:.0f}s", flush=True)

json.dump(res, open(os.path.join(OUT, "split_experiment.json"), "w"), indent=1)
INK, MUTE, GRID = "#0b0b0b", "#52514e", "#e6e4de"; BLUE, ORANGE = "#2a78d6", "#eb6834"
fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.8), constrained_layout=True, gridspec_kw={"width_ratios": [1, 1, 1.15]})
for ax, key, title in [(axes[0], "rand", "随机划分（种子 11）"), (axes[1], "block", "空间分块划分（种子 11）")]:
    img = np.zeros((H, W)); tr, te = maps[key]
    img[rows[tr], cols[tr]] = 1; img[rows[te], cols[te]] = 2
    ax.imshow(np.ma.masked_equal(img, 0), cmap=matplotlib.colors.ListedColormap([BLUE, ORANGE]), vmin=1, vmax=2, interpolation="nearest")
    ax.set_facecolor("#f1f0ec"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{title}\n蓝 = 训练 {len(tr)}　橙 = 测试 {len(te)}", fontsize=11)
ax = axes[2]
names = ["OA", "AA", "Kappa"]
rm = np.array(res["random"])[:, :3] * [100, 100, 100]; bm = np.array(res["block"])[:, :3] * [100, 100, 100]
x = np.arange(3); w = 0.36
ax.bar(x - w/2, rm.mean(0), w, color=BLUE, label="随机划分（3 个种子均值）")
ax.bar(x + w/2, bm.mean(0), w, color=ORANGE, label="空间分块划分（3 个种子均值）")
for i in range(3):
    ax.plot([x[i]-w/2]*2, [rm[:, i].min(), rm[:, i].max()], color=INK, lw=1.2)
    ax.plot([x[i]+w/2]*2, [bm[:, i].min(), bm[:, i].max()], color=INK, lw=1.2)
    ax.text(x[i]-w/2, rm.mean(0)[i]+1.5, f"{rm.mean(0)[i]:.1f}", ha="center", fontsize=10)
    ax.text(x[i]+w/2, bm.mean(0)[i]+1.5, f"{bm.mean(0)[i]:.1f}", ha="center", fontsize=10)
ax.set_xticks(x); ax.set_xticklabels(["OA（%）", "AA（%）", "Kappa×100"]); ax.set_ylim(0, 105)
ax.legend(frameon=False, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.12)); ax.set_title("同一个 SVM，两种划分，结果差多少\n（黑线 = 3 个种子的最小到最大）", fontsize=11)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)
fig.savefig(os.path.join(OUT, "03-split-leakage-experiment.png"), dpi=130)
print("done")
