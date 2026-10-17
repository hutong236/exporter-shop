# exporter-catalog Specification

## Purpose

规范 exporter-shop 商店目录的三件套行为：`exporters/<name>/exporter.yaml` 类型条目声明（含直连原生端点型）、镜像平台仓库 `backend/internal/console/registry/registry.go` 加载期校验的本地校验脚本 `scripts/validate.py`，以及由 `scripts/docgen.py` 从源目录生成的参数对比文档 `docs/exporter-params.md`。本地校验与文档生成口径 SHALL 与平台现行校验规则保持同步。

## Requirements

### Requirement: 直连原生端点类型条目

商店目录 SHALL 支持登记 `target_mode: endpoint` 的直连原生端点类型（外部已部署 exporter 的免部署登记观测，平台 REQ-181 机制）。该类条目 SHALL 仅声明 `name` / `label` / `preface` / `target_mode` / `metrics_port` / `target_contract`（`mode/path/scheme`），SHALL NOT 声明 `image` / `fields` / `config` / `requires_devices` / `probe` / `target_health_metric` / `workload`。

#### Scenario: 新增外部 node_exporter 直连条目

- **WHEN** 商店目录含 `target_mode: endpoint` 的 `node-exporter-external` 条目（声明形态如上，省略 `scrape.interval` 与 `health_path`）
- **THEN** `python3 scripts/validate.py` 全部通过（17 个类型，退出码 0；计数由 14 增至 17：+oracle_exporter / +rocketmq_exporter / +activemq-native）
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

- **WHEN** 新增 oracle_exporter / rocketmq_exporter / activemq-native 条目并修改 mssql_exporter 后重新生成文档，再剔除上述 3 个新增条目并还原 mssql_exporter 重跑 docgen
- **THEN** 与 HEAD 渲染 diff 为空（既有 14 个条目的总览行与明细节逐字节不变，本轮 diff 仅新增类型的行、mssql 新字段行与计数行）

### Requirement: 缺口产品部署型条目覆盖

商店目录 SHALL 覆盖缺口产品的部署型条目：oracle_exporter（YAML 配置经 config/raw 模板渲染，模板内仅 `${VAR}` 占位、由上游在配置加载期从环境变量展开；连接凭据 `sensitive+password` 落点仅 env）与 rocketmq_exporter（NameServer 地址与 ACL 凭据经 Spring Boot relaxed binding 环境变量注入）。每个部署型条目镜像 SHALL 使用显式 tag；凭据字段 SHALL 满足 `sensitive+password` 且落点仅 env，SHALL NOT 经 args_template 注入敏感字段。

#### Scenario: oracle 条目登记

- **WHEN** 商店目录含 oracle_exporter 部署型条目（镜像 `container-registry.oracle.com/database/observability-exporter:2.5.0`，`DB_USERNAME` / `DB_PASSWORD` / `DB_CONNECT_STRING` 三字段 env 落点，数据库密码 `sensitive+password`，YAML 配置经 config/raw 模板声明）
- **THEN** `python3 scripts/validate.py` 全部通过（17 个类型，退出码 0）
- **THEN** 渲染配置文件内不含明文凭据（仅 `${DB_PASSWORD}` 等占位，实际值经平台 Secret 环境变量注入）

#### Scenario: rocketmq ACL 凭据落点

- **WHEN** rocketmq_exporter 条目声明 ACL SecretKey（`sensitive+password`，env `ROCKETMQ_CONFIG_SECRETKEY`）且不声明任何 args_template
- **THEN** `python3 scripts/validate.py` 通过，且该凭据不出现在任何 args_template 引用域（凭据零命令行暴露）

### Requirement: 缺口产品直连原生端点条目覆盖

商店目录 SHALL 含一个 `target_mode: endpoint` 的 activemq-native 条目，满足「直连原生端点类型条目」的禁止键矩阵；preface SHALL 注明外部前置（broker 侧挂 jmx_exporter javaagent）与指标端口惯例（8778，实例级可改）。

#### Scenario: activemq-native 条目登记

- **WHEN** 商店目录含 `target_mode: endpoint` 的 activemq-native 条目（仅 `name` / `label` / `preface` / `target_mode` / `metrics_port` / `target_contract` 声明）
- **THEN** `python3 scripts/validate.py` 通过（17 个类型）且禁止键（`image` / `fields` / `config` / `requires_devices` / `probe` / `target_health_metric` / `workload`）全零命中

### Requirement: mssql_exporter TLS 兼容字段

mssql_exporter 条目 SHALL 声明 encrypt（env 名 `ENCRYPT`，default true）与 trust_server_certificate（env 名 `TRUST_SERVER_CERTIFICATE`，default true）两个 advanced select env 字段（sensitive=false）；默认值 SHALL 与所钉上游 tag（v1.3.0）未设置环境变量时的兜底行为等价（均为 true）；既有 4 字段与镜像/端口声明 SHALL 逐字节不变。

#### Scenario: 新字段渲染且默认行为不变

- **WHEN** mssql_exporter 条目追加上述两个字段后重新生成文档
- **THEN** `python3 scripts/validate.py` 通过（17 个类型），既有 4 字段（SERVER / PORT / USERNAME / PASSWORD）在源清单中的声明 diff 为零
- **THEN** 未改选新字段时注入的 env 与上游默认等价（`ENCRYPT=true` / `TRUST_SERVER_CERTIFICATE=true` 即上游未设 env 时的兜底值；SQL Server 2008 R2 等老版本由用户显式改选 false）

