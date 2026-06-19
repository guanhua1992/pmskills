# 画像门禁（Profile Gates）

画像门禁在基础 PRD 质量门禁之上，叠加产品类型专属的阻断项。

定稿前画像必须是一个具体值（`general`、`b2b`、`b2c` 或 `ai-data`）。仍为 `auto` 的画像是严格校验的阻断项——请先在模块计划中确定它。

## General（通用软件）

若缺失下列内容，严格校验应阻断：

- 平台或兼容性目标（设备、浏览器、OS 或运行时）；
- 支持或运维影响。

有用的标记与术语：

- `Platform`
- `Compatibility`
- `Support`
- `Operations`

## B2B

若缺失下列内容，严格校验应阻断：

- 映射"角色、操作、数据范围、限制"的权限矩阵；
- 审批/状态工作流，或显式声明无需审批；
- 审计轨迹，或显式声明无需审计；
- 数据范围、租户隔离或归属边界；
- 在相关处说明导出、批量操作或管理员行为。

有用的标记与术语：

- `Permission Matrix`（权限矩阵）
- `Role`（角色）
- `Operation`（操作）
- `Data Scope`（数据范围）
- `Approval`（审批）
- `Status`（状态）
- `Audit`（审计）
- `Tenant`（租户）

## B2C

若缺失下列内容，严格校验应阻断：

- 漏斗或转化指标；
- 隐私或同意行为；
- 空状态与恢复行为；
- 兼容性目标，如设备、浏览器、App 版本或平台；
- 在相关处考虑滥用、欺诈、风险或安全。

有用的标记与术语：

- `Funnel`（漏斗）
- `Conversion`（转化）
- `Privacy`（隐私）
- `Consent`（同意）
- `Empty State`（空状态）
- `Compatibility`（兼容性）
- `Abuse`（滥用）
- `Risk`（风险）

## AI/Data

若缺失下列内容，严格校验应阻断：

- 评估数据集或评估方法；
- 置信度、阈值或质量分；
- 人工兜底或人工复核流程；
- 监控与漂移/质量告警；
- 成本与延迟目标；
- 数据血缘、新鲜度或来源质量。

有用的标记与术语：

- `Evaluation`（评估）
- `Dataset`（数据集）
- `Confidence`（置信度）
- `Threshold`（阈值）
- `Human Review`（人工复核）
- `Fallback`（兜底）
- `Monitoring`（监控）
- `Cost`（成本）
- `Latency`（延迟）
- `Lineage`（血缘）
- `Freshness`（新鲜度）
