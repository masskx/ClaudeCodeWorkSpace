#!/usr/bin/env python3
"""H08 配图：空间不相交划分长什么样（种子 0），以及各类在训练/测试里的样本数。
用法：python3 exp_disjoint_viz.py <复跑目录> <输出目录>
划分规则与 exp_disjoint_cnn.py 完全一致（20×20 方块、约 30% 训练 / 10% 验证、切比雪夫距离 ≤ 8 的隔离带）。"""
import sys, os, json
import numpy as np
from scipy.io import loadmat
from scipy.ndimage import maximum_filter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

RUN, OUT = sys.argv[1], sys.argv[2]
for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
sys.path.insert(0, os.path.join(RUN, "src"))
from hsi_learning.data import DATASET_SPECS
names = list(DATASET_SPECS["IP"].class_names)
gt = loadmat(os.path.join(RUN, "dataset/Indian_pines_gt.mat"))["indian_pines_gt"]
H, W = gt.shape
rows, cols = np.nonzero(gt); y = gt[rows, cols] - 1
BS, FT, FV = 20, 0.30, 0.10


def split(seed):
    rng = np.random.default_rng(seed)
    nbc = int(np.ceil(W / BS)); bid = (rows // BS) * nbc + (cols // BS)
    ub = np.unique(bid); rng.shuffle(ub)
    nt = int(round(len(ub) * FT)); nv = max(1, int(round(len(ub) * FV)))
    tr = np.isin(bid, ub[:nt]); va = np.isin(bid, ub[nt:nt + nv]); te = ~(tr | va)
    m = np.zeros((H, W), bool); m[rows[tr], cols[tr]] = True
    near = maximum_filter(m, size=17)[rows, cols]
    return tr, va & ~near, te & ~near, va & near, te & near, (va | te)


out = {}
fig, axes = plt.subplots(1, 3, figsize=(15, 5.2))
cmap = ListedColormap(["#000000", "#2878d6", "#1aa97b", "#ec6a34", "#9a9a9a"])
for ax, seed in zip(axes, (0, 1, 2)):
    tr, va, te, va_b, te_b, _ = split(seed)
    img = np.zeros((H, W), int)
    img[rows[tr], cols[tr]] = 1; img[rows[va], cols[va]] = 2; img[rows[te], cols[te]] = 3
    img[rows[va_b | te_b], cols[va_b | te_b]] = 4
    ax.imshow(img, cmap=cmap, vmin=0, vmax=4, interpolation="nearest")
    ax.set_title(f"种子 {seed}：训练 {int(tr.sum())} / 验证 {int(va.sum())} / 测试 {int(te.sum())}\n被隔离带剔除 {int((va_b|te_b).sum())}", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
    ctr = np.bincount(y[tr], minlength=16); cte = np.bincount(y[te], minlength=16)
    out[seed] = {"train": ctr.tolist(), "test": cte.tolist(), "train_total": int(tr.sum()), "test_total": int(te.sum()),
                 "excluded_by_buffer": int((va_b | te_b).sum())}
axes[1].legend(handles=[Patch(color=c, label=l) for c, l in zip(["#2878d6", "#1aa97b", "#ec6a34", "#9a9a9a", "#000000"],
               ["训练", "验证", "测试", "隔离带内被剔除（不用）", "未标注"])], loc="upper center",
               bbox_to_anchor=(0.5, -0.02), ncol=5, frameon=False, fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "08-disjoint-split-maps.png"), dpi=160)
json.dump({"class_names": names, "seeds": out}, open(os.path.join(OUT, "disjoint_split_counts.json"), "w"), ensure_ascii=False, indent=1)
for s, v in out.items():
    print(s, "train-absent classes:", [names[i] for i in range(16) if v["train"][i] == 0],
          "| test-absent:", [names[i] for i in range(16) if v["test"][i] == 0])
