# REQ-3 decisions — 裁定日志

## Gate A 裁定（2026-10-17 批准，来源 INTAKE 包）

| # | 裁定 | 状态 |
| --- | --- | --- |
| G-1 | spec 计数锚定具体值：18 类型 / 16 部署型 | 执行中偏离 → R-impl-1 |
| G-2 | mssql trust_server_certificate default "false"（显式等价上游默认） | 前提被证伪 → R-impl-2 |
| G-3 | 字段级细节（oracle DSN 变量名 / rocketmq 参数名 / atompi env 名 / metrics_port）实现期按所钉 tag 上游 README/源码核定；红线：凭据仅 flag 入口（env 不可用）的条目不可行，停下回报，不得硬编码明文 flag | 已执行 → R-impl-1 / R-impl-3 / R-impl-5 |
| G-4 | activemq-native 的 metrics_port 实现期选定（如 8778 惯例）并在 preface 注明 | 已执行 → R-impl-3 |
| G-5 | validate.py 不新增「镜像显式 tag」本地检查（平台 registry.go 无同规则，违反同步约束）；核验入 upstream-verification 文档 | 已执行（validate.py 零改动，核验已入文档） |
| G-6 | rocketmq 若上游无官方镜像，registry 路径属平台侧配套（非本单范围），显式 tag 硬规则不变 | 已执行（apache 官方镜像存在，无需平台配套） |
| G-7 | minio-native 不在本单（平台 REQ-265 内置承载） | 已执行（未触碰） |

## 实现期裁定（2026-10-18，coder 提报）

### R-impl-1 activemq_exporter 部署型条目不可行（触发 G-3 红线，本单不登记）

- 证据①（env 通道不存在）：atompi/activemq_exporter@main（仓库无任何 tag/release）凭据 `jolokia.username/password` 仅能写入 YAML 配置文件经 `--collector.config.file` 加载（`yaml.Unmarshal` 整体读入）；kingpin 声明中唯一 `Envar` 为 `GOMAXPROCS`。「凭据 sensitive+password、落点仅 env」无法满足。
- 证据②（无镜像可钉）：Docker Hub `atompi` 56 仓无 `activemq-exporter`（API 404）、ghcr.io DENIED、GitHub 无 release；其 docker-compose 引用的 `atompi/activemq-exporter:latest` 在 Hub 不存在。「镜像显式 tag」无可钉对象。
- 证据③（前提失效）：非 rm-hull fork（GitHub `fork: False`，rm-hull 无 activemq/jolokia 仓库）。
- 证据④（无替代）：Hub 全量检索 activemq/jolokia 仅 broker 与 agent 镜像；GitHub 候选（pulord 等）2019 年停更且无镜像。
- 处置：停下回报（本结果 + 协调者通报），不硬凑 flag/config 明文注入；目录按 **17 类型 = 15 部署/市场 + 2 直连** 落地（偏离 G-1 锚点 18/16，主规格按真实计数合并）。后续如仍需部署型条目：平台侧构建发布镜像（可钉 tag）+ 凭据改走 config secret_mount 通道的设计修订，另行立单。

### R-impl-2 mssql trust_server_certificate default 取 "true"（G-2 字面值被上游事实证伪）

- 上游 v1.3.0：`trustServerCertificate: process.env["TRUST_SERVER_CERTIFICATE"] !== undefined ? ... === "true" : true`（src/index.js）；README「optional defaults to true」。未设 env 时上游兜底为 **true**，非 G-2 前提的 false。
- 若按 "false" 注入：既有实例重部署时 trustServerCertificate 由 true→false，自签名证书 SQL Server 断连；且违反批准 delta Scenario「未填新字段时 env 注入与上游默认等价」。
- 处置：按 G-2 自身意图（显式等价上游默认）+ G-3 授权的实现期上游核定取 **"true"**（ENCRYPT 无偏差）。已通报协调者待确认；如最终坚持字面值 false，一行可改（`default: "true"→"false"` + hint/spec 同步）。

### R-impl-3 activemq-native 端口与前置文档化（执行 G-4）

- metrics_port 选 **8778**（ActiveMQ Artemis 官方文档 jmx_exporter javaagent 示例惯例端口），preface 注明「实例级可改」；javaagent 前置为平台外部事项，仅 preface 文档化（平台不可强制）。

### R-impl-4 rocketmq 字段拆分与 health_path

- ACL AccessKey 按目录标识符惯例（ES_USERNAME/USERNAME 先例）作 text 非敏感；SecretKey `sensitive+password` 仅 env。条目零 args_template（凭据零命令行暴露）。
- `health_path: /metrics`：Spring 未映射 `/`（404），`/metrics` 恒 200——目录内首个取 /metrics 的部署型条目（其余均有 / 落地页）。
- 镜像 amd64-only 记录为风险（mssql v1.3.0 同况先例）。

### R-impl-5 oracle 通道形态（执行 G-3 核定）

- env 名取上游 compose 口径 `DB_USERNAME` / `DB_PASSWORD` / `DB_CONNECT_STRING`；渲染配置经 `${VAR}` 占位 + 上游 `os.Expand` 运行期展开（config/config.go@v2.5.0）——模板内无明文敏感值，故 `secret_mount: false`（ConfigMap），密码实际走平台 Secret env。
- 配置模板照抄上游示例键（UnmarshalStrict，未知键启动失败）；镜像匿名可拉（OCR registry API 实测，无许可墙）。
