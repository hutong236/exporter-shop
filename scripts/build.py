#!/usr/bin/env python3
"""聚合 exporters/*/exporter.yaml 为根 exporter-types.yaml。

- 源文件（唯一维护入口）：exporters/<name>/exporter.yaml，每文件一个 `types:` 单条目，
  与平台 registry.ParseTypesFile 格式一致。
- 输出：根 exporter-types.yaml（平台单文件模式的消费路径，生成产物，请勿手改）。
- 合并顺序：文件路径字典序 —— 与平台目录模式（gitstore.go，Trees API 字典序逐文件
  拉取合并）语义一致，两种接入方式看到的清单完全相同。
- 纯文本拼接（不经 YAML 重排），条目内容逐字节保留源文件写法。

用法：
    python3 scripts/build.py            # 生成根清单
    python3 scripts/build.py --check    # 仅校验根清单与源目录一致（CI 用，漂移即退出码 1）
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "exporters"
OUT_FILE = REPO / "exporter-types.yaml"

# 目录模式平台侧限制（gitstore.go）：MaxTypesFiles=64 / MaxTotalTypesBytes=768KiB。
MAX_FILES = 64
MAX_TOTAL_BYTES = 768 * 1024

GENERATED_HEADER = """\
# Exporter 商店标准清单（hutong-project-monitor 平台 Git 源消费）
#
# ⚠️ 本文件由 scripts/build.py 从 exporters/*/exporter.yaml 自动聚合生成，请勿手改。
#    修改请编辑对应类型的 exporters/<name>/exporter.yaml 后重新生成。
#
# 格式与校验权威定义见平台仓库 backend/internal/console/registry/registry.go（TypeDef schema）。
# 平台拉取本文件（默认约定：仓库 main 分支根路径 exporter-types.yaml），或把商店"文件路径"
# 设为 exporters 走目录模式（Trees API 按字典序逐文件合并，与本聚合产物等价）。拉取后与内置
# 类型走完全相同的加载期校验，任一条目非法将整份拒绝并保留 last-good。
#
# 关键约束：
#   - sensitive: true 必须 kind: password，且落点（to）只允许 env 或 config，禁止进 args
#   - target_mode: connection（连接型多目标）必须搭配 config.mode=raw + config.secret_mount=true + 非空 template
#   - 探针型由 probe 声明；name 须为 ^[a-z][a-z0-9_]*$
#   - 同 key 条目整体覆盖平台内置定义（优先级 内置 < Git < 页面新增）
#
# 源清单最初由平台仓库 registry.Defaults() 忠实导出（2026-09-26，16 个市场类），
# 2026-09-27 起拆分维护于 exporters/ 目录，本文件为聚合产物。
"""

ENTRY_RE = re.compile(r"^    - name: [a-z][a-z0-9_]*\s*$")


def collect() -> tuple[str, int]:
    files = sorted(SRC_DIR.glob("*/exporter.yaml"))
    if not files:
        sys.exit(f"错误：{SRC_DIR} 下未发现 */exporter.yaml 源文件")
    if len(files) > MAX_FILES:
        sys.exit(f"错误：源文件数 {len(files)} 超过平台目录模式上限 {MAX_FILES}")

    blocks, total = [], 0
    for f in files:
        text = f.read_text()
        lines = text.splitlines(keepends=True)
        # 跳过文件头注释与空行，定位 types: 行；其后即条目区（逐字保留）。
        try:
            t_idx = next(i for i, l in enumerate(lines) if l.rstrip("\n") == "types:")
        except StopIteration:
            sys.exit(f"错误：{f} 缺少 types: 行")
        block_lines = [l for l in lines[t_idx + 1:] if l.strip()]
        if not block_lines or not ENTRY_RE.match(block_lines[0]):
            sys.exit(f"错误：{f} types: 后缺少 4 空格缩进的 '- name:' 条目")
        block = "".join(block_lines)
        total += len(block.encode())
        blocks.append((f, block))
    if total > MAX_TOTAL_BYTES:
        sys.exit(f"错误：合并总字节 {total} 超过平台目录模式上限 {MAX_TOTAL_BYTES}")

    names = [b.splitlines()[0].strip() for _, b in blocks]
    seen = set()
    for n in names:
        key = n.split("name: ")[1]
        if key in seen:
            sys.exit(f"错误：类型 {key} 跨文件重复")
        seen.add(key)

    out = GENERATED_HEADER + "types:\n" + "\n".join(b for _, b in blocks)
    if not out.endswith("\n"):
        out += "\n"
    return out, len(blocks)


def main() -> None:
    out, count = collect()
    if "--check" in sys.argv:
        current = OUT_FILE.read_text() if OUT_FILE.exists() else ""
        if current != out:
            sys.exit("错误：exporter-types.yaml 与 exporters/ 源目录不一致，请运行 python3 scripts/build.py")
        print(f"OK：根清单与源目录一致（{len(out)} 字节，{count} 个条目）")
        return
    OUT_FILE.write_text(out)
    print(f"已生成 {OUT_FILE.relative_to(REPO)}（{len(out)} 字节，{count} 个条目）")


if __name__ == "__main__":
    main()
