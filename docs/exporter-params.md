# Exporter 商店表单参数对比

> ⚠️ 本文件由 `scripts/docgen.py` 从 `exporters/*/exporter.yaml` 自动生成，请勿手改。
> 修改请编辑对应类型的源清单后执行 `python3 scripts/docgen.py` 重新生成。

- 覆盖 13 个类型 / 23 个表单字段（敏感字段 8 个），按字典序排列（与平台目录模式合并顺序一致）
- 落点（`to`）语义：`env` = 环境变量；`arg` = 经 `args_template` 注入命令行；`var`/`config` = 渲染进 `config.template`（`config` 仅供敏感凭据，配套 `secret_mount` 物化为 Secret）
- 控件为 `password` 的即敏感字段（`sensitive`，二者双向绑定）：只写不回显，落点仅允许 `env`/`config`，禁止进 args
- 字段取值与上游行为（镜像 tag / 端口 / 环境变量 / flag 写法）的核验依据见 [upstream-verification.md](./upstream-verification.md)

## 总览

| 类型 | 显示名 | 镜像 | 端口 | 目标模式 | 参数注入 | 字段数 |
| --- | --- | --- | --- | --- | --- | --- |
| `apache_exporter` | Apache（市场） | `quay.io/lusitaniae/apache-exporter:v1.1.0` | 9117 | single（单目标） | args_template | 1 |
| `blackbox_exporter` | Blackbox 探针（市场） | `quay.io/prometheus/blackbox-exporter:v0.25.0` | 9115 | probe（探针） | 固定 args + config 模板 | 0 |
| `elasticsearch_exporter` | Elasticsearch（市场） | `quay.io/prometheuscommunity/elasticsearch-exporter:v1.9.0` | 9114 | single（单目标） | args_template + env | 5 |
| `kafka_exporter` | Kafka（市场） | `danielqsj/kafka-exporter:v1.9.0` | 9308 | single（单目标） | args_template | 1 |
| `memcached_exporter` | Memcached（市场） | `quay.io/prometheus/memcached-exporter:v0.15.1` | 9150 | single（单目标） | args_template | 1 |
| `mongodb_exporter` | MongoDB（市场） | `percona/mongodb_exporter:0.43.1` | 9216 | single（单目标） | env | 3 |
| `mssql_exporter` | SQL Server（市场） | `awaragi/prometheus-mssql-exporter:v1.3.0` | 4000 | single（单目标） | env | 4 |
| `mysql_exporter` | MySQL（市场 · 多目标） | `quay.io/prometheus/mysqld-exporter:v0.15.1` | 9104 | connection（1:N 多目标） | 固定 args + config 模板 | 2 |
| `nginx_exporter` | NGINX（市场） | `nginx/nginx-prometheus-exporter:1.4.2` | 9113 | single（单目标） | args_template | 2 |
| `node_exporter` | Node Exporter（主机 · DaemonSet） | `quay.io/prometheus/node-exporter:v1.9.1` | 9100 | single（单目标） | 固定 args | 0 |
| `postgresql_exporter` | PostgreSQL（市场） | `prometheuscommunity/postgres-exporter:v0.15.0` | 9187 | single（单目标） | env | 1 |
| `redis_exporter` | Redis（市场） | `oliver006/redis_exporter:v1.66.0` | 9121 | single（单目标） | env | 2 |
| `snmp_exporter` | SNMP 探针（市场） | `quay.io/prometheus/snmp-exporter:v0.26.0` | 9116 | probe（探针） | 固定 args + config 模板 | 1 |

## 参数注入方式对比

### 非敏感参数（地址 / 账号 / 开关）

