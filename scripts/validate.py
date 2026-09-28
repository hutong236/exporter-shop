#!/usr/bin/env python3
"""Exporter 商店清单本地校验（python3 + PyYAML）。

镜像平台仓库 backend/internal/console/registry/registry.go 的 FromDefs/validateTypeDef
加载期关键不变量，外加本仓库拆分结构约束。平台语义：任一条目非法 → 整份清单拒绝并
保留 last-good；本脚本目标是在推送前于本地/CI 拦截同类错误。

校验范围：
  A. 结构约束（拆分仓库自身）
     - exporters/<name>/exporter.yaml 一类一目录；目录下不得有其他 .yaml/.yml
       （平台目录模式会把目录内全部 yaml 当清单拉取合并）
     - 每文件恰一个条目，条目 name 与目录名一致
     - 文件数 ≤64、合并总字节 ≤768KiB（gitstore.go 目录模式上限）
     - 根 exporter-types.yaml 与 scripts/build.py 聚合产物一致（防漂移）
     - docs/exporter-params.md 与 scripts/docgen.py 生成产物一致（防漂移）
  B. 类型级不变量（registry.go 镜像，见各函数注释标注的对应行号语义）
     - name 正则 / metrics_port 必填 / target_mode·workload·config.mode 枚举
     - connection 互斥 probe 且须 raw+secret_mount+非空 template
     - sensitive ⇔ password；敏感落点仅 env|config；to:config 须 raw+secret_mount
     - probe 声明约束（path/modules/default_module/max_targets/auth）
     - scrape duration / resources quantity 格式
     - args_template 引用字段须已声明、非敏感、非 env 落点

用法：python3 scripts/validate.py   （任何 FAIL 退出码 1）
"""

import pathlib
import re
import sys

import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "exporters"

MAX_FILES = 64                # gitstore.go MaxTypesFiles
MAX_TOTAL_BYTES = 768 * 1024  # gitstore.go MaxTotalTypesBytes

NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
QUANTITY_RE = re.compile(r"^[+-]?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?(m|K|M|G|T|P|E|Ki|Mi|Gi|Ti|Pi|Ei)?$")
DURATION_RE = re.compile(r"^([0-9]+(\.[0-9]+)?(ns|us|µs|ms|s|m|h))+$")
TMPL_FIELD_RE = re.compile(r"\.([A-Za-z_][A-Za-z0-9_]*)")

KINDS = {"text", "number", "password", "select"}
TOS = {"env", "arg", "var", "config"}
MODES = {"", "hutong", "raw", "none"}
WORKLOADS = {"", "deployment", "daemonset"}
TARGET_MODES = {"", "probe", "connection"}

errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def balanced_template(name: str, where: str, tmpl: str) -> None:
    """Go text/template 语法无法在 python 完整复刻，退而校验定界符配对与嵌套平衡。"""
    depth = 0
    i = 0
    while i < len(tmpl) - 1:
        if tmpl[i:i + 2] == "{{":
            depth += 1
            i += 2
            continue
        if tmpl[i:i + 2] == "}}":
            depth -= 1
            if depth < 0:
                err(f"类型 {name} {where} 模板定界符不配对（多余的 }}）")
                return
            i += 2
            continue
        i += 1
    if depth != 0:
        err(f"类型 {name} {where} 模板定界符不配对（缺少 }}）")


