# 高光谱图像分类系列（跟着 HSI-Learning 课程走）

> 项目：`WeChat Official Account/高光谱系列/`（公众号文章系列，中文）。本 README 用英文写，文章用中文。

A 12-article Chinese WeChat series that walks through the open course
[masskx/HSI-Learning](https://github.com/masskx/HSI-Learning) (hyperspectral image classification, from data
fundamentals to writing a first paper). The brief: explain **every result and every figure** clearly, and introduce
the **datasets** properly. Each article reads its figures one by one ("how to read it / what you can see / what it
means / what you cannot conclude"), and wherever feasible the numbers were **re-run locally** instead of copied.

## Articles

| # | Folder | Course chapters | What is original here |
|---|---|---|---|
| H01 | `H01-高光谱图像是什么…` | ch01 | class counts re-counted from the `.mat` files |
| H02 | `H02-三个数据集一次看懂…` | dataset README | **dataset introduction**: 4 new figures + `dataset_stats.json` generated from the data |
| H03 | `H03-评价别翻车…` | ch02 | experiment: random vs 10×10 block split (SVM) |
| H04 | `H04-传统机器学习基线…` | ch03 | re-run of SVM/RF/KNN/LR/PCA; experiment: gamma × feature scale |
| H05 | `H05-从像素到Patch…` | ch04 | label-only purity numbers (0.89/0.67/0.42) |
| H06 | `H06-三种卷积…` | ch05–07 | re-run of 1D/2D/3D CNN (6 runs); params/MACs counted; per-class recall figure |
| H07 | `H07-HybridSN与SSRN…` | ch08–09 | re-run of HybridSN and SSRN; params/MACs counted |
| H08 | `H08-空间不相交划分实验…` | ch06 §6.4, ch08 | **new experiment**: spatially disjoint split with a leakage buffer (2D CNN and SVM, 3 seeds) |
| H09 | `H09-注意力与Transformer…` | ch10 | re-run of the Transformer; occlusion check of the attention claim; data-size learning curve |
| H10 | `H10-实战补遗…` | ch15 | 9-run loss ablation (3 losses × 3 seeds); bucket sizes; t-SNE/bucket figures re-generated |
| H11 | `H11-小样本与开集…` | ch16–17 | re-runs of the ProtoNet and open-set scripts |
| H12 | `H12-科研篇与收官…` | ch11–14 + classroom revision | pre-registered mini-capstone (HybridSN global-pooling variant, 3 seeds) |

Each article folder holds `article.md` (with front matter), `imgs/` (figures + raw result JSON), and
`发布备忘.md` (publishing memo: what is real, what was not verified, cover-image prompt). Cover images
(`imgs/cover.png`) are **not** generated; the prompt is in each memo, per the project's image rules.

## Tools (`_工具/`)

| Script | Used by | Produces |
|---|---|---|
| `make_dataset_figs.py` | H02 | 4 dataset figures + `dataset_stats.json` |
| `exp_split_leakage.py` | H03 | random vs block split (SVM) |
| `exp_svm_gamma_scale.py` | H04 | gamma grid, raw vs standardized |
| `collect_cnn_results.py` | H06 | per-class recall figure, re-run vs course table |
| `exp_disjoint_cnn.py`, `exp_disjoint_svm.py`, `exp_disjoint_viz.py` | H08 | disjoint-split experiment and figures |
| `exp_transformer_checks.py`, `exp_transformer_data.py` | H09 | occlusion check, learning curve |
| `collect_loss_ablation.py` | H10 | loss ablation summary figure |
| `exp_hybridsn_gap.py` | H12 | HybridSN with global average pooling (wraps the course `train_hybridsn.py`) |

All scripts take explicit input/output paths. The training scripts of the course were run **unmodified** from a local
clone (CPU only, PyTorch 2.14, Python 3.13); the tools above only wrap or post-process them.

## How numbers were verified (and what that does and does not mean)

- **Only GitHub and PyPI were reachable** from the writing environment. Anything about papers, datasets' home pages,
  or other websites was *not* checked against the source; the articles say so.
- **Re-run** = same course script, same seed, same split, on CPU. Re-runs matched the course within ~0.1–0.6 points
  for OA (SVM/RF/KNN exactly); rare-class recalls (Alfalfa, Grass-pasture-mowed, Oats) vary a lot between
  environments, which the articles use as a teaching point rather than hiding it.
- **Original experiments** (H03, H04, H08, H09, H12) are small (≤ 3 seeds, one dataset, one configuration). They are
  presented as illustrations with explicit limits, not as general findings.
- Simulated images follow the project's rules: nothing here fakes a commercial UI; no figure presents simulated data
  as real. All plots are generated from real runs or from the course's own figures.

## Inconsistencies found in the course material

Listed so the course author can fix them, and so readers who open the course side by side are not confused. Items
marked † are already acknowledged in the course's own `docs/teaching/errata.md`; the rest I did not find there.

| # | Where | What | Article |
|---|---|---|---|
| 1 | ch02 text | Oats' wrong prediction target written as Stone-Steel-Towers; the matrix shows class 15 (Buildings-Grass-Trees-Drives) | H03 |
| 2 | ch02 text | the 39-count Corn-mintill → Soybean-mintill confusion is omitted from the list of examples | H03 |
| 3 | ch01 / ch05 | band index converted to nm / read as "red edge" although the dataset README says the index is not linear wavelength † | H01, H06, H09 |
| 4 | ch03 | logistic-regression numbers are not reproducible across environments (non-converged lbfgs) | H04 |
| 5 | ch06 fig 6-1 | receptive field drawn as 3→7→11 (no pooling); the network gives 3→4→8→12; the text was corrected, the figure and caption were not † (text only) | H06 |
| 6 | ch07 text | Oats' second error target written as Stone-Steel-Towers; matrix and re-run show class 15 | H06 |
| 7 | ch09 fig 9-1 | spectral length drawn as 98 / kernel (1,1,98); the table and the code give 97 | H07 |
| 8 | ch15 fig 15-2 | x-axis labels attach the *sorted* class sizes to class names in *index* order; the claim "rare classes on the left" does not hold | H10 |
| 9 | ch10 | attention peak over bands 75–105 read as NIR/red edge without wavelength metadata † | H09 |

## Status

Drafts complete for the articles listed above; nothing has been published. Everything that needs the owner's
decision (cover images, publishing, whether to forward the inconsistencies to the course author) is listed in the
per-article memos.
