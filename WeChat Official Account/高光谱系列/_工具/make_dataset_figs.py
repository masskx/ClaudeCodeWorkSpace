#!/usr/bin/env python3
"""用 HSI-Learning 仓库里的三份 .mat 数据，重新生成"数据集介绍"一文用到的图和统计。
用法：python3 make_dataset_figs.py <HSI-Learning 仓库路径> <输出目录>
需要 numpy、scipy、matplotlib。所有数字都是从 .mat 文件里实际读出来的，不是抄的。"""
import sys, json, os
import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

REPO, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
for f in font_manager.findSystemFonts():
    if "wqy" in f.lower() or "zenhei" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
INK, MUTE, GRID = "#0b0b0b", "#52514e", "#e6e4de"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"

SPEC = {
 "IP": dict(f="Indian_pines_corrected.mat", k="indian_pines_corrected", g="Indian_pines_gt.mat", gk="indian_pines_gt",
            title="Indian Pines（IP）", rgb=(60, 30, 10), res=20.0,
            names=["Alfalfa","Corn-notill","Corn-mintill","Corn","Grass-pasture","Grass-trees","Grass-pasture-mowed","Hay-windrowed","Oats","Soybean-notill","Soybean-mintill","Soybean-clean","Wheat","Woods","Buildings-Grass-Trees-Drives","Stone-Steel-Towers"]),
 "SA": dict(f="Salinas_corrected.mat", k="salinas_corrected", g="Salinas_gt.mat", gk="salinas_gt",
            title="Salinas（SA）", rgb=(40, 20, 8), res=3.7,
            names=["Brocoli_green_weeds_1","Brocoli_green_weeds_2","Fallow","Fallow_rough_plow","Fallow_smooth","Stubble","Celery","Grapes_untrained","Soil_vinyard_develop","Corn_senesced_green","Lettuce_romaine_4wk","Lettuce_romaine_5wk","Lettuce_romaine_6wk","Lettuce_romaine_7wk","Vinyard_untrained","Vinyard_vertical"]),
 "PU": dict(f="PaviaU.mat", k="paviaU", g="PaviaU_gt.mat", gk="paviaU_gt",
            title="Pavia University（PU）", rgb=(55, 41, 12), res=1.3,
            names=["Asphalt","Meadows","Gravel","Trees","Painted metal sheets","Bare Soil","Bitumen","Self-Blocking Bricks","Shadows"]),
}
D = {}
for code, s in SPEC.items():
    cube = loadmat(os.path.join(REPO, "dataset", s["f"]))[s["k"]]
    gt = loadmat(os.path.join(REPO, "dataset", s["g"]))[s["gk"]]
    D[code] = (cube, gt)

def stretch(a, lo=2, hi=98):
    l, h = np.percentile(a, [lo, hi]); return np.clip((a - l) / (h - l), 0, 1)

# ---------- 统计表 ----------
stats = {}
for code, (cube, gt) in D.items():
    cnt = np.bincount(gt.ravel())[1:]
    stats[code] = dict(shape=list(cube.shape), dtype=str(cube.dtype), vmin=int(cube.min()), vmax=int(cube.max()),
                       pixels=int(gt.size), labeled=int((gt > 0).sum()), classes=int(len(cnt)),
                       cmax=int(cnt.max()), cmin=int(cnt.min()), ratio=round(float(cnt.max() / cnt.min()), 1),
                       counts=cnt.tolist())
