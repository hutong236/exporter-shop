# REQ-1 proposal — node-exporter-external（直连原生端点型首个条目）

## 需求背景

Issue #1：exporter-shop 商店目录自平台 REQ-181（直连原生端点机制）上线后，首次接入「免部署登记观测」形态——node_exporter 已由运维在平台外独立部署（systemd/Ansible 等纳管）的场景，平台无需重复部署采集器，仅登记抓取目标：vmagent 直抓、实例进台账、健康轮询/采集确认/Grafana 与部署型实例同权，实例物化产物仅为单个 VMStaticScrape（零工作负载）。

本 PR 落地内容：

1. 新增目录首个直连型条目 `exporters/node-exporter-external/exporter.yaml`（name 与目录名一致，类型 key `node-exporter-external`）。
2. 同步本地校验脚本 `scripts/validate.py`：name 正则放宽至平台 REQ-181 口径、`workload` 枚举新增 `none`（门控仅 endpoint 型可用）、`target_mode` 枚举新增 `endpoint`、新增 endpoint 校验矩阵与 `target_contract` 最小校验（逐条镜像平台 registry.go 现行逻辑）。
3. 同步文档生成脚本 `scripts/docgen.py`：endpoint 目标模式标签、none 免部署工作负载标签（含平台归一语义）、空镜像 `—` 渲染、`target_contract` 明细渲染；既有 13 类渲染逐字节不变。
4. 重新生成 `docs/exporter-params.md`，更新 `README.md`（目录表第 14 行、计数、name 正则表述、直连型要点）与 `docs/upstream-verification.md`（2026-10-09 核验小节 + 汇总行）。
5. 本仓库首次引入 openspec：新建 `openspec/specs/exporter-catalog/spec.md` 主规格（ADDED 全量落地），决策史存于 `openspec/changes/archive/REQ-1/`。

## Gate A 拍板（五项）

1. **类型 key 用连字符命名**：`node-exporter-external`（非下划线变体），与平台 REQ-181 预置直连型命名风格一致，推动本地 name 正则放宽为 `^[a-z](?:[a-z0-9_-]*[a-z0-9_])?$` 并与平台同步。
2. **openspec/specs/exporter-catalog/spec.md 随本 PR 落地**：不做延迟同步，主规格与代码同 PR 合入。
3. **demo 辅助脚本（up/serve/down）不入库**：仅用于平台集群实测的临时脚手架，不进入商店目录仓库。
4. **条目最小声明**：仅 `name` / `label` / `preface` / `target_mode` / `metrics_port` / `target_contract`，省略 `scrape.interval` 与 `health_path`（后者平台加载期统一归一为 `/metrics`，声明即死键）。
5. **不携带 pr-checks 工作流文件**：本 PR 不混入 CI 工作流变更，仓库 CI 维持既有 `.github/workflows/manifest.yml`。

## 关联

- 平台机制：hutong-project-monitor REQ-181（`registry.go` normalizeEndpointType / validateEndpointType / validateTargetContract，name 正则放宽）。
- 上游核验：`docs/upstream-verification.md` 2026-10-09 小节（端口 9100 与 /metrics 沿用 node_exporter 上游口径；REQ-181 机制经平台集群实测：拉取成功、vmagent 双目标 up、采集确认 2/2）。
