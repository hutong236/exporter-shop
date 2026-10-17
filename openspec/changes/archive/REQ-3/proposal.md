# REQ-3 proposal — 商店目录补充缺口产品类型条目

## 需求背景

Issue hutong236/exporter-shop#3：商店目录补充缺口产品类型——新增 oracle_exporter / rocketmq_exporter / activemq_exporter / activemq-native 条目并为 mssql_exporter 追加 TLS 兼容字段，目标为「外部中间件/数据库监控零平台代码接入」。规划来源：平台会话 hulane-planner 完整报告（2026-10-17，INTAKE 包 `.hulane/INTAKE-catalog-gap-products.md`），Gate A 已批准（approval_source=auto_intake）。

## 落地内容（本 PR）

1. 新增部署型条目 `exporters/oracle_exporter/exporter.yaml`：上游 oracle/oracle-db-appdev-monitoring v2.5.0（原 oracle-db-exporter 更名），镜像 `container-registry.oracle.com/database/observability-exporter:2.5.0`（amd64+arm64 双架构、匿名可拉）；YAML 配置经 config/raw 模板渲染（模板内仅 `${DB_USERNAME}` / `${DB_PASSWORD}` / `${DB_CONNECT_STRING}` 占位，上游 `os.Expand` 运行期展开），三字段 env 落点，数据库密码 `sensitive+password` 经 Secret 环境变量注入。
2. 新增部署型条目 `exporters/rocketmq_exporter/exporter.yaml`：上游 apache/rocketmq-exporter 0.0.2（Apache 官方 Docker Hub 镜像，amd64-only），NameServer 地址 + ACL 凭据全部经 Spring Boot relaxed binding 环境变量注入（`ROCKETMQ_CONFIG_*`），SecretKey `sensitive+password` 仅 env 落点，条目不声明任何 args_template。
3. 新增直连原生端点条目 `exporters/activemq-native/exporter.yaml`：broker 侧预挂 jmx_exporter javaagent 后登记观测，最小声明 + preface 注明外部前置与 8778 端口惯例。
4. `exporters/mssql_exporter/exporter.yaml` 追加 `mssql_encrypt`（env `ENCRYPT`，default true）/ `mssql_trust_server_certificate`（env `TRUST_SERVER_CERTIFICATE`，default true）两个 advanced select env 字段（sensitive=false），既有 4 字段与镜像/端口声明逐字节不变；支撑 SQL Server 2008 R2 老版本 TLS 兼容。
5. `python3 scripts/docgen.py` 再生成 `docs/exporter-params.md`；`README.md` 目录表同步为 15 市场类 + 2 直连型；`docs/upstream-verification.md` 增补 2026-10-18 核验小节（含 activemq_exporter 不可行核验记录）。
6. `scripts/validate.py` 与 `scripts/docgen.py` 零改动（禁止键矩阵、name 正则、落点校验、动态计数均已就位）。

## 与批准范围的两处实现期偏差（均已回报协调者）

1. **activemq_exporter 部署型条目不可行，未登记**（触发红线「凭据 env 不可用须停下回报」）：atompi/activemq_exporter 凭据仅能经 YAML 配置文件注入（无 env 入口），且无任何公开镜像可钉 tag（Docker Hub / ghcr 实测不存在）；「= rm-hull 活跃 fork」前提亦不成立（GitHub fork:False）。证据链见 `docs/upstream-verification.md`「activemq_exporter 部署型可行性核验（2026-10-18）」。目录计数因此为 **17 类型 = 15 部署/市场 + 2 直连**（批准锚点为 18/16）。ActiveMQ 场景由 activemq-native 直连条目承载；部署型条目待平台侧构建发布镜像 + 凭据改 config secret_mount 通道的设计修订后另行立单。
2. **mssql trust_server_certificate default 取 "true" 而非裁定的 "false"**：裁定 #2 的前提「上游默认 false」与 v1.3.0 事实不符（README 与 src/index.js 均为 defaults to true）。注入 false 将使既有实例重部署时 trustServerCertificate 由 true 变 false（自签名证书 SQL Server 断连），且违反批准 delta Scenario「未填新字段时 env 注入与上游默认等价」；按裁定自身的「显式等价上游默认」意图与上游事实取 "true"（ENCRYPT 无偏差）。

## 关联

- 规划包：`.hulane/INTAKE-catalog-gap-products.md`（主工作区，只读）；决策史全文见同目录 `decisions.md`。
- 平台机制：REQ-181（endpoint 型加载期归一与校验矩阵）；MinIO 场景由平台 REQ-265 内置承载（本单不含 minio-native）。
- 上游核验：`docs/upstream-verification.md` 2026-10-18 各小节。
