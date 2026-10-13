#!/usr/bin/env python3
"""H11 对照实验：课程的 ProtoNet 成绩里，“元训练”到底贡献了多少？
用法：python3 exp_protonet_controls.py <复跑目录> <输出目录>
发现：课程脚本的验证准确率在第 1 个 episode（几乎没训练）时最高，之后一直更低，所以最终被选中的 checkpoint 是第 1 步。
本脚本用课程保存的同一批 30 个测试 episode（split.npz），在同样的原型分类规则（负平方欧氏距离）下比较：
  A) 课程选中的 checkpoint；
  B) 同样结构、没有训练的随机初始化 encoder（10 个不同的初始化）；
  C) 不用任何网络：只用 PCA-12+标准化后的中心像元特征；
  D) 不用任何网络：把 9×9×12 的 patch 拉平成 972 维特征。
K = 1 / 5 / 10 的支持样本，与课程用法一致（每类前 K 个为支持集，query 每类 5 个）。"""
import sys, os, json
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

RUN, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(RUN, "src"))
os.chdir(RUN)
from hsi_learning import teaching_runs as T
from hsi_learning.teaching import PatchEncoder, patches_at

model, cube, gt, names, split, cfg = T.load_bundle(os.path.join(RUN, "results/protonet"))
labels = gt.ravel()
ep_classes, ep_sup, ep_qry = split["episode_classes"], split["episode_support"], split["episode_query"]
N = len(ep_classes)


def label_of(ids, classes):
    return np.array([int(np.where(classes == labels[i])[0][0]) for i in ids])


def run(feat_fn):
    out = {}
    for K in (1, 5, 10):
        accs = []
        for e in range(N):
            sup = ep_sup[e].reshape(5, 10)[:, :K].ravel()
            sy = torch.as_tensor(np.repeat(np.arange(5), K)); qy = torch.as_tensor(label_of(ep_qry[e], ep_classes[e]))
            sf, qf = feat_fn(sup), feat_fn(ep_qry[e])
            protos = torch.stack([sf[sy == k].mean(0) for k in range(5)])
            pred = (-torch.cdist(qf, protos) ** 2).argmax(1)
            accs.append(float((pred == qy).float().mean()))
        out[K] = accs
    return out


@torch.no_grad()
def enc_feat(m):
    m.eval()
    return lambda ids: m(patches_at(cube, ids, 9))


res = {}
res["A 课程选中的 checkpoint（第 1 步）"] = run(enc_feat(model))
rand = []
for s in range(10):
    torch.manual_seed(1000 + s); rand.append(run(enc_feat(PatchEncoder(12))))
res["B 随机初始化 encoder（10 次均值）"] = {K: [float(np.mean([r[K][e] for r in rand])) for e in range(N)] for K in (1, 5, 10)}
rand_means = {K: [float(np.mean(r[K])) for r in rand] for K in (1, 5, 10)}
cube_t = torch.as_tensor(cube) if not torch.is_tensor(cube) else cube
res["C 中心像元 PCA-12（无网络）"] = run(lambda ids: patches_at(cube, ids, 1).flatten(1) if False else torch.as_tensor(np.asarray(cube).reshape(-1, np.asarray(cube).shape[-1])[ids]).float())
res["D 9×9×12 patch 拉平（无网络）"] = run(lambda ids: patches_at(cube, ids, 9).flatten(1))
summary = {"n_episodes": N, "mean": {k: {str(K): float(np.mean(v[K])) for K in v} for k, v in res.items()},
           "random_init_means_per_init": {str(K): v for K, v in rand_means.items()}, "chance": 0.2}
json.dump(summary, open(os.path.join(OUT, "protonet_controls.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps(summary["mean"], ensure_ascii=False, indent=1))
print({K: (round(float(np.mean(v)) * 100, 1), round(float(np.std(v)) * 100, 1), round(min(v) * 100, 1), round(max(v) * 100, 1)) for K, v in rand_means.items()})

for f in font_manager.findSystemFonts():
    if "wqy" in f.lower(): font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["WenQuanYi Zen Hei", "DejaVu Sans"], "axes.unicode_minus": False})
fig, ax = plt.subplots(figsize=(10, 4.6))
x = np.arange(3); keys = list(res); w = 0.2; cols = ["#ec6a34", "#2878d6", "#1aa97b", "#9a9a9a"]
for j, k in enumerate(keys):
    m = [np.mean(res[k][K]) * 100 for K in (1, 5, 10)]
    ax.bar(x + (j - 1.5) * w, m, w, color=cols[j], label=k)
    for xi, mm in zip(x + (j - 1.5) * w, m): ax.text(xi, mm + 1, f"{mm:.1f}", ha="center", fontsize=8)
ax.axhline(20, ls="--", color="#999", lw=1); ax.text(2.45, 21.5, "随机猜 = 20%", ha="right", fontsize=8, color="#666")
ax.set_xticks(x); ax.set_xticklabels(["1-shot", "5-shot", "10-shot"]); ax.set_ylim(0, 112); ax.set_ylabel("5 类任务的准确率（%，30 个 episode 平均）")
ax.set_title("同一批测试任务、同样的最近原型规则：元训练的 encoder 比“不训练”强多少？", fontsize=10)
ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(OUT, "11-protonet-controls.png"), dpi=165)