| 类型 | 字段 | 显示名 | 控件 | 默认值 | 落点 | 上游入口 |
| --- | --- | --- | --- | --- | --- | --- |
| `apache_exporter` | `apache_scrape_uri` | server-status 地址 | text | `http://localhost/server-status?auto` | arg（args_template） | 参数 `--scrape_uri={{.apache_scrape_uri}}` |
| `elasticsearch_exporter` | `es_uri` | 集群地址 | text | `http://elasticsearch:9200` | arg（args_template） | 参数 `--es.uri={{.es_uri}}` |
| `elasticsearch_exporter` | `es_username` | 账号 | text | — | env `ES_USERNAME` | 环境变量 `ES_USERNAME` |
| `elasticsearch_exporter` | `es_ssl_skip_verify` | 跳过 TLS 校验 | select（false / true） | `false` | arg（args_template） | 参数 `{{ if eq .es_ssl_skip_verify "true" }}--es.ssl-skip-verify{{ end }}` |
| `kafka_exporter` | `kafka_servers` | Kafka 地址 | text | `localhost:9092` | arg（args_template） | 参数 `--kafka.server={{.kafka_servers}}` |
| `memcached_exporter` | `memcached_address` | Memcached 地址 | text | `localhost:11211` | arg（args_template） | 参数 `--memcached.address={{.memcached_address}}` |
| `mongodb_exporter` | `mongodb_uri` | MongoDB 地址 | text | — | env `MONGODB_URI` | 环境变量 `MONGODB_URI` |
| `mongodb_exporter` | `mongodb_user` | 账号 | text | — | env `MONGODB_USER` | 环境变量 `MONGODB_USER` |
| `mssql_exporter` | `mssql_host` | SQL Server 主机 | text | — | env `SERVER` | 环境变量 `SERVER` |
| `mssql_exporter` | `mssql_port` | 端口 | number | `1433` | env `PORT` | 环境变量 `PORT` |
| `mssql_exporter` | `mssql_user` | 账号 | text | — | env `USERNAME` | 环境变量 `USERNAME` |
| `mysql_exporter` | `mysql_user` | 数据库账号 | text | `exporter` | var（config 模板插值） | config 模板插值 |
| `nginx_exporter` | `nginx_scrape_uri` | stub_status 地址 | text | `http://127.0.0.1:8080/stub_status` | arg（args_template） | 参数 `--nginx.scrape-uri={{.nginx_scrape_uri}}` |
| `nginx_exporter` | `nginx_plus` | NGINX Plus | select（false / true） | `false` | arg（args_template） | 参数 `{{ if eq .nginx_plus "true" }}--nginx.plus{{ end }}` |
| `redis_exporter` | `redis_addr` | Redis 地址 | text | `redis://localhost:6379` | env `REDIS_ADDR` | 环境变量 `REDIS_ADDR` |

### 敏感字段（凭据）

| 类型 | 字段 | 显示名 | 必填 | 落点 | 上游入口 |
| --- | --- | --- | --- | --- | --- |
| `elasticsearch_exporter` | `es_password` | 密码 | — | env `ES_PASSWORD` | 环境变量 `ES_PASSWORD` |
| `elasticsearch_exporter` | `es_api_key` | API Key（可选） | — | env `ES_API_KEY` | 环境变量 `ES_API_KEY` |
| `mongodb_exporter` | `mongodb_password` | 密码 | — | env `MONGODB_PASSWORD` | 环境变量 `MONGODB_PASSWORD` |
| `mssql_exporter` | `mssql_password` | 密码 | — | env `PASSWORD` | 环境变量 `PASSWORD` |
| `mysql_exporter` | `mysql_password` | 数据库密码 | ✅ | config（config 模板插值） | config 模板插值（Secret 挂载 `/etc/mysql_exporter/.my.cnf`） |
| `postgresql_exporter` | `pg_datasource` | 数据源 DSN | ✅ | env `DATA_SOURCE_NAME` | 环境变量 `DATA_SOURCE_NAME` |
| `redis_exporter` | `redis_password` | Redis 密码 | — | env `REDIS_PASSWORD` | 环境变量 `REDIS_PASSWORD` |
| `snmp_exporter` | `snmp_community` | SNMP 团体字（community） | ✅ | config（config 模板插值） | config 模板插值（Secret 挂载 `/etc/snmp_exporter/snmp.yml`） |

## 逐类型明细

### apache_exporter — Apache（市场）

- 镜像 `quay.io/lusitaniae/apache-exporter:v1.1.0` ｜ 指标端口 `9117` ｜ 目标模式 single（单目标） ｜ 工作负载 deployment（缺省）

> 前置：启用 mod_status，且地址须带 ?auto 后缀（缺后缀只有 up/CPU 指标）。

`args_template`（`{{ … }}` 为表单字段插值）：

```text
--scrape_uri={{.apache_scrape_uri}}
```

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `apache_scrape_uri` | server-status 地址 | text | — | `http://localhost/server-status?auto` | arg（args_template） | 必须带 ?auto 后缀 |

### blackbox_exporter — Blackbox 探针（市场）

- 镜像 `quay.io/prometheus/blackbox-exporter:v0.25.0` ｜ 指标端口 `9115` ｜ 目标模式 probe（探针） ｜ 工作负载 deployment（缺省）