def validate_type(t: dict) -> None:
    name = t.get("name", "<空 name>")
    # FromDefs：name 非空 + 正则 + metrics_port 必填
    if not t.get("name"):
        err(f"存在空 name 条目")
        return
    if not NAME_RE.match(t["name"]):
        err(f"类型 {name} name 非法（须 ^[a-z][a-z0-9_]*$）")
    port = t.get("metrics_port", 0)
    if not isinstance(port, int) or not (1 <= port <= 65535):
        err(f"类型 {name} 缺少/非法 metrics_port: {port!r}")

    # target_mode 枚举 + connection 约束
    tm = t.get("target_mode", "")
    if tm not in TARGET_MODES:
        err(f"类型 {name} target_mode 非法: {tm!r}（须为空|probe|connection）")
    cfg = t.get("config") or {}
    mode = cfg.get("mode", "")
    if tm == "connection":
        if t.get("probe"):
            err(f"类型 {name} target_mode=connection 与 probe 声明互斥")
        if mode != "raw" or not cfg.get("secret_mount"):
            err(f"类型 {name} target_mode=connection 须搭配 raw + secret_mount 配置通道")
        if not cfg.get("template"):
            err(f"类型 {name} target_mode=connection 缺少 config.template")

    # workload
    wl = t.get("workload", "")
    if wl not in WORKLOADS:
        err(f"类型 {name} workload 非法: {wl!r}")
    if wl == "daemonset" and t.get("replicas", 0):
        err(f"类型 {name} daemonset 不支持 replicas")

    # config.mode 枚举 + configless 冲突
    if mode not in MODES:
        err(f"类型 {name} config.mode 非法: {mode!r}")
    if t.get("configless") and mode not in ("", "none"):
        err(f"类型 {name} configless 与 config.mode={mode!r} 冲突")
    if mode == "raw":
        if not cfg.get("template"):
            err(f"类型 {name} raw 模式缺少 config.template")
        else:
            balanced_template(name, "config.template", cfg["template"])
    if mode == "none" and cfg.get("template"):
        err(f"类型 {name} none 模式不应携带 config.template")

    # probe 声明
    probe = t.get("probe")
    if probe:
        p = probe.get("path", "")
        if p and (not p.startswith("/") or re.search(r"\s", p)):
            err(f"类型 {name} probe.path 非法: {p!r}")
        modules = probe.get("modules") or []
        if len(set(modules)) != len(modules) or any(not m for m in modules):
            err(f"类型 {name} probe.modules 存在空条目或重复")
        dm = probe.get("default_module", "")
        if dm and dm not in modules:
            err(f"类型 {name} probe.default_module {dm!r} 不在模块枚举内")
        mt = probe.get("max_targets", 0)
        if not (0 <= mt <= 5000):
            err(f"类型 {name} probe.max_targets 超界: {mt}")
        if probe.get("auth", "") and (mode != "raw" or not cfg.get("secret_mount")):
            err(f"类型 {name} probe.auth 须搭配 raw + secret_mount 配置通道")

    # secret_mount 仅 raw
    if cfg.get("secret_mount") and mode != "raw":
        err(f"类型 {name} secret_mount 仅支持 raw 模式")

    # scrape duration / resources quantity
    sc = t.get("scrape") or {}
    for k in ("interval", "timeout"):
        v = sc.get(k, "")
        if v and not DURATION_RE.match(v):
            err(f"类型 {name} scrape.{k} 非法: {v!r}")
    res = t.get("resources") or {}
    for kind, m in (("requests", res.get("requests") or {}), ("limits", res.get("limits") or {})):
        for k, v in m.items():
            if not QUANTITY_RE.match(str(v)):
                err(f"类型 {name} resources.{kind}[{k}] 非法: {v!r}")

    # fields
    fields = t.get("fields") or []
    by_key: dict[str, dict] = {}
    for f in fields:
        key = f.get("key", "")
        if not key:
            err(f"类型 {name} 存在空 fields.key 条目")
            continue
        if key in by_key:
            err(f"类型 {name} 字段 {key} 重复声明")
        by_key[key] = f
        kind = f.get("kind", "")
        to = f.get("to", "")
        if kind not in KINDS:
            err(f"类型 {name} 字段 {key} kind 非法: {kind!r}")
        if bool(f.get("sensitive")) != (kind == "password"):
            err(f"类型 {name} 字段 {key} sensitive 与 password 控件须双向绑定")
        if to not in TOS:
            err(f"类型 {name} 字段 {key} to 非法: {to!r}")
        if f.get("sensitive") and to not in ("env", "config"):
            err(f"类型 {name} 敏感字段 {key} 只允许落点 env|config")
        if to == "config":
            if not f.get("sensitive"):
                err(f"类型 {name} config 落点字段 {key} 仅供敏感凭据插值")
            if mode != "raw" or not cfg.get("secret_mount"):
                err(f"类型 {name} 字段 {key} config 落点要求 raw + secret_mount 配置通道")
        if to == "env" and not f.get("env"):
            err(f"类型 {name} 字段 {key} 落点 env 缺少 env 变量名")
        if kind == "select" and not f.get("options"):
            err(f"类型 {name} select 字段 {key} 缺少 options")
        if kind == "number" and f.get("default", "") != "":
            d = f["default"]
            if not re.match(r"^-?[0-9]+$", str(d)):
                err(f"类型 {name} 字段 {key} number default 非法: {d!r}")

    # args_template：占位符引用已声明的非敏感、非 env 落点字段
    for i, arg in enumerate(t.get("args_template") or []):
        balanced_template(name, f"args_template[{i}]", arg)
        body = "".join(m.group(0) for m in re.finditer(r"\{\{.*?\}\}", arg, re.S))
        for ref in set(TMPL_FIELD_RE.findall(body)):
            fd = by_key.get(ref)
            if fd is None:
                err(f"类型 {name} args_template[{i}] 引用未声明字段 {ref!r}")
            elif fd.get("sensitive"):
                err(f"类型 {name} args_template[{i}] 引用敏感字段 {ref!r}（禁止进 args）")
            elif fd.get("to") == "env":
                err(f"类型 {name} args_template[{i}] 引用 env 落点字段 {ref!r}（插值域仅 arg/var）")


