#!/usr/bin/env python3
"""生成 docs/exporter-params.md：商店各类型 exporter 的表单参数对比文档。

- 源：exporters/<name>/exporter.yaml（唯一维护入口），按字典序读取（与平台目录模式合并顺序一致）。
- 输出：docs/exporter-params.md 为生成产物，请勿手改；validate.py 对本文件做防漂移检查。
- 分区：总览 → 非敏感参数注入对比 → 敏感字段（凭据）注入对比 → 逐类型明细
  （固定 args / args_template / 配置通道 / 探针声明 / 表单字段表）。

用法：
    python3 scripts/docgen.py            # 生成文档
    python3 scripts/docgen.py --check    # 仅校验文档与源目录一致（CI 用，漂移即退出码 1）
"""

import pathlib
import re
import sys

import yaml

REPO = pathlib.Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "exporters"
OUT_FILE = REPO / "docs" / "exporter-params.md"


def load_types() -> list[dict]:
    files = sorted(SRC_DIR.glob("*/exporter.yaml"))
    if not files:
        sys.exit(f"错误：{SRC_DIR} 下未发现 */exporter.yaml 源文件")
    types = []
    for f in files:
        doc = yaml.safe_load(f.read_text())
        entries = (doc or {}).get("types") or []
        if len(entries) != 1:
            sys.exit(f"错误：{f} 须恰含 1 个条目，实际 {len(entries)}")
        types.append(entries[0])
    return types


def cell(v) -> str:
    """表格单元格：转义竖线、压平换行。"""
    return str(v).replace("|", "\\|").replace("\n", " ")


def target_mode_label(t: dict) -> str:
    tm = t.get("target_mode")
    if tm == "endpoint":
        return "endpoint（直连原生端点）"
    if tm == "connection":
        return "connection（1:N 多目标）"
    if t.get("probe"):
        return "probe（探针）"
    return "single（单目标）"


def channels_label(t: dict) -> str:
    parts = []
    if t.get("args"):
        parts.append("固定 args")
    if t.get("args_template"):
        parts.append("args_template")
    if (t.get("config") or {}).get("mode") == "raw":
        parts.append("config 模板")
    tos = {f.get("to") for f in t.get("fields") or []}
    if "env" in tos:
        parts.append("env")
    if not parts:
        parts.append("无表单参数")
    return " + ".join(parts)


def ctrl_label(f: dict) -> str:
    kind = f.get("kind", "")
    if kind == "password":
        return "password（敏感）"
    if kind == "select":
        return "select（" + " / ".join(str(o) for o in f.get("options") or []) + "）"
    return kind


def dest_label(f: dict) -> str:
    to = f.get("to", "")
    if to == "env":
        return f"env `{f.get('env', '')}`"
    if to == "arg":
        return "arg（args_template）"
    if to == "var":
        return "var（config 模板插值）"
    if to == "config":
        return "config（config 模板插值）"
    return to


def tmpl_refs(s: str) -> set[str]:
    """提取 {{ … }} 定界段内 .field 形式的字段引用（与 validate.py 同口径）。"""
    refs: set[str] = set()
    for m in re.finditer(r"\{\{.*?\}\}", str(s), re.S):
        refs.update(re.findall(r"\.([A-Za-z_][A-Za-z0-9_]*)", m.group(0)))
    return refs


def arg_frags(t: dict, key: str) -> list[str]:
    return [str(a) for a in t.get("args_template") or [] if key in tmpl_refs(a)]


def entry_label(t: dict, f: dict) -> str:
    """非敏感参数的上游入口：环境变量名或引用该字段的 args_template 原文。"""
    to = f.get("to", "")
    if to == "env":
        return f"环境变量 `{f.get('env', '')}`"
    if to == "arg":
        frags = arg_frags(t, f.get("key", ""))
        if frags:
            return "；".join(f"参数 `{cell(x)}`" for x in frags)
        return "args_template"
    return "config 模板插值"


def secret_entry_label(t: dict, f: dict) -> str:
    to = f.get("to", "")
    if to == "env":
        return f"环境变量 `{f.get('env', '')}`"
    mount = (t.get("config") or {}).get("mount_path", "")
    where = f"Secret 挂载 `{mount}`" if mount else "Secret 挂载"
    return f"config 模板插值（{where}）"