> 探针型：在「探测目标」中登记目标列表（实例级在线增删，只更新抓取配置，零 Pod 滚动）。探测自身 /metrics 抓取始终保留。

固定 `args`：

```text
--config.file=/etc/blackbox_exporter/config.yml
```

配置通道：raw 模板（ConfigMap）→ 挂载 `/etc/blackbox_exporter/config.yml`

<details><summary>config.template</summary>

```text
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      preferred_ip_protocol: ip4
  icmp:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: ip4
  tcp_connect:
    prober: tcp
    timeout: 5s
  dns_lookup:
    prober: dns
    timeout: 5s
    dns:
      query_name: www.prometheus.io
      query_type: A
      valid_rcodes:
        - NOERROR
      validate_answer_rrs:
        fail_if_none_matches_regexp:
          - ".+"
      preferred_ip_protocol: ip4
```

</details>

探针声明：端点 `/probe` ｜ 模块 `http_2xx` / `icmp` / `tcp_connect` / `dns_lookup` ｜ 默认 `http_2xx`

（无表单字段）

### elasticsearch_exporter — Elasticsearch（市场）

- 镜像 `quay.io/prometheuscommunity/elasticsearch-exporter:v1.9.0` ｜ 指标端口 `9114` ｜ 目标模式 single（单目标） ｜ 工作负载 deployment（缺省）

> 凭据必须走环境变量，不要内联进 URI（URL 编码坑）。

`args_template`（`{{ … }}` 为表单字段插值）：

```text
--es.uri={{.es_uri}}
{{ if eq .es_ssl_skip_verify "true" }}--es.ssl-skip-verify{{ end }}
```

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `es_uri` | 集群地址 | text | — | `http://elasticsearch:9200` | arg（args_template） | host:port 形态 |
| `es_username` | 账号 | text | — | — | env `ES_USERNAME` | — |
| `es_password` | 密码 | password（敏感） | — | — | env `ES_PASSWORD` | — |
| `es_api_key` | API Key（可选） | password（敏感） | — | — | env `ES_API_KEY` | 高级字段（折叠展示）；提供后以 API Key 认证（v1.9.0 无对应 flag，仅环境变量生效；勿与账号密码同时填写） |
| `es_ssl_skip_verify` | 跳过 TLS 校验 | select（false / true） | — | `false` | arg（args_template） | 高级字段（折叠展示） |

### kafka_exporter — Kafka（市场）

- 镜像 `danielqsj/kafka-exporter:v1.9.0` ｜ 指标端口 `9308` ｜ 目标模式 single（单目标） ｜ 工作负载 deployment（缺省）

`args_template`（`{{ … }}` 为表单字段插值）：

```text
--kafka.server={{.kafka_servers}}
```

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `kafka_servers` | Kafka 地址 | text | — | `localhost:9092` | arg（args_template） | 单条 --kafka.server 注入（KAFKA_SERVERS 环境变量不被该镜像读取）；多 broker 场景需扩展本类型 args_template（--kafka.server 可重复传） |

### memcached_exporter — Memcached（市场）

- 镜像 `quay.io/prometheus/memcached-exporter:v0.15.1` ｜ 指标端口 `9150` ｜ 目标模式 single（单目标） ｜ 工作负载 deployment（缺省）

`args_template`（`{{ … }}` 为表单字段插值）：

```text
--memcached.address={{.memcached_address}}
```

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `memcached_address` | Memcached 地址 | text | — | `localhost:11211` | arg（args_template） | — |

### mongodb_exporter — MongoDB（市场）

- 镜像 `percona/mongodb_exporter:0.43.1` ｜ 指标端口 `9216` ｜ 目标模式 single（单目标） ｜ 工作负载 deployment（缺省）

> 凭据走环境变量（官方明确命令行 flag 会经 ps 泄漏）；建议为监控账号只授予 clusterMonitor 角色。

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `mongodb_uri` | MongoDB 地址 | text | — | — | env `MONGODB_URI` | mongodb://host:27017（凭据可用下方账号密码单独提供） |
| `mongodb_user` | 账号 | text | — | — | env `MONGODB_USER` | — |
| `mongodb_password` | 密码 | password（敏感） | — | — | env `MONGODB_PASSWORD` | — |

### mssql_exporter — SQL Server（市场）

- 镜像 `awaragi/prometheus-mssql-exporter:v1.3.0` ｜ 指标端口 `4000` ｜ 目标模式 single（单目标） ｜ 工作负载 deployment（缺省）

