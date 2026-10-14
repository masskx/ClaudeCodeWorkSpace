#!/usr/bin/env python3
"""H11：开集结果的“地图”和错误类型图（用课程 train_openset.py 的种子 42 输出）。
用法：python3 exp_openset_maps.py <复跑目录> <输出目录>
读取 results/openset/{split.npz,predictions.npz,run_config.json}。只画测试集像元（训练/验证像元和背景不参与评估，用浅灰/黑表示）。
预测里编号 17 = 拒识（课程里的 unknown_id）。错误类型按课程 ch17 的五项指标划分。"""
import sys, os, json
import numpy as np
from scipy.io import loadmat
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
gt = loadmat(os.path.join(RUN, "dataset/Indian_pines_gt.mat"))["indian_pines_gt"]
H, W = gt.shape
sp = np.load(os.path.join(RUN, "results/openset/split.npz")); pr = np.load(os.path.join(RUN, "results/openset/predictions.npz"))
cfg = json.load(open(os.path.join(RUN, "results/openset/run_config.json")))
UNK = cfg["unknown_id"]; unknown_classes = set(cfg["unknown_classes"])
ids = sp["test_ids"]; r, c = np.unravel_index(ids, (H, W))
true_raw = gt[r, c]
assert np.all(np.isin(true_raw, range(1, 17)))
is_unk = np.isin(true_raw, list(unknown_classes))

base_cmap = plt.get_cmap("nipy_spectral")


def class_img(vals, mask_unknown_white=True):
    img = np.full((H, W, 3), 0.86)           # 浅灰：有标注但不在测试集
    img[gt == 0] = 0.0                       # 黑：未标注背景
    for (rr, cc, v) in zip(r, c, vals):
        img[rr, cc] = (1, 1, 1) if v == UNK else base_cmap((v - 1) / 16.0)[:3]
    return img


true_open = np.where(is_unk, UNK, true_raw)
panels = [("开集真值（白色 = 未知类 1、7、9、16）", class_img(true_open)),
          ("距离法：预测（白色 = 拒识）", class_img(pr["distance_prediction"])),
          ("MSP 法：预测（白色 = 拒识）", class_img(pr["msp_prediction"]))]


def error_img(pred):
    # 0 灰(不在测试) 1 已知且正确接受 2 已知误拒 3 已知错分(接受但分错) 4 未知被拒识(正确) 5 未知漏检(被分成已知)
    code = np.zeros(len(ids), int)
    rej = pred == UNK
    code[(~is_unk) & (~rej) & (pred == true_raw)] = 1
    code[(~is_unk) & rej] = 2
    code[(~is_unk) & (~rej) & (pred != true_raw)] = 3
    code[is_unk & rej] = 4
    code[is_unk & (~rej)] = 5
    img = np.zeros((H, W), int); img[gt > 0] = 0
    lab = np.full((H, W), -1); lab[gt > 0] = 0
    lab[r, c] = code
    return lab, np.bincount(code, minlength=6)


cols = ["#dddddd", "#c9e4c5", "#f4a261", "#d62828", "#2878d6", "#6a0572"]
cm_err = ListedColormap(["#000000"] + cols)
res = {}
for name, key in [("距离法", "distance_prediction"), ("MSP 法", "msp_prediction")]:
    lab, cnt = error_img(pr[key]); res[name] = {"已知正确接受": int(cnt[1]), "已知误拒": int(cnt[2]), "已知错分": int(cnt[3]),
                                                "未知被拒识": int(cnt[4]), "未知漏检": int(cnt[5]), "测试像元总数": int(len(ids))}
    panels.append((f"{name}：错误类型图", (lab + 1, cm_err)))
fig, axes = plt.subplots(2, 3, figsize=(15, 10.2))
for ax, (title, im) in zip(axes.ravel(), panels):
    if isinstance(im, tuple): ax.imshow(im[0], cmap=im[1], vmin=0, vmax=6, interpolation="nearest")
    else: ax.imshow(im, interpolation="nearest")
    ax.set_title(title, fontsize=11); ax.set_xticks([]); ax.set_yticks([])
ax = axes[1, 2]; ax.axis("off")
ax.legend(handles=[Patch(color="#dddddd", label="标注像元但不在测试集"), Patch(color="#c9e4c5", label="已知类：正确接受"),
                   Patch(color="#f4a261", label="已知类：被误拒"), Patch(color="#d62828", label="已知类：接受但分错"),
                   Patch(color="#2878d6", label="未知类：被拒识（正确）"), Patch(color="#6a0572", label="未知类：漏检（被当成已知类）"),
                   Patch(color="#000000", label="未标注背景")], loc="center", frameon=False, fontsize=11)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "11-openset-maps.png"), dpi=150)
json.dump(res, open(os.path.join(OUT, "openset_error_counts.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False))
