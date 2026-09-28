# Exporter 商店上游配置核验报告

- 核验日期：2026-09-27
- 核验对象：`exporters/*/exporter.yaml` 全部 16 个类型
- 核验口径：以**所钉镜像 tag 版本的上游实际行为**为准（README@tag / 源码@tag / 镜像仓库 API 实测），不用最新版行为推断
- 核验维度：① 镜像 tag 存在性 ② `metrics_port` = 该版本默认监听端口 ③ `to: env` 变量名被该版本真实读取 ④ args / args_template flag 写法与字段默认值
- 本报告发现的全部不符项已在同日修正（见文末「修正记录」）；核验后状态：16/16 与上游实际配置一致
- **2026-09-28 移除**：rabbitmq_exporter 与 haproxy_exporter 因上游仓库归档已从商店目录删除（README 目录表同步为 14 类）；本文对应小节与汇总行保留为历史核验记录，不再对应现行目录

## 汇总

| 类型 | 镜像 | tag 存在 | 端口 | 环境变量 | flag/默认值 | 核验结论 | 修正 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| node_exporter | quay.io/prometheus/node-exporter:v1.9.1 | ✅ | ✅ 9100 | — | ✅ | ✅ 符合 | —（附 rootfs 建议） |
| mysql_exporter | quay.io/prometheus/mysqld-exporter:v0.15.1 | ✅ | ✅ 9104 | — | ✅ | ✅ 符合 | — |
| postgresql_exporter | prometheuscommunity/postgres-exporter:v0.15.0 | ✅ | ✅ 9187 | ✅ | — | ✅ 符合 | — |
| mongodb_exporter | percona/mongodb_exporter:0.43.1 | ✅ | ✅ 9216 | ✅ | ✅ | ✅ 符合 | — |
| redis_exporter | oliver006/redis_exporter:v1.66.0 | ✅ | ❌ 9123→**9121** | ✅ | ✅ | ❌ 端口不符 | 已修正 |
| clickhouse_exporter | f1yegor/clickhouse-exporter:~~1.1.0~~→latest | ❌→latest | ✅ 9116 | ❌ CLICKHOUSE_URL 不被读取 | 改为 `-scrape_uri` | ❌ tag+env 失效 | 已修正 |
| elasticsearch_exporter | quay.io/prometheuscommunity/elasticsearch-exporter:v1.9.0 | ✅ | ✅ 9114 | ✅ | ✅ | ✅ 符合 | hint 措辞微调 |
| mssql_exporter | awaragi/prometheus-mssql-exporter:~~1.3.1~~→v1.3.0 | ❌→v1.3.0 | ✅ 4000 | ✅ | — | ❌ tag 不存在 | 已修正 |
| kafka_exporter | danielqsj/kafka-exporter:v1.9.0 | ✅ | ✅ 9308 | ❌ KAFKA_SERVERS 不被读取 | 改为 `--kafka.server` | ❌ env 失效 | 已修正 |
| rabbitmq_exporter | kbudde/rabbitmq-exporter:1.0.0 | ✅ | ✅ 9419 | ✅ | ✅ | ✅ 符合 | — |
| memcached_exporter | quay.io/prometheus/memcached-exporter:v0.15.1 | ✅ | ✅ 9150 | — | ✅ | ✅ 符合 | — |
| nginx_exporter | nginx/nginx-prometheus-exporter:1.4.2 | ✅ | ✅ 9113 | — | ❌ 单横线 flag 直接报错 | ❌ flag 写法 | 已修正（双横线） |
| haproxy_exporter | quay.io/prometheus/haproxy-exporter:v0.15.0 | ✅ | ✅ 9101 | — | ⚠️ default 两头不靠 | ⚠️ 存疑 | default 已对齐 README 示例形态 |
| apache_exporter | quay.io/lusitaniae/apache-exporter:v1.1.0 | ✅ | ✅ 9117 | — | ✅ | ✅ 符合 | — |
| blackbox_exporter | quay.io/prometheus/blackbox-exporter:v0.25.0 | ✅ | ✅ 9115 | — | ✅ | ✅ 符合 | — |
| snmp_exporter | quay.io/prometheus/snmp-exporter:v0.26.0 | ✅ | ✅ 9116 | — | ❌ type 枚举含非法值（静默出错） | ❌ 模板 type 非法 | 已修正 |