def main() -> None:
    # A. 结构约束
    yaml_files = sorted(SRC_DIR.rglob("*.y*ml"))
    extras = [str(p.relative_to(REPO)) for p in yaml_files if p.name != "exporter.yaml"]
    if extras:
        err(f"exporters/ 下存在非 exporter.yaml 的 yaml（目录模式会被平台当清单拉取）: {extras}")
    files = sorted(SRC_DIR.glob("*/exporter.yaml"))
    if not files:
        err("exporters/ 下未发现 */exporter.yaml 源文件")
    if len(files) > MAX_FILES:
        err(f"源文件数 {len(files)} 超过平台目录模式上限 {MAX_FILES}")

    total, seen_names, types = 0, {}, []
    for f in files:
        raw = f.read_text()
        total += len(raw.encode())
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            err(f"{f} YAML 解析失败: {e}")
            continue
        entries = (doc or {}).get("types") or []
        if len(entries) != 1:
            err(f"{f} 须恰含 1 个条目，实际 {len(entries)}")
            continue
        t = entries[0]
        dname = f.parent.name
        if t.get("name") != dname:
            err(f"{f} 条目 name {t.get('name')!r} 与目录名 {dname!r} 不一致")
        if t.get("name") in seen_names:
            err(f"类型 {t.get('name')!r} 跨文件重复（{seen_names[t['name']]} 与 {f}）")
        seen_names[t.get("name", "?")] = str(f.relative_to(REPO))
        validate_type(t)
        types.append(t)
    if total > MAX_TOTAL_BYTES:
        err(f"合并总字节 {total} 超过平台目录模式上限 {MAX_TOTAL_BYTES}")

    # A4. 根清单防漂移（与 build.py 聚合产物逐字节一致）
    sys.path.insert(0, str(REPO / "scripts"))
    import build  # noqa: E402  复用聚合逻辑，保证与生成口径一致
    out, count = build.collect()
    root = REPO / "exporter-types.yaml"
    current = root.read_text() if root.exists() else ""
    if current != out:
        err("exporter-types.yaml 与 exporters/ 源目录不一致（漂移），请运行 python3 scripts/build.py")

    # A5. 参数对比文档防漂移（与 docgen.py 生成产物一致）
    import docgen  # noqa: E402  复用生成逻辑，保证与生成口径一致
    params_doc = REPO / "docs" / "exporter-params.md"
    doc_current = params_doc.read_text() if params_doc.exists() else ""
    if doc_current != docgen.render():
        err("docs/exporter-params.md 与 exporters/ 源目录不一致（漂移），请运行 python3 scripts/docgen.py")

    if errors:
        print(f"FAIL（{len(errors)} 处）：")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print(f"OK：{len(types)} 个类型全部通过校验；根清单与源目录一致（聚合 {count} 条目，{total} 字节）")


if __name__ == "__main__":
    main()