> 数据库侧需授权：GRANT VIEW ANY DEFINITION、GRANT VIEW SERVER STATE。

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `mssql_host` | SQL Server 主机 | text | ✅ | — | env `SERVER` | — |
| `mssql_port` | 端口 | number | — | `1433` | env `PORT` | — |
| `mssql_user` | 账号 | text | — | — | env `USERNAME` | — |
| `mssql_password` | 密码 | password（敏感） | — | — | env `PASSWORD` | — |

### mysql_exporter — MySQL（市场 · 多目标）

- 镜像 `quay.io/prometheus/mysqld-exporter:v0.15.1` ｜ 指标端口 `9104` ｜ 目标模式 connection（1:N 多目标） ｜ 工作负载 deployment（缺省）

> 多目标连接型：账号/密码为本实例全部目标共享；监控目标（host:port）在 Targets 页统一管理，增删目标只更新抓取配置，修改密码会触发 Pod 滚动更新。上游 mysqld-exporter 已停止维护（多目标能力需 v0.15+）。数据库侧需 DBA 预先建号授权：GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'%'; 并设 MAX_USER_CONNECTIONS 3。平台只管 exporter，不管被监控的 MySQL 本身。注意：exporter 自身 /metrics 端点未绑定目标，其 mysql_up=0 为预期（各目标的 mysql_up 见 Targets 页 instance 维度）。

固定 `args`：

```text
--config.my-cnf=/etc/mysql_exporter/.my.cnf
```

配置通道：raw 模板（物化为 Secret）→ 挂载 `/etc/mysql_exporter/.my.cnf`

<details><summary>config.template</summary>

```text
[client]
user = {{ .Fields.mysql_user }}
password = {{ .mysql_password }}
```

</details>

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `mysql_user` | 数据库账号 | text | — | `exporter` | var（config 模板插值） | 本实例全部监控目标共享的连接账号 |
| `mysql_password` | 数据库密码 | password（敏感） | ✅ | — | config（config 模板插值） | 只写不回显 · 加密存储 · 物化为 Secret（修改将触发滚动更新） |

### nginx_exporter — NGINX（市场）

- 镜像 `nginx/nginx-prometheus-exporter:1.4.2` ｜ 指标端口 `9113` ｜ 目标模式 single（单目标） ｜ 工作负载 deployment（缺省）

> 前置：被监控端开启 stub_status（开源版）或 /api（NGINX Plus）。

`args_template`（`{{ … }}` 为表单字段插值）：

```text
--nginx.scrape-uri={{.nginx_scrape_uri}}
{{ if eq .nginx_plus "true" }}--nginx.plus{{ end }}
```

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `nginx_scrape_uri` | stub_status 地址 | text | — | `http://127.0.0.1:8080/stub_status` | arg（args_template） | — |
| `nginx_plus` | NGINX Plus | select（false / true） | — | `false` | arg（args_template） | 高级字段（折叠展示） |

### node_exporter — Node Exporter（主机 · DaemonSet）

- 镜像 `quay.io/prometheus/node-exporter:v1.9.1` ｜ 指标端口 `9100` ｜ 目标模式 single（单目标） ｜ 工作负载 daemonset（每节点）
- hostPath 挂载：`/proc` → `/host/proc`
- hostPath 挂载：`/sys` → `/host/sys`
- 污点容忍：`node-role.kubernetes.io/control-plane`、`node-role.kubernetes.io/master`（NoSchedule）
- 资源：requests `20m` cpu / `32Mi` memory，limits `200m` cpu / `128Mi` memory
- 抓取间隔：`15s`

固定 `args`：

```text
--path.procfs=/host/proc
--path.sysfs=/host/sys
```

（无表单字段）

### postgresql_exporter — PostgreSQL（市场）

- 镜像 `prometheuscommunity/postgres-exporter:v0.15.0` ｜ 指标端口 `9187` ｜ 目标模式 single（单目标） ｜ 工作负载 deployment（缺省）

> 数据库侧需建号并授予监控只读（pg_monitor 角色）。

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `pg_datasource` | 数据源 DSN | password（敏感） | ✅ | — | env `DATA_SOURCE_NAME` | postgresql://user:password@host:5432/database?sslmode=disable |

### redis_exporter — Redis（市场）

- 镜像 `oliver006/redis_exporter:v1.66.0` ｜ 指标端口 `9121` ｜ 目标模式 single（单目标） ｜ 工作负载 deployment（缺省）

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `redis_addr` | Redis 地址 | text | — | `redis://localhost:6379` | env `REDIS_ADDR` | — |
| `redis_password` | Redis 密码 | password（敏感） | — | — | env `REDIS_PASSWORD` | — |