## 逐项明细

### node_exporter ✅

- tag `v1.9.1` 存在：[quay API](https://quay.io/api/v1/repository/prometheus/node-exporter/tag/?limit=100&filter_tag_name=like:v1.9.1)
- 默认端口 9100：README「listens on HTTP port 9100 by default」；源码 `kingpinflag.AddFlags(..., ":9100")`（[README@v1.9.1](https://raw.githubusercontent.com/prometheus/node_exporter/v1.9.1/README.md)、[node_exporter.go@v1.9.1](https://raw.githubusercontent.com/prometheus/node_exporter/v1.9.1/node_exporter.go)）
- `--path.procfs` / `--path.sysfs` 均有效，配合 hostPath `/proc→/host/proc`、`/sys→/host/sys` 语义正确（[paths.go@v1.9.1](https://raw.githubusercontent.com/prometheus/node_exporter/v1.9.1/collector/paths.go)）
- **可选增强（未改）**：官方 Docker 宿主监控示例还建议挂载 `/ → /host/root` 并传 `--path.rootfs=/host/root`；缺失时无告警，但 filesystem collector 的 statfs 与 os_release collector 读到的是容器自身视图而非宿主机。如需主机磁盘使用率准确，后续可补该挂载与参数。

### mysql_exporter ✅

- tag `v0.15.1` 存在：[quay API](https://quay.io/api/v1/repository/prometheus/mysqld-exporter/tag/?limit=100&filter_tag_name=like:v0.15.1)
- 默认端口 9104（[mysqld_exporter.go@v0.15.1](https://raw.githubusercontent.com/prometheus/mysqld_exporter/v0.15.1/mysqld_exporter.go)）
- `--config.my-cnf` 有效；`.my.cnf` `[client]` 段为该版本标准凭据方式（[README@v0.15.1](https://raw.githubusercontent.com/prometheus/mysqld_exporter/v0.15.1/README.md)）。注：该版本 `DATA_SOURCE_NAME` 已移除，清单未使用，无影响。

### postgresql_exporter ✅

- tag `v0.15.0` 存在：[Docker Hub API](https://hub.docker.com/v2/repositories/prometheuscommunity/postgres-exporter/tags/v0.15.0)
- 默认端口 9187（[main.go@v0.15.0](https://raw.githubusercontent.com/prometheus-community/postgres_exporter/v0.15.0/cmd/postgres_exporter/main.go)）
- v0.15.0 仍以 `DATA_SOURCE_NAME` 为最高优先级 DSN 来源（"DATA_SOURCE_NAME always wins so we do not break older versions"；`POSTGRES_EXPORTER_DATA_SOURCE_NAME` 为更高版本引入）：[datasource.go@v0.15.0](https://raw.githubusercontent.com/prometheus-community/postgres_exporter/v0.15.0/cmd/postgres_exporter/datasource.go)

### mongodb_exporter ✅

- tag `0.43.1` 存在（GitHub release 带 v、Docker tag 不带，与上游 README 自身命名一致）：[Docker Hub API](https://hub.docker.com/v2/repositories/percona/mongodb_exporter/tags/0.43.1)
- 默认端口 9216；`MONGODB_URI` / `MONGODB_USER` / `MONGODB_PASSWORD` 均被读取（`env:` 声明）：[main.go@v0.43.1](https://raw.githubusercontent.com/percona/mongodb_exporter/v0.43.1/main.go)、[README@v0.43.1](https://raw.githubusercontent.com/percona/mongodb_exporter/v0.43.1/README.md)

### redis_exporter ❌→已修正（端口）

- tag `v1.66.0` 存在：[Docker Hub API](https://hub.docker.com/v2/repositories/oliver006/redis_exporter/tags/v1.66.0)
- **上游默认端口 9121（清单原写 9123）**：`getEnv("REDIS_EXPORTER_WEB_LISTEN_ADDRESS", ":9121")`、README `defaults to 0.0.0.0:9121`（[main.go@v1.66.0](https://raw.githubusercontent.com/oliver006/redis_exporter/v1.66.0/main.go)、[README@v1.66.0](https://raw.githubusercontent.com/oliver006/redis_exporter/v1.66.0/README.md)）。端口不符会导致平台按 9123 抓取失败。
- `REDIS_ADDR`（默认 `redis://localhost:6379`，与清单 default 一致）/ `REDIS_PASSWORD` 被读取 ✅
- **修正**：`metrics_port: 9123 → 9121`（同步 README 目录表）。

### clickhouse_exporter ❌→已修正（tag + env）

- **tag `1.1.0` 不存在**：Docker Hub 仅 `latest` 一个 tag（2021-06-17）：[tags 列表](https://hub.docker.com/v2/repositories/f1yegor/clickhouse-exporter/tags?page_size=100)。上游仓库 `f1yegor/clickhouse-exporter` 已删除（[API 404](https://api.github.com/repos/f1yegor/clickhouse-exporter)），继任仓库 [ClickHouse/clickhouse_exporter](https://github.com/ClickHouse/clickhouse_exporter)。
- **`CLICKHOUSE_URL` 不被读取**：二进制只 `os.Getenv` 读取 `CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD`（`CLICKHOUSE_LOGIN` 从未存在过，USER 是正名）；地址是 `-scrape_uri` 命令行 flag（默认 `http://localhost:8123/`）：[clickhouse_exporter.go@90ac11beab（latest 镜像所含代码）](https://raw.githubusercontent.com/ClickHouse/clickhouse_exporter/90ac11beab/clickhouse_exporter.go)
- 默认端口 9116 正确（`telemetry.address` 默认 `:9116`、Dockerfile `EXPOSE 9116`）
- **修正**：image → `f1yegor/clickhouse-exporter:latest`（唯一存在 tag）；`clickhouse_url` 落点 env→arg 并新增 `args_template: -scrape_uri={{.clickhouse_url}}`；USER/PASSWORD env 保留；preface 注明上游迁移与镜像陈旧风险（新版 ClickHouse 建议直接用内建 /metrics）。

### elasticsearch_exporter ✅（hint 微调）

- tag `v1.9.0` 存在：[quay API](https://quay.io/api/v1/repository/prometheuscommunity/elasticsearch-exporter/tag/?limit=100&filter_tag_name=like:v1.9.0)
- 默认端口 9114（[main.go@v1.9.0](https://raw.githubusercontent.com/prometheus-community/elasticsearch_exporter/v1.9.0/main.go)）
- `ES_USERNAME` / `ES_PASSWORD` / `ES_API_KEY` 均被 `os.Getenv` 读取；API Key 仅能经 `ES_API_KEY` 环境变量生效（该版本无 `--es.api-key` flag）；`ES_URI` 不被读取（清单用 args_template 传 `--es.uri`，正确）
- `--es.uri` / `--es.ssl-skip-verify` flag 写法正确；default `http://elasticsearch:9200` 为容器网络合理改写
- **微调**：原 hint「提供后覆盖账号密码」措辞不准（实现是追加 Authorization 头，同时填写会产生两个头），已改为「提供后以 API Key 认证……勿与账号密码同时填写」。

### mssql_exporter ❌→已修正（tag）

- **tag `1.3.1` 不存在**：Docker Hub 全部 tag 带 `v` 前缀且最高 `v1.3.0`，GitHub 同样无 1.3.1：[Docker Hub tags](https://hub.docker.com/v2/repositories/awaragi/prometheus-mssql-exporter/tags/?page_size=100)、[GitHub tags](https://api.github.com/repos/awaragi/prometheus-mssql-exporter/tags)
- `SERVER`（必填）/ `PORT`（缺省 1433）/ `USERNAME` / `PASSWORD` 环境变量全部正确（[src/index.js@v1.3.0](https://raw.githubusercontent.com/awaragi/prometheus-mssql-exporter/v1.3.0/src/index.js)）
- 默认端口 4000（[Dockerfile@v1.3.0](https://raw.githubusercontent.com/awaragi/prometheus-mssql-exporter/v1.3.0/Dockerfile)）
- **修正**：image → `awaragi/prometheus-mssql-exporter:v1.3.0`。

### kafka_exporter ❌→已修正（env 失效）

- tag `v1.9.0` 存在：[Docker Hub API](https://hub.docker.com/v2/repositories/danielqsj/kafka-exporter/tags/v1.9.0)
- 默认端口 9308（[kafka_exporter.go@v1.9.0](https://raw.githubusercontent.com/danielqsj/kafka_exporter/v1.9.0/kafka_exporter.go)）
- **`KAFKA_SERVERS` 不被读取**：v1.9.0 源码仅 `SASL_USER_PASSWORD` / `AWS_REGION` 两个 `os.Getenv`；镜像 ENTRYPOINT 为裸二进制无 env→flag 映射。服务地址唯一入口是 `--kafka.server` flag（可重复传，上游默认 `kafka:9092`）
- **修正**：`kafka_servers` 落点 env→arg 并新增 `args_template: --kafka.server={{.kafka_servers}}`；label 去掉「逗号分隔」（kingpin StringSlice 不拆逗号，单条插值只承载单地址），hint 注明多 broker 需扩展模板。

### rabbitmq_exporter ✅

- tag `1.0.0` 存在：[Docker Hub API](https://hub.docker.com/v2/repositories/kbudde/rabbitmq-exporter/tags/1.0.0)
- `RABBIT_URL`（确为 URL 非 URI）/ `RABBIT_USER` / `RABBIT_PASSWORD` 被读取；默认端口 9419（PUBLISH_PORT）；`http://127.0.0.1:15672` 与 `guest` 默认值与上游逐字一致（[README@v1.0.0](https://raw.githubusercontent.com/kbudde/rabbitmq_exporter/v1.0.0/README.md)）

### memcached_exporter ✅

- tag `v0.15.1` 存在：[quay API](https://quay.io/api/v1/repository/prometheus/memcached-exporter/tag/?limit=100&filter_tag_name=like:v0.15.1)
- 默认端口 9150；`--memcached.address` flag 正确且 default `localhost:11211` 与上游默认逐字一致（[main.go@v0.15.1](https://raw.githubusercontent.com/prometheus/memcached_exporter/v0.15.1/cmd/memcached_exporter/main.go)）

### nginx_exporter ❌→已修正（flag 写法）

- tag `1.4.2` 存在：[Docker Hub API](https://hub.docker.com/v2/repositories/nginx/nginx-prometheus-exporter/tags/1.4.2)
- 默认端口 9113；default `http://127.0.0.1:8080/stub_status` 与上游默认逐字一致（[exporter.go@v1.4.2](https://raw.githubusercontent.com/nginxinc/nginx-prometheus-exporter/v1.4.2/exporter.go)）
- **单横线 `-nginx.scrape-uri` / `-nginx.plus` 在 v1.4.2 直接报错**：该版本用 kingpin/v2（[go.mod@v1.4.2](https://raw.githubusercontent.com/nginxinc/nginx-prometheus-exporter/v1.4.2/go.mod)），单横线长 flag 被解析为短 flag 集合 → `unknown short flag 'n'`（[kingpin v2.4.0 parser](https://raw.githubusercontent.com/alecthomas/kingpin/v2.4.0/parser.go)）。README@v1.4.2 全部示例为双横线。
- **修正**：args_template 全部改双横线 `--nginx.scrape-uri=` / `--nginx.plus`。

### haproxy_exporter ⚠️→default 已对齐

- tag `v0.15.0` 存在：[quay API](https://quay.io/api/v1/repository/prometheus/haproxy-exporter/tag/?limit=100&filter_tag_name=like:v0.15.0)；上游仓库 archived 状态与清单「已归档」标注一致（[GitHub API](https://api.github.com/repos/prometheus/haproxy_exporter)）
- 默认端口 9101；`--haproxy.scrape-uri` flag 正确；`;csv` 后缀强制（README：「the `;csv` is mandatory」）
- **default 存疑**：原 `http://127.0.0.1:8404/haproxy?;csv` 既非上游默认（`http://localhost/;csv`，[haproxy_exporter.go@v0.15.0](https://raw.githubusercontent.com/prometheus/haproxy_exporter/v0.15.0/haproxy_exporter.go)）也不匹配 8404 端口的官方 promex 前端示例路径（该示例 CSV 地址应为 `/stats;csv`）——开箱大概率 404
- **修正**：default 改为 `http://localhost/haproxy?;csv`（路径形态对齐官方 README 示例，host 为占位风格），hint 注明按实际 stats 前端填写

### apache_exporter ✅

- tag `v1.1.0` 存在：[quay API](https://quay.io/api/v1/repository/lusitaniae/apache-exporter/tag/?limit=100&filter_tag_name=like:v1.1.0)
- 该版本 flag 确为 `--scrape_uri`（下划线）写法正确；default `http://localhost/server-status?auto` 与上游逐字一致；默认端口 9117（[README@v1.1.0](https://raw.githubusercontent.com/Lusitaniae/apache_exporter/v1.1.0/README.md)）

### blackbox_exporter ✅

- tag `v0.25.0` 存在：[quay API](https://quay.io/api/v1/repository/prometheus/blackbox-exporter/tag/?limit=100&filter_tag_name=like:v0.25.0)
- 默认端口 9115、`--config.file` flag、`/probe` 端点全部正确（[README@v0.25.0](https://raw.githubusercontent.com/prometheus/blackbox_exporter/v0.25.0/README.md)）
- config.yml 模板的 `modules/prober/timeout/preferred_ip_protocol` 结构在 v0.25.0 全部合法，三个模块与上游自带 blackbox.yml 同构（[config/config.go@v0.25.0](https://raw.githubusercontent.com/prometheus/blackbox_exporter/v0.25.0/config/config.go)、[blackbox.yml@v0.25.0](https://raw.githubusercontent.com/prometheus/blackbox_exporter/v0.25.0/blackbox.yml)）
- 提示：icmp 模块需容器具备 `CAP_NET_RAW`（README 有说明，属部署层事项）

### snmp_exporter ❌→已修正（模板 type 非法）

- tag `v0.26.0` 存在：[quay API](https://quay.io/api/v1/repository/prometheus/snmp-exporter/tag/?limit=100&filter_tag_name=like:v0.26.0)
- 默认端口 9116、`--config.file` flag、`/snmp` 端点、`auths: {community, version: 2}` 结构全部正确（[README@v0.26.0](https://raw.githubusercontent.com/prometheus/snmp_exporter/v0.26.0/README.md)、[generator/FORMAT.md@v0.26.0](https://raw.githubusercontent.com/prometheus/snmp_exporter/v0.26.0/generator/FORMAT.md)）
- **metric `type` 枚举含非法值**：v0.26.0 合法集为 `gauge/counter/OctetString/DateAndTime/DisplayString/PhysAddress48/Float/Double/InetAddress*/EnumAsInfo/EnumAsStateSet/Bits` 等（[generator/README.md@v0.26.0](https://raw.githubusercontent.com/prometheus/snmp_exporter/v0.26.0/generator/README.md)）；原模板的 `index`、`map`、`timedelta` 均不存在，且**未知 type 不报错而是静默落入字符串分支**（指标值恒为 1.0，[collector/collector.go@v0.26.0](https://raw.githubusercontent.com/prometheus/snmp_exporter/v0.26.0/collector/collector.go)）
- **修正**：
  - `ifIndex` metric type `index→gauge`；全部 `indexes.type: index→gauge`（对齐上游生成物 snmp.yml 写法）
  - `ifType` type `map→gauge`（保留 lookups）
  - `ifAdminStatus` / `ifOperStatus` type `map→EnumAsStateSet` + IF-MIB 标准 `enum_values`（1 up / 2 down / 3 testing / 4 unknown / 5 dormant；ifOperStatus 另含 6 notPresent / 7 lowerLayerDown）
  - `sysUpTime` type `timedelta→gauge`；sysuptime 模块 `walk: [1.3.6.1.2.1.1.3]` → `get: [1.3.6.1.2.1.1.3.0]`（对齐上游 if_mib 对该标量的取法）
- 边界说明：if_mib 的 walk 范围仅覆盖 ifTable（`1.3.6.1.2.1.2.2.1.x`），不含 ifXTable 高速计数器列（`1.3.6.1.2.1.31.1.1`）；需要时经类型覆盖扩展。

## 修正记录（2026-09-27）

| # | 类型 | 修正内容 |
| --- | --- | --- |
| 1 | redis_exporter | `metrics_port: 9123 → 9121`（上游默认端口，原值抓取必失败） |
| 2 | clickhouse_exporter | image `1.1.0 → latest`（原 tag 不存在）；`clickhouse_url` env→arg + `args_template: -scrape_uri=`（原 `CLICKHOUSE_URL` env 不被读取，等于不生效）；preface 注明上游迁移/镜像陈旧 |
| 3 | kafka_exporter | `kafka_servers` env→arg + `args_template: --kafka.server=`（原 `KAFKA_SERVERS` env 不被读取）；label/hint 移除逗号分隔多地址语义 |
| 4 | mssql_exporter | image `1.3.1 → v1.3.0`（原 tag 不存在，上游从未发布 1.3.1） |
| 5 | nginx_exporter | args_template 单横线→双横线（kingpin v2 下原写法启动即报 `unknown short flag`） |
| 6 | snmp_exporter | 模板 type 枚举修正：`index/map/timedelta → gauge/EnumAsStateSet`；sysuptime 改 `get` 取法（原写法静默产出错误指标） |
| 7 | haproxy_exporter | default `http://127.0.0.1:8404/haproxy?;csv → http://localhost/haproxy?;csv`（对齐 README 示例形态 + 占位风格） |
| 8 | elasticsearch_exporter | `es_api_key` hint 措辞修正（覆盖→并存告警） |
| — | README | 目录表 redis 端口 9123→9121；clickhouse/kafka 说明补充 |

未修正的遗留建议（供后续决策）：

- node_exporter 可选补 `--path.rootfs` + `/ → /host/root` 挂载（filesystem/os_release collector 主机视图准确性）；属功能增强，未纳入本次最小变更。
- clickhouse_exporter 镜像 2021 年后未更新、上游已迁移，长期建议评估替换（新版 ClickHouse 内建 /metrics 端点）。
- kafka_exporter 多 broker 地址需扩展该类型 args_template（平台字段插值单条承载单地址）。

## 多目标属性（target_mode）核验（2026-09-27 第二轮）

平台三种目标模式：`single`（单实例单目标）/ `connection`（1 实例 : N 目标，抓取配置经三段式 relabel 注入 `?target=<host:port>`，凭据实例级共享）/ `probe`（探针型，`?target=&module=`）。判定标准：**只有上游抓取端点真实接受 `?target=` 且凭据可实例级共享的类型才适用 connection**；connection 还须满足平台强制条件 raw + secret_mount + template。逐项核验（上游 README@tag / 源码为证）：

| 类型 | 现配置 | 上游多目标能力 | 结论 |
| --- | --- | --- | --- |
| node_exporter | single + DaemonSet | 无（主机级 1:1） | ✅ 正确 |
| mysql_exporter | connection | **支持，但端点是 `/probe?target=` 非 `/metrics?target=`**（README@v0.15.1 正文 + probe.go；README 的 YAML 示例漏写 metrics_path 为上游文档瑕疵） | ❌ **平台侧路径缺陷，见下** |
| postgresql_exporter | single | 支持 `/probe?target=` + `?auth_module=`（v0.12.0 引入）；但平台 connection 不注入 auth_module 参数，凭据必须走 URL（平台 targets 仅 host:port） | ✅ single 是当前唯一可行模式 |
| mongodb_exporter | single | "闭集"多目标：目标必须启动时枚举进 MONGODB_URI，`/scrape?target=` 只查预建映射，未预配置返回 404；新增目标需重启 | ✅ 正确（connection 会 404） |
| redis_exporter | single | 支持 `/scrape?target=` + 共享密码（--redis.password）；但平台 connection 强制凭据走 raw 配置通道，redis 仅支持 env 共享密码/host 键控 password-file | ✅ single 正确；升级 connection 属平台增强项 |
| clickhouse_exporter | single | 无 | ✅ 正确 |
| elasticsearch_exporter | single | 无（--es.uri 单值） | ✅ 正确 |
| mssql_exporter | single | 无（SERVER 单值，官方 FAQ 建议多容器） | ✅ 正确 |
| kafka_exporter | single | 无 ?target= 语义；--kafka.server 可重复 = 1 实例 : 1 集群（cluster 级指标） | ✅ 正确 |
| rabbitmq_exporter | single | 无（RABBIT_URL 单值） | ✅ 正确 |
| memcached_exporter | single | 支持 `/scrape?target=`（无凭据）；但平台 connection 强制 raw+secret_mount+template，memcached 无任何配置文件可渲染 | ✅ single 是当前唯一可行模式 |
| nginx/haproxy/apache_exporter | single | 无（单 endpoint 参数语义） | ✅ 正确 |
| blackbox_exporter | probe | `/probe?target=&module=` 与平台渲染完全一致 | ✅ 正确 |
| snmp_exporter | probe | `/snmp?target=&module=&auth=` 与平台渲染完全一致（probe.auth → ?auth=public_v2） | ✅ 正确 |

### mysql_exporter connection 的路径缺陷（需平台侧修复）

- **现象**：平台 connection 模式目标抓取路径取 `scrape.path`，缺省 `/metrics`（operator `builder.go` BuildVMStaticScrape 连接型分支）。mysql 条目未设 `scrape.path` → N 个目标全部打在裸 `/metrics?target=` 上；而 mysqld-exporter v0.15.1 的 `/metrics` 是普通单实例端点（不接受 target），多目标处理器在 `/probe`。结果：**全部目标拿到同一份 exporter 自身指标（mysql_up=0），静默错数据**。
- **为什么商店侧不能单独修**：`scrape.path` 同时驱动自身指标抓取（BuildVMServiceScrape，self 恒在）。若设 `/probe`，目标抓取修好，但自身抓取 `/probe`（无 target 参数）返回 HTTP 400 "target is required" → self up=0。一个开关两条链路，无两全值。
- **修复建议（hutong-project-monitor 平台侧）**：connection 模式下将目标抓取路径与 self 抓取路径解耦——例如 BuildVMStaticScrape 连接型分支新增类型级 `scrape.target_path`（或复用 probe 类似声明），self 恒定 `/metrics`；平台修复后商店侧为 mysql 条目声明目标路径 `/probe`。memcached（/scrape）与 redis（/scrape）若未来升级 connection 同样依赖该解耦。
- 上游佐证：mysqld `/probe` 缺 target 返回 400（probe.go）；裸 `/metrics` HTTP 200、mysql_up=0（[README@v0.15.1](https://raw.githubusercontent.com/prometheus/mysqld_exporter/v0.15.1/README.md)、[probe.go@v0.15.1](https://raw.githubusercontent.com/prometheus/mysqld_exporter/v0.15.1/probe.go)）。