json.dump(stats, open(os.path.join(OUT, "dataset_stats.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: {x: v for x, v in d.items() if x != "counts"} for k, d in stats.items()}, ensure_ascii=False))

# ---------- 图 1：伪彩色 + 标签图 ----------
cmap = plt.get_cmap("nipy_spectral")
fig, axes = plt.subplots(3, 2, figsize=(9.5, 15), constrained_layout=True,
                         gridspec_kw={"height_ratios": [145, 512, 610]})
for row, (code, s) in zip(axes, SPEC.items()):
    cube, gt = D[code]
    r, g_, b = s["rgb"]
    rgb = np.stack([stretch(cube[:, :, r]), stretch(cube[:, :, g_]), stretch(cube[:, :, b])], 2)
    row[0].imshow(rgb); row[0].set_title(f"{s['title']}  伪彩色（波段 {r}/{g_}/{b}）", fontsize=11)
    n = int(gt.max())
    row[1].imshow(np.ma.masked_equal(gt, 0), cmap=cmap, vmin=0, vmax=n, interpolation="nearest")
    row[1].set_facecolor("black"); row[1].set_title(f"标签图（黑色 = 0 = 未标注，共 {n} 类）", fontsize=11)
    for ax in row: ax.set_xticks([]); ax.set_yticks([])
fig.savefig(os.path.join(OUT, "01-maps-three-datasets.png"), dpi=130)
plt.close(fig)

# ---------- 图 2：真实地面尺度 ----------
fig, ax = plt.subplots(figsize=(9, 5.2), constrained_layout=True)
x0 = 0
cols = {"IP": BLUE, "SA": ORANGE, "PU": AQUA}
for code, s in SPEC.items():
    h, w, b = D[code][0].shape
    W, H = w * s["res"], h * s["res"]
    ax.add_patch(plt.Rectangle((x0, 0), W, H, color=cols[code], alpha=0.85))
    ax.text(x0 + W / 2, H + 80, f"{s['title']}\n{h}×{w} 像元 × {s['res']} m\n≈ {W/1000:.2f} × {H/1000:.2f} km", ha="center", va="bottom", fontsize=10.5, color=INK)
    x0 += W + 400
ax.set_xlim(-200, x0); ax.set_ylim(-200, 3900); ax.set_aspect("equal")
ax.set_xlabel("东西向（米）"); ax.set_ylabel("南北向（米）")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.set_title("三个数据集在地面上的真实大小（按像元数 × 空间分辨率换算）", fontsize=12)
fig.savefig(os.path.join(OUT, "02-ground-scale.png"), dpi=140); plt.close(fig)

# ---------- 图 3：类别分布 ----------
fig, axes = plt.subplots(1, 3, figsize=(14, 5.4), constrained_layout=True, gridspec_kw={"width_ratios": [16, 16, 9]})
for ax, (code, s) in zip(axes, SPEC.items()):
    cnt = np.array(stats[code]["counts"]); order = np.argsort(cnt)
    ax.barh(np.arange(len(cnt)), cnt[order], color=cols[code], height=0.7)
    ax.set_yticks(np.arange(len(cnt))); ax.set_yticklabels([s["names"][i] for i in order], fontsize=8.5)
    for i, v in enumerate(cnt[order]): ax.text(v, i, f" {v}", va="center", fontsize=8, color=MUTE)
    ax.set_title(f"{s['title']}\n最大 {cnt.max()} / 最小 {cnt.min()} = {cnt.max()/cnt.min():.1f} 倍", fontsize=10.5)
    ax.set_xlim(0, cnt.max() * 1.18)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.grid(axis="x", color=GRID); ax.set_axisbelow(True)
fig.savefig(os.path.join(OUT, "03-class-distribution.png"), dpi=130); plt.close(fig)

# ---------- 图 4：平均光谱（SA、PU）----------
fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), constrained_layout=True)
picks = {"SA": [0, 6, 8, 13, 7], "PU": [0, 1, 3, 4, 8]}
cs = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA]
for ax, code in zip(axes, ["SA", "PU"]):
    cube, gt = D[code]; s = SPEC[code]
    for c in range(gt.max()):
        m = cube[gt == c + 1].astype(float).mean(0)
        ax.plot(m, color="#d6d4cc", lw=1)
    for c, col in zip(picks[code], cs):
        m = cube[gt == c + 1].astype(float).mean(0)
        ax.plot(m, color=col, lw=2.2, label=s["names"][c])
    ax.set_title(f"{s['title']}：各类平均光谱（彩色为 5 个代表类别）", fontsize=11)
    ax.set_xlabel(f"波段序号（0–{cube.shape[2]-1}）"); ax.set_ylabel("平均光谱响应（原始数值）")
    ax.legend(fontsize=8.5, frameon=False)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.grid(axis="y", color=GRID); ax.set_axisbelow(True)
fig.savefig(os.path.join(OUT, "04-mean-spectra-sa-pu.png"), dpi=130); plt.close(fig)
print("ok")