def default_cell(f: dict) -> str:
    d = f.get("default", "")
    return f"`{cell(d)}`" if d != "" else "—"


def overview_table(types: list[dict]) -> list[str]:
    lines = [
        "| 类型 | 显示名 | 镜像 | 端口 | 目标模式 | 参数注入 | 字段数 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for t in types:
        # 免部署条目（endpoint 型）无镜像，镜像列渲染 —
        image = f"`{cell(t['image'])}`" if t.get("image") else "—"
        lines.append(
            "| `{}` | {} | {} | {} | {} | {} | {} |".format(
                cell(t.get("name")),
                cell(t.get("label", "")),
                image,
                t.get("metrics_port"),
                target_mode_label(t),
                channels_label(t),
                len(t.get("fields") or []),
            )
        )
    return lines


def plain_params_table(types: list[dict]) -> list[str]:
    lines = [
        "| 类型 | 字段 | 显示名 | 控件 | 默认值 | 落点 | 上游入口 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for t in types:
        for f in t.get("fields") or []:
            if f.get("sensitive"):
                continue
            lines.append(
                "| `{}` | `{}` | {} | {} | {} | {} | {} |".format(
                    cell(t.get("name")),
                    cell(f.get("key")),
                    cell(f.get("label", "")),
                    ctrl_label(f),
                    default_cell(f),
                    dest_label(f),
                    entry_label(t, f),
                )
            )
    return lines


def secret_params_table(types: list[dict]) -> list[str]:
    lines = [
        "| 类型 | 字段 | 显示名 | 必填 | 落点 | 上游入口 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for t in types:
        for f in t.get("fields") or []:
            if not f.get("sensitive"):
                continue
            lines.append(
                "| `{}` | `{}` | {} | {} | {} | {} |".format(
                    cell(t.get("name")),
                    cell(f.get("key")),
                    cell(f.get("label", "")),
                    "✅" if f.get("required") else "—",
                    dest_label(f),
                    secret_entry_label(t, f),
                )
            )
    return lines


def type_section(t: dict) -> list[str]:
    out = [f"### {t.get('name')} — {cell(t.get('label', ''))}", ""]
    # endpoint 型 workload 由平台加载期归一为 none（registry.go normalizeEndpointType），
    # 源清单可省略声明——此处按归一后语义展示
    wl_raw = t.get("workload", "")
    if wl_raw == "none" or t.get("target_mode") == "endpoint":
        wl = "none（免部署）"
    elif wl_raw == "daemonset":
        wl = "daemonset（每节点）"
    else:
        wl = "deployment（缺省）"
    image = f"`{cell(t['image'])}`" if t.get("image") else "—"
    out.append(
        "- 镜像 {} ｜ 指标端口 `{}` ｜ 目标模式 {} ｜ 工作负载 {}".format(
            image, t.get("metrics_port"), target_mode_label(t), wl
        )
    )
    contract = t.get("target_contract")
    if contract:
        bits = [f"模式 `{contract.get('mode', '')}`", f"路径 `{contract.get('path', '')}`"]
        if contract.get("scheme"):
            bits.append(f"协议 `{contract['scheme']}`")
        out.append("- 目标契约（target_contract）：" + " ｜ ".join(bits))
    for m in t.get("host_mounts") or []:
        out.append(f"- hostPath 挂载：`{m.get('host_path')}` → `{m.get('mount_path')}`")
    tols = t.get("tolerations") or []
    if tols:
        keys = "、".join(f"`{c.get('key')}`" for c in tols)
        out.append(f"- 污点容忍：{keys}（{tols[0].get('effect', '')}）")
    res = t.get("resources") or {}
    if res.get("requests") or res.get("limits"):
        out.append(
            "- 资源：requests {}，limits {}".format(
                " / ".join(f"`{v}` {k}" for k, v in (res.get("requests") or {}).items()),
                " / ".join(f"`{v}` {k}" for k, v in (res.get("limits") or {}).items()),
            )
        )
    sc = t.get("scrape") or {}
    if sc.get("interval"):
        out.append(f"- 抓取间隔：`{sc['interval']}`")

    if t.get("preface"):
        out += ["", "> " + cell(t["preface"])]

    if t.get("args"):
        out += ["", "固定 `args`：", "", "```text"] + [str(a) for a in t["args"]] + ["```"]
    if t.get("args_template"):
        out += [
            "",
            "`args_template`（`{{ … }}` 为表单字段插值）：",
            "",
            "```text",
        ] + [str(a) for a in t["args_template"]] + ["```"]

    cfg = t.get("config") or {}
    if cfg.get("mode") == "raw":
        secret = "物化为 Secret" if cfg.get("secret_mount") else "ConfigMap"
        out += [
            "",
            f"配置通道：raw 模板（{secret}）→ 挂载 `{cfg.get('mount_path', '')}`",
            "",
            "<details><summary>config.template</summary>",
            "",
            "```text",
            str(cfg.get("template", "")).rstrip("\n"),
            "```",
            "",
            "</details>",
        ]

    p = t.get("probe")
    if p:
        mods = " / ".join(f"`{m}`" for m in p.get("modules") or [])
        bits = [f"端点 `{p.get('path')}`", f"模块 {mods}", f"默认 `{p.get('default_module')}`"]
        if p.get("auth"):
            bits.append(f"认证 `{p['auth']}`")
        out += ["", "探针声明：" + " ｜ ".join(bits)]

    fields = t.get("fields") or []
    if fields:
        out += [
            "",
            "表单字段：",
            "",
            "| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for f in fields:
            notes = []
            if f.get("advanced"):
                notes.append("高级字段（折叠展示）")
            if f.get("hint"):
                notes.append(cell(f["hint"]))
            out.append(
                "| `{}` | {} | {} | {} | {} | {} | {} |".format(
                    cell(f.get("key")),
                    cell(f.get("label", "")),
                    ctrl_label(f),
                    "✅" if f.get("required") else "—",
                    default_cell(f),
                    dest_label(f),
                    "；".join(notes) if notes else "—",
                )
            )
    else:
        out += ["", "（无表单字段）"]
    return out


def render() -> str:
    types = load_types()
    total = sum(len(t.get("fields") or []) for t in types)
    secrets = sum(1 for t in types for f in t.get("fields") or [] if f.get("sensitive"))
    lines = [
        "# Exporter 商店表单参数对比",
        "",
        "> ⚠️ 本文件由 `scripts/docgen.py` 从 `exporters/*/exporter.yaml` 自动生成，请勿手改。",
        "> 修改请编辑对应类型的源清单后执行 `python3 scripts/docgen.py` 重新生成。",
        "",
        f"- 覆盖 {len(types)} 个类型 / {total} 个表单字段（敏感字段 {secrets} 个），按字典序排列（与平台目录模式合并顺序一致）",
        "- 落点（`to`）语义：`env` = 环境变量；`arg` = 经 `args_template` 注入命令行；`var`/`config` = 渲染进 `config.template`（`config` 仅供敏感凭据，配套 `secret_mount` 物化为 Secret）",
        "- 控件为 `password` 的即敏感字段（`sensitive`，二者双向绑定）：只写不回显，落点仅允许 `env`/`config`，禁止进 args",
        "- 字段取值与上游行为（镜像 tag / 端口 / 环境变量 / flag 写法）的核验依据见 [upstream-verification.md](./upstream-verification.md)",
        "",
        "## 总览",
        "",
    ]
    lines += overview_table(types)
    lines += [
        "",
        "## 参数注入方式对比",
        "",
        "### 非敏感参数（地址 / 账号 / 开关）",
        "",
    ]
    lines += plain_params_table(types)
    lines += ["", "### 敏感字段（凭据）", ""]
    lines += secret_params_table(types)
    lines += ["", "## 逐类型明细", ""]
    for t in types:
        lines += type_section(t) + [""]
    return "\n".join(lines).rstrip("\n") + "\n"


def main() -> None:
    out = render()
    if "--check" in sys.argv:
        current = OUT_FILE.read_text() if OUT_FILE.exists() else ""
        if current != out:
            sys.exit("错误：docs/exporter-params.md 与 exporters/ 源目录不一致（漂移），请运行 python3 scripts/docgen.py")
        print("OK：docs/exporter-params.md 与源目录一致")
        return
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(out)
    print(f"已生成 {OUT_FILE.relative_to(REPO)}")


if __name__ == "__main__":
    main()
