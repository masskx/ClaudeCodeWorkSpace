#!/usr/bin/env python3
"""H09 实验 A：注意力聚焦的 75–105 号波段，真的是“分类靠它”吗？——遮挡检验 + 波段判别力。
用法：python3 exp_transformer_checks.py <复跑目录> <输出目录>
前提：复跑目录里已有课程脚本训练出的 results/transformer_120/IP/*.pth（谱 Transformer，120 epochs，协议 C 种子 42）
和 results/1d_cnn_60/IP/*.pth（1D CNN，60 epochs），划分与标准化沿用课程（只在训练像元上拟合）。
做三件事：
 1) 每个波段的 ANOVA F 值（类间差异/类内差异，用训练像元算）——衡量这个波段“判别力”；
 2) 把一组波段在标准化空间里置 0（等于换成训练均值）后，测试集准确率掉多少；
 3) 对照组：随机 31 个波段（20 次）、0–30、140–170、F 值最高的 31 个、最低的 31 个。
遮挡只改测试输入，不重新训练。"""
import sys, os, json, glob, importlib.util
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUN, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(RUN, "src"))
from hsi_learning.data import load_hsi_dataset, split_ground_truth


def load_mod(name):
    sp = importlib.util.spec_from_file_location(name, os.path.join(RUN, f"scripts/{name}.py"))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


cube, gt, names = load_hsi_dataset("IP", dataset_dir=os.path.join(RUN, "dataset"))
tr_gt, va_gt, te_gt = split_ground_truth(gt, train_rate=0.1, val_rate=0.1, random_state=42)


def spectra(m):
    r, c = np.nonzero(m); return cube[r, c].astype(np.float32), (m[r, c] - 1).astype(np.int64)


Xtr, ytr = spectra(tr_gt); Xte, yte = spectra(te_gt)
sc = StandardScaler().fit(Xtr)
Ztr, Zte = sc.transform(Xtr).astype(np.float32), sc.transform(Xte).astype(np.float32)

# 1) ANOVA F per band (training pixels)
cls = np.unique(ytr); gm = Ztr.mean(0)
ssb = sum((ytr == k).sum() * (Ztr[ytr == k].mean(0) - gm) ** 2 for k in cls)
ssw = sum(((Ztr[ytr == k] - Ztr[ytr == k].mean(0)) ** 2).sum(0) for k in cls)
F = (ssb / (len(cls) - 1)) / (ssw / (len(ytr) - len(cls)))

tf = load_mod("train_transformer"); cn = load_mod("train_1d_cnn")
m_tf = tf.SpectralTransformerClassifier(200, 16); m_cn = cn.SpectralCNN1D(200, 16)
for m, pat in [(m_tf, "results/transformer_120/IP/epoch_*.pth"), (m_cn, "results/1d_cnn_60/IP/epoch_*.pth")]:
    ck = sorted(glob.glob(os.path.join(RUN, pat)))[-1]; m.load_state_dict(torch.load(ck, map_location="cpu")); m.eval()


@torch.no_grad()
def acc(model, Z, kind):
    X = torch.from_numpy(Z)
    if kind == "cnn": X = X.unsqueeze(1)
    p = np.concatenate([model(X[i:i + 512]).argmax(1).numpy() for i in range(0, len(X), 512)])
    return float((p == yte).mean())


def masked(idx):
    Z = Zte.copy(); Z[:, idx] = 0.0; return Z


order = np.argsort(F)
sets = {"不遮挡": [], "注意力区 75–105": list(range(75, 106)), "前段 0–30": list(range(0, 31)),
        "后段 140–170": list(range(140, 171)), "F 值最高的 31 个波段": list(order[-31:]),
        "F 值最低的 31 个波段": list(order[:31])}
res = {}
rng = np.random.default_rng(0)
rand = [sorted(rng.choice(200, 31, replace=False).tolist()) for _ in range(20)]
for kind, model, key in [("tf", m_tf, "Transformer"), ("cnn", m_cn, "1D CNN")]:
    r = {k: acc(model, masked(v) if v else Zte, kind) for k, v in sets.items()}
    ra = [acc(model, masked(ix), kind) for ix in rand]
    r["随机 31 个波段（20 次均值）"] = float(np.mean(ra)); r["随机 31 个波段（最小/最大）"] = [float(min(ra)), float(max(ra))]
    res[key] = r
top = int(np.argmax(F))
info = {"F_mean_75_105": float(F[75:106].mean()), "F_mean_all": float(F.mean()), "F_median_all": float(np.median(F)),
        "F_rank_of_75_105_mean_among_random31": float(np.mean([F[ix].mean() < F[75:106].mean() for ix in rand])),
        "top_band": top, "top31_bands_sorted": sorted(int(i) for i in order[-31:]),
        "bottom31_bands_sorted": sorted(int(i) for i in order[:31]),
        "n_test": int(len(yte)), "results": res}
json.dump(info, open(os.path.join(OUT, "attention_occlusion.json"), "w"), ensure_ascii=False, indent=1)

for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 4.6), gridspec_kw={"width_ratios": [1.1, 1]})
a1.plot(np.arange(200), F, color="#2878d6", lw=1.3)
a1.axvspan(75, 105, color="#ec6a34", alpha=0.25, label="注意力聚焦的 75–105")
a1.set_yscale("log"); a1.set_xlabel("波段序号（不是波长）"); a1.set_ylabel("ANOVA F 值（类间/类内，对数轴）")
a1.set_title("每个波段的判别力（训练像元）"); a1.legend(frameon=False)
labs = ["不遮挡", "注意力区 75–105", "前段 0–30", "后段 140–170", "F 值最高的 31 个波段", "F 值最低的 31 个波段", "随机 31 个波段（20 次均值）"]
x = np.arange(len(labs)); w = 0.38
for j, (k, col) in enumerate([("Transformer", "#ec6a34"), ("1D CNN", "#2878d6")]):
    a2.bar(x + (j - 0.5) * w, [res[k][l] * 100 for l in labs], w, color=col, label=k)
a2.set_xticks(x); a2.set_xticklabels([l.replace("（", "\n（") for l in labs], rotation=35, ha="right", fontsize=8)
a2.set_ylabel("测试集 OA（%）"); a2.set_title("遮挡 31 个波段后的准确率（不重新训练）"); a2.legend(frameon=False)
for s in ("top", "right"):
    a1.spines[s].set_visible(False); a2.spines[s].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "09-attention-occlusion.png"), dpi=165)
print(json.dumps({k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in res.items()}, ensure_ascii=False))
print({k: info[k] for k in ("F_mean_75_105", "F_mean_all", "F_median_all", "F_rank_of_75_105_mean_among_random31", "top_band")})
