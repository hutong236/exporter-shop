#!/usr/bin/env bash
set -euo pipefail

# PR 检查入口：装依赖 + 清单校验 + 防漂移
# validate.py 内置 docgen 渲染比对，已覆盖生成文档与 exporters/ 源目录的防漂移。
python3 -m pip install --quiet pyyaml
python3 scripts/validate.py