### snmp_exporter — SNMP 探针（市场）

- 镜像 `quay.io/prometheus/snmp-exporter:v0.26.0` ｜ 指标端口 `9116` ｜ 目标模式 probe（探针） ｜ 工作负载 deployment（缺省）

> 探针型：目标列表实例级在线增删（零 Pod 滚动）。snmp.yml 含团体字等凭据，整文件以 Secret 挂载（ConfigMap 无凭据）；模块段为 generator 产物示例，深度定制经商店源清单覆盖。

固定 `args`：

```text
--config.file=/etc/snmp_exporter/snmp.yml
```

配置通道：raw 模板（物化为 Secret）→ 挂载 `/etc/snmp_exporter/snmp.yml`

<details><summary>config.template</summary>

```text
modules:
  if_mib:
    walk:
      - 1.3.6.1.2.1.2.2.1.1
      - 1.3.6.1.2.1.2.2.1.2
      - 1.3.6.1.2.1.2.2.1.3
      - 1.3.6.1.2.1.2.2.1.5
      - 1.3.6.1.2.1.2.2.1.6
      - 1.3.6.1.2.1.2.2.1.7
      - 1.3.6.1.2.1.2.2.1.8
      - 1.3.6.1.2.1.2.2.1.10
      - 1.3.6.1.2.1.2.2.1.14
      - 1.3.6.1.2.1.2.2.1.16
    metrics:
      - name: ifIndex
        oid: 1.3.6.1.2.1.2.2.1.1
        type: gauge
      - name: ifDescr
        oid: 1.3.6.1.2.1.2.2.1.2
        type: DisplayString
        indexes:
          - labelname: ifIndex
            type: gauge
      - name: ifType
        oid: 1.3.6.1.2.1.2.2.1.3
        type: gauge
        indexes:
          - labelname: ifIndex
            type: gauge
        lookups:
          - labels:
              - ifIndex
              - ifDescr
            labelname: ifDescr
            oid: 1.3.6.1.2.1.2.2.1.2
      - name: ifSpeed
        oid: 1.3.6.1.2.1.2.2.1.5
        type: gauge
        indexes:
          - labelname: ifIndex
            type: gauge
      - name: ifPhysAddress
        oid: 1.3.6.1.2.1.2.2.1.6
        type: PhysAddress48
        indexes:
          - labelname: ifIndex
            type: gauge
      - name: ifAdminStatus
        oid: 1.3.6.1.2.1.2.2.1.7
        type: EnumAsStateSet
        enum_values:
          1: up
          2: down
          3: testing
          4: unknown
          5: dormant
        indexes:
          - labelname: ifIndex
            type: gauge
      - name: ifOperStatus
        oid: 1.3.6.1.2.1.2.2.1.8
        type: EnumAsStateSet
        enum_values:
          1: up
          2: down
          3: testing
          4: unknown
          5: dormant
          6: notPresent
          7: lowerLayerDown
        indexes:
          - labelname: ifIndex
            type: gauge
      - name: ifInOctets
        oid: 1.3.6.1.2.1.2.2.1.10
        type: counter
        indexes:
          - labelname: ifIndex
            type: gauge
      - name: ifInErrors
        oid: 1.3.6.1.2.1.2.2.1.14
        type: counter
        indexes:
          - labelname: ifIndex
            type: gauge
      - name: ifOutOctets
        oid: 1.3.6.1.2.1.2.2.1.16
        type: counter
        indexes:
          - labelname: ifIndex
            type: gauge
  sysuptime:
    get:
      - 1.3.6.1.2.1.1.3.0
    metrics:
      - name: sysUpTime
        oid: 1.3.6.1.2.1.1.3
        type: gauge
        help: The time (in hundredths of a second) since the network management portion of the system was last re-initialized.
auths:
  public_v2:
    community: {{ .snmp_community }}
    version: 2
```

</details>

探针声明：端点 `/snmp` ｜ 模块 `if_mib` / `sysuptime` ｜ 默认 `if_mib` ｜ 认证 `public_v2`

表单字段：

| 字段 | 显示名 | 控件 | 必填 | 默认值 | 落点 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| `snmp_community` | SNMP 团体字（community） | password（敏感） | ✅ | — | config（config 模板插值） | 渲染进 snmp.yml auth 段，整文件以 Secret 挂载，任何 ConfigMap / 预览不出现明文 |
