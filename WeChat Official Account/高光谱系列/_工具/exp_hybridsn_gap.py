#!/usr/bin/env python3
"""H12 迷你 Capstone：HybridSN 轻量化——用全局平均池化替代 flatten（课程第 14 章示例选题 2）。
用法：python3 exp_hybridsn_gap.py <复跑目录> <课程 train_hybridsn.py 的全部参数……>
例：python3 exp_hybridsn_gap.py /tmp/repro/hsi --train-rate 0.1 --val-rate 0.1 --seed 42 --epochs 40 --eval-interval 1 --output-dir results/hybridsn_gap_s42
做法：把课程 HybridSN 的 conv4 之后的“拉平→Linear(18496→256)”换成“AdaptiveAvgPool2d(1)→Linear(64→256)”，
其余层、预处理、划分、优化器、训练循环（课程的 scripts/train_hybridsn.py 本身）一行不改。
只替换模型类，所以与基线是严格的一次一变量对照。"""
import sys, os, importlib.util
import torch, torch.nn as nn

RUN = sys.argv[1]
sys.path.insert(0, os.path.join(RUN, "src"))
import hsi_learning.models as M
from hsi_learning.models.hybridsn import HybridSN


class HybridSNGAP(HybridSN):
    """与 HybridSN 完全相同，只是 conv4 之后用全局平均池化代替拉平。"""

    def __init__(self, input_channels: int, patch_size: int, num_classes: int):
        super().__init__(input_channels, patch_size, num_classes)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.dense1 = nn.Sequential(nn.Linear(64, 256), nn.ReLU(inplace=True), nn.Dropout(p=0.4))

    def forward(self, inputs):
        f = inputs.unsqueeze(1)
        f = self.conv3(self.conv2(self.conv1(f)))
        f = f.view(f.shape[0], f.shape[1] * f.shape[2], f.shape[3], f.shape[4])
        f = self.pool(self.conv4(f)).flatten(1)
        return self.dense3(self.dense2(self.dense1(f)))


M.HybridSN = HybridSNGAP
print("HybridSNGAP params:", sum(p.numel() for p in HybridSNGAP(15, 25, 16).parameters()), flush=True)
sp = importlib.util.spec_from_file_location("train_hybridsn", os.path.join(RUN, "scripts/train_hybridsn.py"))
mod = importlib.util.module_from_spec(sp); sp.loader.exec_module(mod)
sys.argv = ["train_hybridsn.py"] + sys.argv[2:]
sys.exit(mod.main())
