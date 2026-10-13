#!/usr/bin/env python3
"""H09 实验 B：谱 Transformer 输给 1D CNN，是“数据饥饿”吗？——学习曲线。
用法：python3 exp_transformer_data.py <复跑目录> <输出目录> [epochs=60]
设计：先固定 30% 的有标注像元作测试集、10% 作验证集（分层，种子 42）；剩余 60% 作为“训练池”，
再从训练池里分层抽取约占全部有标注像元 5% / 10% / 30% / 60% 的训练集（嵌套：小的是大的子集；样本数取 256 的整数倍：512 / 1024 / 3072 / 6144，避免末尾小批次）。
模型和训练设置都沿用课程脚本：谱 Transformer（85,200 参数）与 SpectralCNN1D（76,880 参数），
Adam(1e-3, wd 1e-4)，批 256，两个模型用同样的 epoch 数；StandardScaler 只在训练集拟合；取验证集最优 epoch。
（先验证“数据越多，两个模型的差距怎么变”，不做调参。）"""
import sys, os, json, importlib.util, time
import numpy as np
import torch, torch.nn as nn
from scipy.io import loadmat
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUN, OUT = sys.argv[1], sys.argv[2]
EPOCHS = int(sys.argv[3]) if len(sys.argv) > 3 else 60
torch.set_num_threads(4)


def load_mod(name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(RUN, f"scripts/{name}.py"))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


tf = load_mod("train_transformer"); cn = load_mod("train_1d_cnn")
cube = loadmat(os.path.join(RUN, "dataset/Indian_pines_corrected.mat"))["indian_pines_corrected"].astype(np.float32)
gt = loadmat(os.path.join(RUN, "dataset/Indian_pines_gt.mat"))["indian_pines_gt"]
r, c = np.nonzero(gt); X = cube[r, c]; y = gt[r, c] - 1
idx = np.arange(len(y))
pool_idx, te_idx = train_test_split(idx, test_size=0.30, stratify=y, random_state=42)
pool_idx, va_idx = train_test_split(pool_idx, test_size=0.10 / 0.70, stratify=y[pool_idx], random_state=42)
RATES = [0.05, 0.10, 0.30, 0.60]
sub = {}
cur = pool_idx
for rate in sorted(RATES, reverse=True):          # 嵌套子集：从大到小依次抽
    n = int(round(rate * len(y) / 256)) * 256   # 取 256 的整数倍：避免每个 epoch 末尾出现只有 1~5 个样本的小批次（会让训练明显变差）
    if n >= len(cur):
        sub[rate] = cur
    elif len(cur) - n < 16:                       # 剩余不足类别数时无法分层：随机丢掉几个样本
        sub[rate] = np.random.RandomState(42).permutation(cur)[:n]
    else:
        sub[rate], _ = train_test_split(cur, train_size=n, stratify=y[cur], random_state=42)
    cur = sub[rate]


def train_eval(mk, kind, tr, seed=42):
    torch.manual_seed(seed); np.random.seed(seed); model = mk()   # 先设种子再初始化模型，保证可复现
    sc = StandardScaler().fit(X[tr])
    f = lambda ix: torch.from_numpy(sc.transform(X[ix]).astype(np.float32))
    xtr, xva, xte = f(tr), f(va_idx), f(te_idx)
    if kind == "cnn": xtr, xva, xte = xtr.unsqueeze(1), xva.unsqueeze(1), xte.unsqueeze(1)
    ytr = torch.from_numpy(y[tr])
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    best, bs, be = -1, None, 0
    for ep in range(1, EPOCHS + 1):
        model.train(); perm = torch.randperm(len(ytr))
        for i in range(0, len(perm), 256):
            b = perm[i:i + 256]; opt.zero_grad(); nn.functional.cross_entropy(model(xtr[b]), ytr[b]).backward(); opt.step()
        model.eval()
        with torch.no_grad():
            v = float((torch.cat([model(xva[i:i + 512]).argmax(1) for i in range(0, len(xva), 512)]).numpy() == y[va_idx]).mean())
        if v > best: best, bs, be = v, {k: t.clone() for k, t in model.state_dict().items()}, ep
    model.load_state_dict(bs); model.eval()
    with torch.no_grad():
        p = torch.cat([model(xte[i:i + 512]).argmax(1) for i in range(0, len(xte), 512)]).numpy()
    yt = y[te_idx]; rec = [float((p[yt == k] == k).mean()) for k in np.unique(yt)]
    return float((p == yt).mean()), float(np.mean(rec)), best, be


out = {"epochs": EPOCHS, "n_test": int(len(te_idx)), "n_val": int(len(va_idx)), "rows": []}
for rate in RATES:
    tr = sub[rate]
    for name, kind, mk, seeds in [("谱 Transformer", "tf", lambda: tf.SpectralTransformerClassifier(200, 16), (42,)),
                                  ("1D CNN", "cnn", lambda: cn.SpectralCNN1D(200, 16), (42, 43, 44))]:
        t0 = time.time(); rs = [train_eval(mk, kind, tr, sd) for sd in seeds]
        row = {"train_rate": rate, "n_train": int(len(tr)), "model": name, "init_seeds": list(seeds),
               "OA": float(np.mean([r[0] for r in rs])), "AA": float(np.mean([r[1] for r in rs])),
               "OA_sd": float(np.std([r[0] for r in rs], ddof=1)) if len(rs) > 1 else None,
               "AA_sd": float(np.std([r[1] for r in rs], ddof=1)) if len(rs) > 1 else None,
               "OA_each": [float(r[0]) for r in rs], "best_epoch": [r[3] for r in rs], "sec": round(time.time() - t0)}
        out["rows"].append(row); print(json.dumps(row, ensure_ascii=False), flush=True)
        json.dump(out, open(os.path.join(OUT, "transformer_data_curve.json"), "w"), ensure_ascii=False, indent=1)

for f_ in font_manager.findSystemFonts():
    if "wqy" in f_.lower(): font_manager.fontManager.addfont(f_)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for k, (metric, title) in enumerate([("OA", "OA（测试集）"), ("AA", "AA（测试集）")]):
    for name, col in [("谱 Transformer", "#ec6a34"), ("1D CNN", "#2878d6")]:
        rows = [r for r in out["rows"] if r["model"] == name]
        ax[k].errorbar([r["n_train"] for r in rows], [r[metric] * 100 for r in rows], yerr=[(r[metric + "_sd"] or 0) * 100 for r in rows], fmt="o-", color=col, capsize=3, label=name + ("（3 个初始化均值±标准差）" if name == "1D CNN" else "（1 个种子）"))
        for r in rows: ax[k].annotate(f"{r[metric]*100:.1f}", (r["n_train"], r[metric] * 100), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8, color=col)
    ax[k].set_xscale("log"); ax[k].set_xlabel("训练样本数（对数轴）"); ax[k].set_ylabel("%"); ax[k].set_title(title)
    ax[k].legend(frameon=False)
    for s in ("top", "right"): ax[k].spines[s].set_visible(False)
plt.suptitle(f"训练样本越多，Transformer 和 1D CNN 的差距怎么变？（{EPOCHS} epochs，固定测试集 {out['n_test']} 个像元）", fontsize=10)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "09-data-curve.png"), dpi=165)
