# exporter-shop

[hutong-project-monitor](https://github.com/hutong236/hutong-project-monitor) 监控平台的 **Exporter 商店**：以 Git 仓库托管的设备 Exporter 类型标准目录。平台在「设置 → 商店来源」切换为 Git 源并指向本仓库后，按间隔自动拉取（或手动「立即拉取」）根路径的 [`exporter-types.yaml`](./exporter-types.yaml)，拉取到的类型即可在上线表单中使用，来源徽章显示为 **Git**。

平台不配置本仓库也完整可用（内置类型兜底）；接入后本仓库成为受版本管理与 PR 评审约束的标准目录。

## 接入方式

平台控制台 → **设置** → 商店来源切换为 **Git**，填写：

| 配置项 | 值 |
| --- | --- |
| 仓库地址（gitUrl） | `https://github.com/hutong236/exporter-shop` |
| 分支 | `main` |
| 文件路径 | `exporter-types.yaml`（平台固定，只读） |
| 拉取间隔 | 缺省 10 分钟，可调 |

保存后点击「立即拉取」，状态应为 `ok`；拉取失败或清单非法时平台保留上一次成功清单（last-good），不影响已上线 exporter。

## 当前目录（16 个市场类）

| 类型 key | 显示名 | 指标端口 | 说明 |
| --- | --- | --- | --- |
| `node_exporter` | Node Exporter | 9100 | 主机指标，DaemonSet 形态 |
| `mysql_exporter` | MySQL | 9104 | **连接型多目标**（1 实例 : N 目标，目标增删零滚动） |
| `postgresql_exporter` | PostgreSQL | 9187 | |
| `mongodb_exporter` | MongoDB | 9216 | |
| `redis_exporter` | Redis | 9123 | |
| `clickhouse_exporter` | ClickHouse | 9116 | |
| `elasticsearch_exporter` | Elasticsearch | 9114 | |
| `mssql_exporter` | SQL Server | 4000 | |
| `kafka_exporter` | Kafka | 9308 | |
| `rabbitmq_exporter` | RabbitMQ 3.x | 9419 | 上游已归档 |
| `memcached_exporter` | Memcached | 9150 | |
| `nginx_exporter` | NGINX | 9113 | |
| `haproxy_exporter` | HAProxy 1.x | 9101 | 上游已归档 |
| `apache_exporter` | Apache | 9117 | |
| `blackbox_exporter` | Blackbox 探针 | 9115 | 探针型（HTTP/TCP/ICMP 等探测） |
| `snmp_exporter` | SNMP 探针 | 9116 | 探针型（网络设备） |

## 清单格式

单一 YAML 文档，顶层 `types:` 为类型定义列表（TypeDef）。字段权威定义与校验逻辑在平台仓库 `backend/internal/console/registry/registry.go`。要点：

- `name`：类型 key，`^[a-z][a-z0-9_]*$`；`metrics_port` 必填；`label` 为显示名。
- `fields`：统一表单字段（`key/label/kind(text|number|password|select)/default/required/sensitive/options/to(env|arg|var|config)/env/advanced/hint`）。
- **敏感字段**：`sensitive: true` 必须搭配 `kind: password`，落点只允许 `env` 或 `config`（**禁止进 args**）；`to: config` 仅用于 raw 模板凭据插值（配套 `config.secret_mount: true`，物化为 Secret，密文存储）。
- **连接型多目标**：`target_mode: connection` 必须搭配 `config.mode: raw` + `config.secret_mount: true` + 非空 `config.template`（参照 `mysql_exporter` 条目）。
- **探针型**：由 `probe` 声明（`path/modules/default_module/max_targets`）。
- 平台拉取后走与内置类型完全相同的加载期校验，**任一条目非法将整份清单拒绝**（保留 last-good）；清单上限 2 MiB。
- 同 key 条目整体覆盖平台内置定义；优先级 内置 < Git < 页面新增。

## 维护

- 修改 `exporter-types.yaml` 请走 PR；字段说明与各类型逐字段清单另见平台仓库 `docs/exporter-config-inventory.md`。
- 平台侧无需重启：下一次定时拉取或手动「立即拉取」即生效；回滚即 revert 本仓库。
- 新增类型建议同时更新本 README 的目录表。

## License

Apache-2.0（见 [LICENSE](./LICENSE)）。
