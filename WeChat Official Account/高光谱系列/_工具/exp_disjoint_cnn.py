#!/usr/bin/env python3
"""实验：同一个 2D CNN，随机划分 vs 空间不相交划分（带隔离带），成绩差多少？
用法：python3 exp_disjoint_cnn.py <复跑目录(含 scripts/ src/ dataset/)> <输出目录> [种子数=3]
模型/预处理/超参完全沿用课程 scripts/train_2d_cnn.py：PCA-12(whiten，整图拟合) + StandardScaler(仅训练像元拟合)，
9×9 patch，SpectralSpatialCNN2D，Adam(1e-3, wd 1e-4)，批 256，40 epochs，取验证集最优 epoch。
空间不相交划分：把图像切成 20×20 的方块；随机取约 30% 的方块作训练区、约 10% 作验证区、其余作测试区；
再把验证/测试像元里“与任一训练像元的切比雪夫距离 ≤ 8”的剔除（9×9 窗口相互重叠的充要条件），
这样任何测试 patch 与任何训练 patch 都没有共同的输入像元。
随机划分对照：训练/验证/测试样本数与上面一次完全相同，但在全部有标注像元里随机抽。
指标：OA_all（全部测试像元）、OA_seen（只算训练集里出现过的类）、AA_seen（对训练和测试里都出现的类取召回平均）。"""
import sys, os, json, time, importlib.util
import numpy as np
import torch, torch.nn as nn
from scipy.io import loadmat
from scipy.ndimage import maximum_filter
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUN, OUT = sys.argv[1], sys.argv[2]
REPLOT = len(sys.argv) > 3 and sys.argv[3] == "replot"   # 只用已有 json 重画图，不重训
NSEED = 3 if REPLOT or len(sys.argv) <= 3 else int(sys.argv[3])
torch.set_num_threads(2)
sys.path.insert(0, os.path.join(RUN, "src"))
sp = importlib.util.spec_from_file_location("t2d", os.path.join(RUN, "scripts/train_2d_cnn.py"))
t2d = importlib.util.module_from_spec(sp); sp.loader.exec_module(t2d)

cube = loadmat(os.path.join(RUN, "dataset/Indian_pines_corrected.mat"))["indian_pines_corrected"].astype(np.float32)
gt = loadmat(os.path.join(RUN, "dataset/Indian_pines_gt.mat"))["indian_pines_gt"]
H, W, B = cube.shape
rows, cols = np.nonzero(gt); y = gt[rows, cols] - 1
pos = np.stack([rows, cols], 1)
red = PCA(12, whiten=True, random_state=0).fit_transform(cube.reshape(-1, B)).astype(np.float32).reshape(H, W, 12)
BS, FT, FV, EPOCHS = 20, 0.30, 0.10, 40


def disjoint_split(seed):
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


def run(tr, va, te, seed):
    torch.manual_seed(seed); np.random.seed(seed)
    sc = StandardScaler().fit(red[pos[tr, 0], pos[tr, 1]])
    z = sc.transform(red.reshape(-1, 12)).astype(np.float32).reshape(H, W, 12)
    mk = lambda ix: t2d.PatchDataset2D(z, pos[ix], y[ix], 9)
    L = lambda ds, sh: torch.utils.data.DataLoader(ds, batch_size=256, shuffle=sh)
    ltr, lva, lte = L(mk(tr), True), L(mk(va), False), L(mk(te), False)
    model = t2d.SpectralSpatialCNN2D(12, 16)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    best, bs, bepoch = -1, None, 0
    for ep in range(1, EPOCHS + 1):
        model.train()
        for xb, yb in ltr:
            opt.zero_grad(); nn.functional.cross_entropy(model(xb), yb).backward(); opt.step()
        model.eval(); c = n = 0
        with torch.no_grad():
            for xb, yb in lva:
                c += (model(xb).argmax(1) == yb).sum().item(); n += len(yb)
        v = c / max(n, 1)
        if v > best: best, bs, bepoch = v, {k: t.clone() for k, t in model.state_dict().items()}, ep
    model.load_state_dict(bs); model.eval()
    with torch.no_grad():
        pred = np.concatenate([model(xb).argmax(1).numpy() for xb, _ in lte])
    return pred, best, bepoch


def metrics(tr, te, pred):
    yt = y[te]; seen = np.isin(yt, np.unique(y[tr]))
    oa_all = float((pred == yt).mean()); oa_seen = float((pred[seen] == yt[seen]).mean())
    cls = [c for c in np.unique(yt) if c in np.unique(y[tr])]
    aa = float(np.mean([(pred[yt == c] == c).mean() for c in cls]))
    return oa_all, oa_seen, aa, len(np.unique(y[tr])), len(np.unique(yt)), len(cls), float(seen.mean())


res = json.load(open(os.path.join(OUT, "disjoint_experiment.json")))["runs"] if REPLOT else []
for s in range(0 if REPLOT else NSEED):
    tr, va, te = disjoint_split(s)
    t0 = time.time()
    pd_, bv_d, be_d = run(tr, va, te, s)
    md = metrics(tr, te, pd_)
    r_tr, r_va, r_te = random_split(s, len(tr), len(va), len(te))
    pr, bv_r, be_r = run(r_tr, r_va, r_te, s)
    mr = metrics(r_tr, r_te, pr)
    row = {"seed": s, "n_train": len(tr), "n_val": len(va), "n_test": len(te),
           "disjoint": dict(zip(["OA_all", "OA_seen", "AA_seen", "classes_train", "classes_test", "classes_both", "share_test_seen"], md),
                            val_acc=bv_d, best_epoch=be_d),
           "random": dict(zip(["OA_all", "OA_seen", "AA_seen", "classes_train", "classes_test", "classes_both", "share_test_seen"], mr),
                          val_acc=bv_r, best_epoch=be_r)}
    res.append(row); print(json.dumps(row), f"{time.time()-t0:.0f}s", flush=True)
    json.dump({"config": {"block": BS, "train_frac_blocks": FT, "val_frac_blocks": FV, "epochs": EPOCHS, "buffer_chebyshev": 8},
               "runs": res}, open(os.path.join(OUT, "disjoint_experiment.json"), "w"), ensure_ascii=False, indent=1)

for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
fig, ax = plt.subplots(figsize=(8.6, 4.6))
keys = [("OA_all", "OA（全部测试像元）"), ("OA_seen", "OA（只算训练见过的类）"), ("AA_seen", "AA（训练和测试都有的类）")]
x = np.arange(len(keys)); w = 0.36
for j, (mode, lab, col) in enumerate([("random", "随机划分", "#2878d6"), ("disjoint", "空间不相交划分", "#ec6a34")]):
    mean = [np.mean([r[mode][k] for r in res]) * 100 for k, _ in keys]
    sd = [np.std([r[mode][k] for r in res]) * 100 for k, _ in keys]
    b = ax.bar(x + (j - 0.5) * w, mean, w, yerr=sd, capsize=3, label=lab, color=col)
    for xi, m, sdv in zip(x + (j - 0.5) * w, mean, sd): ax.text(xi, m + sdv + 2.0, f"{m:.1f}", ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels([l for _, l in keys]); ax.set_ylim(0, 125); ax.set_ylabel("%")
ax.set_title(f"同一个 2D CNN、同样的训练样本数：随机划分 vs 空间不相交划分（{len(res)} 个种子，误差线=标准差）", fontsize=10)
ax.legend(loc="upper center", ncol=2, frameon=False)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "08-disjoint-bars.png"), dpi=170)
