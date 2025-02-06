# _*_coding:utf-8_*_

import torch

# 查看 PyTorch 版本
print(torch.__version__)

# 查看 PyTorch 关联的 CUDA 版本（若安装的是 GPU 版）
print(torch.version.cuda)

# 检查 CUDA 是否可用
print(torch.cuda.is_available())