# REQ-3 spec delta — exporter-catalog（批准稿快照，3 ADDED + 2 MODIFIED）

> 本文件为 Gate A 批准的 delta 快照（approval_source=auto_intake，2026-10-17）。
> 实现期偏差（activemq_exporter 不可行、mssql trust_server_certificate default 按上游事实取 true）
> 见 `decisions.md` R-impl-1 / R-impl-2；主规格 `openspec/specs/exporter-catalog/spec.md`
> 按实际落地形态（17 类型 = 15 部署/市场 + 2 直连）合并。

## ADDED Requirements

### Requirement: 缺口产品部署型条目覆盖

商店目录 SHALL 覆盖缺口产品的部署型条目：oracle_exporter（YAML 配置经 config/raw 模板声明，DSN 敏感 env）/ rocketmq_exporter（namesrv 地址 + ACL 凭据 env）/ activemq_exporter（Jolokia URL + 凭据 env）；每个部署型条目镜像 SHALL 使用显式 tag；凭据字段 SHALL 满足 `sensitive+password` 且落点仅 env，SHALL NOT 经 args_template 注入敏感字段。

#### Scenario: oracle 条目登记

- **WHEN** 商店目录含 oracle_exporter 部署型条目（镜像显式 tag，DSN 凭据 sensitive+password 落点仅 env，YAML 配置经 config/raw 模板声明）
- **THEN** `python3 scripts/validate.py` 全部通过（18 个类型，退出码 0）

#### Scenario: rocketmq ACL 凭据落点

- **WHEN** rocketmq_exporter 条目声明 ACL 凭据（sensitive+password，落点仅 env）
- **THEN** `python3 scripts/validate.py` 通过，且该凭据不出现在任何 args_template 引用域

#### Scenario: activemq Jolokia 凭据落点

- **WHEN** activemq_exporter 条目声明 Jolokia 凭据（sensitive+password，落点仅 env）
- **THEN** `python3 scripts/validate.py` 通过，且该凭据不出现在任何 args_template 引用域

### Requirement: 缺口产品直连原生端点条目覆盖

商店目录 SHALL 含一个 `target_mode: endpoint` 的 activemq-native 条目，满足「直连原生端点类型条目」禁止键矩阵；preface SHALL 注明外部前置（broker 侧挂 jmx_exporter javaagent）。

#### Scenario: activemq-native 条目登记

- **WHEN** 商店目录含 `target_mode: endpoint` 的 activemq-native 条目（最小声明 + preface 注明 javaagent 前置与指标端口）
- **THEN** `python3 scripts/validate.py` 通过且禁止键全零命中

### Requirement: mssql_exporter TLS 兼容字段

mssql_exporter 条目 SHALL 声明 encrypt（env 名 `ENCRYPT`，default true）与 trust_server_certificate（env 名 `TRUST_SERVER_CERTIFICATE`）两个 advanced select env 字段（sensitive=false）；默认值 SHALL 与所钉上游 tag 默认行为等价；既有 4 字段声明 SHALL 不变。

#### Scenario: 新字段渲染且默认行为不变

- **WHEN** mssql_exporter 条目追加上述两个字段后重新生成文档
- **THEN** `python3 scripts/validate.py` 通过，既有 4 字段 diff 为零
- **THEN** 未填新字段时 env 注入与上游默认等价

## MODIFIED Requirements

### Requirement: 直连原生端点类型条目

#### Scenario: 新增外部 node_exporter 直连条目

- **WHEN** 商店目录含 `target_mode: endpoint` 的 `node-exporter-external` 条目（声明形态如上，省略 `scrape.interval` 与 `health_path`）
- **THEN** `python3 scripts/validate.py` 全部通过（18 个类型，退出码 0；计数由 14 增至 18）
- **THEN** 平台经 Git 目录模式拉取该清单可用，登记实例仅物化单个 VMStaticScrape（零工作负载）

#### Scenario: endpoint 条目携带禁止键

- **WHEN** endpoint 条目声明任一禁止键（`workload`（非 none 归一形态）/ `image` / `fields` / `config` / `requires_devices` / `probe` / `target_health_metric`，或 `target_contract.mode` ≠ endpoint）
- **THEN** `scripts/validate.py` 对应条目 FAIL
- **THEN** 本地 FAIL 项与平台 registry.go `validateEndpointType` 拒绝矩阵一一对应

### Requirement: 生成文档覆盖直连型

#### Scenario: 既有条目渲染不变

- **WHEN** 新增条目后重新生成文档，再剔除新条目重跑 docgen
- **THEN** 与 HEAD 渲染 diff 为空（既有条目总览行 / 明细节逐字节不变，diff 仅新增类型的行与计数行）
