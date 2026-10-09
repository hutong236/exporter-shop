# exporter-catalog Specification

## Purpose

规范 exporter-shop 商店目录的三件套行为：`exporters/<name>/exporter.yaml` 类型条目声明（含直连原生端点型）、镜像平台仓库 `backend/internal/console/registry/registry.go` 加载期校验的本地校验脚本 `scripts/validate.py`，以及由 `scripts/docgen.py` 从源目录生成的参数对比文档 `docs/exporter-params.md`。本地校验与文档生成口径 SHALL 与平台现行校验规则保持同步。

## Requirements

### Requirement: 直连原生端点类型条目

商店目录 SHALL 支持登记 `target_mode: endpoint` 的直连原生端点类型（外部已部署 exporter 的免部署登记观测，平台 REQ-181 机制）。该类条目 SHALL 仅声明 `name` / `label` / `preface` / `target_mode` / `metrics_port` / `target_contract`（`mode/path/scheme`），SHALL NOT 声明 `image` / `fields` / `config` / `requires_devices` / `probe` / `target_health_metric` / `workload`。

#### Scenario: 新增外部 node_exporter 直连条目

- **WHEN** 商店目录含 `target_mode: endpoint` 的 `node-exporter-external` 条目（声明形态如上，省略 `scrape.interval` 与 `health_path`）
- **THEN** `python3 scripts/validate.py` 全部通过（14 个类型，退出码 0）
- **THEN** 平台经 Git 目录模式拉取该清单可用，登记实例仅物化单个 VMStaticScrape（零工作负载）

#### Scenario: endpoint 条目携带禁止键

- **WHEN** endpoint 条目声明任一禁止键（`workload`（非 none 归一形态）/ `image` / `fields` / `config` / `requires_devices` / `probe` / `target_health_metric`，或 `target_contract.mode` ≠ endpoint）
- **THEN** `scripts/validate.py` 对应条目 FAIL
- **THEN** 本地 FAIL 项与平台 registry.go `validateEndpointType` 拒绝矩阵一一对应

### Requirement: 类型 name 规则与平台同步

本地校验脚本的类型 name 正则 SHALL 镜像平台现行规则 `^[a-z](?:[a-z0-9_-]*[a-z0-9_])?$`（允许中划线、收尾禁连字符，平台 REQ-181 放宽口径），校验错误文案 SHALL 同步该口径；`README.md` 清单格式说明 SHALL 与该规则保持一致。

#### Scenario: 连字符 key 通过

- **WHEN** 条目 name 为含中划线的合法 key（如 `node-exporter-external`）
- **THEN** `scripts/validate.py` 通过（放宽只扩大接受域，既有全下划线 key 不受影响）

#### Scenario: 收尾连字符拒绝

- **WHEN** 条目 name 以连字符收尾（如 `node-`）
- **THEN** `scripts/validate.py` FAIL 并提示收尾禁连字符的现行正则

### Requirement: 生成文档覆盖直连型

`scripts/docgen.py` SHALL 为 endpoint 型条目渲染目标模式标签（endpoint（直连原生端点））、免部署工作负载标签（none（免部署），含平台归一语义）、直连契约明细（`target_contract` 的 mode/path/scheme）与空镜像占位（`—`）；既有条目的渲染输出 SHALL 逐字节不变。

#### Scenario: 再生成无漂移

- **WHEN** 源目录含 endpoint 条目时运行 `python3 scripts/docgen.py` 重新生成 `docs/exporter-params.md`
- **THEN** `python3 scripts/validate.py`（含防漂移检查）通过

#### Scenario: 既有条目渲染不变

- **WHEN** 新增 endpoint 条目后重新生成文档
- **THEN** 既有 13 个市场类条目的总览行与明细节逐字节不变（diff 仅新增该类型的总览行、明细节与计数行）
