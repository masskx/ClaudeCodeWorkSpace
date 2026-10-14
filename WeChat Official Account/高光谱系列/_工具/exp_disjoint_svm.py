#!/usr/bin/env python3
"""H08 对照：同样的随机/空间不相交划分（与 exp_disjoint_cnn.py 完全相同的种子与规则），换成像素级 SVM。
用法：python3 exp_disjoint_svm.py <复跑目录> <输出目录>
SVM 设置同课程 notebooks/02：RBF，C=100，gamma='scale'，原始 200 波段（不做标准化）。
读取 <输出目录>/disjoint_experiment.json（CNN 的结果），写 svm_disjoint.json 并画 08-svm-vs-cnn.png。"""
import sys, os, json
import numpy as np
from scipy.io import loadmat
from scipy.ndimage import maximum_filter
from sklearn.svm import SVC
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUN, OUT = sys.argv[1], sys.argv[2]
cube = loadmat(os.path.join(RUN, "dataset/Indian_pines_corrected.mat"))["indian_pines_corrected"].astype(np.float32)
gt = loadmat(os.path.join(RUN, "dataset/Indian_pines_gt.mat"))["indian_pines_gt"]
H, W, B = cube.shape
rows, cols = np.nonzero(gt); y = gt[rows, cols] - 1
X = cube[rows, cols]
BS, FT, FV = 20, 0.30, 0.10


def disjoint_split(seed):  # 与 exp_disjoint_cnn.py 逐行一致
    rng = np.random.default_rng(seed)
    nbc = int(np.ceil(W / BS)); bid = (rows // BS) * nbc + (cols // BS)
    ub = np.unique(bid); rng.shuffle(ub)
    nt = int(round(len(ub) * FT)); nv = max(1, int(round(len(ub) * FV)))
    tr = np.isin(bid, ub[:nt]); va = np.isin(bid, ub[nt:nt + nv]); te = ~(tr | va)
    m = np.zeros((H, W), bool); m[rows[tr], cols[tr]] = True
    near = maximum_filter(m, size=17)[rows, cols]
    return np.where(tr)[0], np.where(va & ~near)[0], np.where(te & ~near)[0]


def random_split(seed, ntr, nva, nte):
    rng = np.random.default_rng(1000 + seed); p = rng.permutation(len(y))
    return p[:ntr], p[ntr:ntr + nva], p[ntr + nva:ntr + nva + nte]


def metrics(tr, te, pred):
    yt = y[te]; seen = np.isin(yt, np.unique(y[tr]))
    cls = [c for c in np.unique(yt) if c in np.unique(y[tr])]
    return (float((pred == yt).mean()), float((pred[seen] == yt[seen]).mean()),
            float(np.mean([(pred[yt == c] == c).mean() for c in cls])))


res = []
for s in range(3):
    tr, va, te = disjoint_split(s)
    rtr, rva, rte = random_split(s, len(tr), len(va), len(te))
    row = {"seed": s}
    for name, (a, b) in {"disjoint": (tr, te), "random": (rtr, rte)}.items():
        pred = SVC(kernel="rbf", C=100, gamma="scale").fit(X[a], y[a]).predict(X[b])
        row[name] = dict(zip(["OA_all", "OA_seen", "AA_seen"], metrics(a, b, pred)))
    res.append(row); print(json.dumps(row), flush=True)
json.dump(res, open(os.path.join(OUT, "svm_disjoint.json"), "w"), indent=1)

cnn = json.load(open(os.path.join(OUT, "disjoint_experiment.json")))["runs"]
for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
fig, ax = plt.subplots(figsize=(7.6, 4.6))
vals = {}
for lab, src in [("像素级 SVM（只看光谱）", res), ("2D CNN（9×9 邻域）", cnn)]:
    for mode in ("random", "disjoint"):
        v = [r[mode]["OA_all"] * 100 for r in src]; vals[(lab, mode)] = (np.mean(v), np.std(v))
x = np.arange(2); w = 0.36
for j, (mode, lab, col) in enumerate([("random", "随机划分", "#2878d6"), ("disjoint", "空间不相交划分", "#ec6a34")]):
    m = [vals[(l, mode)][0] for l in ("像素级 SVM（只看光谱）", "2D CNN（9×9 邻域）")]
    sd = [vals[(l, mode)][1] for l in ("像素级 SVM（只看光谱）", "2D CNN（9×9 邻域）")]
    ax.bar(x + (j - 0.5) * w, m, w, yerr=sd, capsize=3, color=col, label=lab)
    for xi, mm, ss in zip(x + (j - 0.5) * w, m, sd): ax.text(xi, mm + ss + 2, f"{mm:.1f}", ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(["像素级 SVM（只看光谱）", "2D CNN（9×9 邻域）"])
ax.set_ylim(0, 125); ax.set_ylabel("测试集 OA（%）")
ax.set_title("同样的划分、同样的训练样本数：谁更依赖“邻居泄漏”？（3 个种子）", fontsize=10)
ax.legend(loc="upper center", ncol=2, frameon=False)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "08-svm-vs-cnn.png"), dpi=170)
