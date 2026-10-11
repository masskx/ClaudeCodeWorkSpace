#!/usr/bin/env python3
"""五个"代码能跑通，但结果是假的"的例子。全部用随机数据或合成数据，可以直接运行。

依赖：numpy、scikit-learn。 用法：python3 bugs_demo.py
每个例子都对比“报告出来的数字”（错误写法）和“诚实的评估”（正确写法）。前三个例子里标签是随机的，真实准确率应该是 50% 左右。
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupShuffleSplit, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline

REPEAT = 10


def bug1_select_features_before_split():
    """先用全部数据（含标签）挑特征，再做交叉验证。"""
    wrong, right = [], []
    for seed in range(REPEAT):
        rng = np.random.RandomState(seed)
        X, y = rng.randn(100, 5000), rng.randint(0, 2, 100)
        X_sel = SelectKBest(f_classif, k=20).fit_transform(X, y)          # 错：挑特征时已经看过全部标签
        wrong.append(cross_val_score(LogisticRegression(max_iter=1000), X_sel, y, cv=5).mean())
        pipe = make_pipeline(SelectKBest(f_classif, k=20), LogisticRegression(max_iter=1000))
        right.append(cross_val_score(pipe, X, y, cv=5).mean())             # 对：挑特征放进流水线，只用训练折
    return np.mean(wrong), np.mean(right)


def bug2_duplicate_samples():
    """同一个样本出现了多份，随机划分后，训练集和测试集里有同一条数据。"""
    wrong, right = [], []
    for seed in range(REPEAT):
        rng = np.random.RandomState(seed)
        base_X, base_y = rng.randn(200, 20), rng.randint(0, 2, 200)
        X, y = np.repeat(base_X, 5, axis=0), np.repeat(base_y, 5)           # 每条样本重复 5 次
        groups = np.repeat(np.arange(200), 5)
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=seed)   # 错：随机划分
        wrong.append(KNeighborsClassifier(1).fit(Xtr, ytr).score(Xte, yte))
        tr, te = next(GroupShuffleSplit(test_size=0.2, random_state=seed).split(X, y, groups))   # 对：按样本分组划分
        right.append(KNeighborsClassifier(1).fit(X[tr], y[tr]).score(X[te], y[te]))
    return np.mean(wrong), np.mean(right)


def bug3_tune_on_test_set():
    """在测试集上挑最好的配置，再把这个分数当成最终结果。"""
    wrong, right = [], []
    for seed in range(REPEAT):
        rng = np.random.RandomState(seed)
        X, y = rng.randn(300, 10), rng.randint(0, 2, 300)
        Xtr, Xrest, ytr, yrest = train_test_split(X, y, test_size=0.5, random_state=seed)
        Xva, Xte, yva, yte = train_test_split(Xrest, yrest, test_size=0.5, random_state=seed)
        models = [RandomForestClassifier(n_estimators=20, max_depth=d, random_state=r).fit(Xtr, ytr)
                  for d in (2, 4, 8) for r in range(20)]                     # 60 个配置
        wrong.append(max(m.score(Xte, yte) for m in models))                  # 错：用测试集挑最好的，并汇报这个分数
        best = max(models, key=lambda m: m.score(Xva, yva))                    # 对：用验证集挑，测试集只用一次
        right.append(best.score(Xte, yte))
    return np.mean(wrong), np.mean(right)


def bug4_random_split_on_time_series():
    """有时间趋势的数据，用随机划分评估，相当于让模型“偷看”了未来。"""
    rng = np.random.RandomState(0)
    t = np.arange(600)
    y = 0.05 * t + 2 * np.sin(t / 10) + rng.randn(600) * 0.5
    X = t.reshape(-1, 1)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0)         # 错：随机划分
    wrong = r2_score(yte, RandomForestRegressor(random_state=0).fit(Xtr, ytr).predict(Xte))
    cut = int(len(t) * 0.8)                                                            # 对：按时间划分
    right = r2_score(y[cut:], RandomForestRegressor(random_state=0).fit(X[:cut], y[:cut]).predict(X[cut:]))
    return wrong, right


def bug5_report_best_seed():
    """跑了很多个随机种子，只汇报最好的那一个。"""
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=150, n_features=20, n_informative=5, class_sep=0.8, random_state=0)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0)
    scores = np.array([RandomForestClassifier(n_estimators=10, random_state=s).fit(Xtr, ytr).score(Xte, yte)
                       for s in range(20)])
    return scores.max(), scores.mean(), scores.std()


if __name__ == "__main__":
    w, r = bug1_select_features_before_split()
    print("1 先挑特征再划分（随机标签）    报告 %.3f   诚实 %.3f" % (w, r))
    w, r = bug2_duplicate_samples()
    print("2 样本重复（随机标签）          报告 %.3f   诚实 %.3f" % (w, r))
    w, r = bug3_tune_on_test_set()
    print("3 用测试集挑配置（随机标签）    报告 %.3f   诚实 %.3f" % (w, r))
    w, r = bug4_random_split_on_time_series()
    print("4 时间序列随机划分（R²）        报告 %.3f   诚实 %.3f" % (w, r))
    best, mean, std = bug5_report_best_seed()
    print("5 只汇报最好的种子（准确率）    报告 %.3f   诚实 %.3f ± %.3f" % (best, mean, std))
