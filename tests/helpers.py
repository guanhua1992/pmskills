from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "write-production-prd" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from assemble_prd import assemble  # noqa: E402
from common import REVIEW_FILES, SHAPING_STAGES, load_json, write_json_atomic  # noqa: E402
from init_workspace import initialize  # noqa: E402


BASE_VALID_MODULE = """<!-- module-status: confirmed -->
<!-- sources: SRC-001 -->

## Document Control [PRD-CONTROL]
- Owner: Product
- Audience: Engineering, Design, QA

## Background [PRD-BACKGROUND]
SRC-001 confirms the problem and why now.

## Goals [PRD-GOALS]
- GOAL-001: Reduce manual work from 20 minutes to 5 minutes.

## Users [PRD-USERS]
- SCN-001: A confirmed primary user scenario.

## Scope [PRD-SCOPE]
- In scope: the confirmed capability.
- Out of scope: unrelated capabilities.

## Flows [PRD-FLOWS]
The primary flow and alternate flow are defined.

## Functional Requirements [PRD-REQUIREMENTS]

### FR-001: Complete the primary action
- Priority: P0
- Traces To: GOAL-001, SCN-001, SRC-001
- Business Rules: BR-001
- Requirement: The system must complete the primary action after valid confirmation.
- Acceptance Criteria:
  - AC-001: Given valid input, when the user confirms, then the completed result is visible.

## Business Rules [PRD-RULES]
- BR-001: Confirmation requires valid input.

## Exceptions [PRD-EXCEPTIONS]
- Invalid input blocks confirmation and identifies the invalid field.

## Data [PRD-DATA]
- Store the confirmed result and its owner.

## Permissions [PRD-PERMISSIONS]

### Permission Matrix

| Role | Operation | Data Scope | Allowed? | Audit? |
|---|---|---|---|---|
| Owner | Complete primary action | Own workspace | yes | Audit log recorded |

Approval Status workflow: draft -> submitted -> approved. Tenant data boundary is respected.

## Integrations [PRD-INTEGRATIONS]
- Not applicable because the confirmed scope has no external integration.

## Non-Functional Requirements [PRD-NFR]

### NFR-001: Response time
- Category: performance
- Traces To: GOAL-001, SRC-001
- Target: p95 response time <= 500 ms.
- Verification: production-like load test.

## Metrics [PRD-METRICS]
- Measure completion rate, error rate, Funnel conversion, and guardrail metric.
- Privacy and Consent behavior is explicit.
- Empty State recovery is available.
- Compatibility target includes desktop browser and mobile browser.
- Abuse and Risk handling are owned by operations.

## Release [PRD-RELEASE]
- Release to 10%, 50%, and 100%; disable the feature to roll back.

## Acceptance [PRD-ACCEPTANCE]
- All P0 requirements pass normal, error, and permission tests.

## Risks [PRD-RISKS]
- Risk and mitigation are owned by Product.

## Vibe Coding Spec [PRD-VIBE-SPEC]

| Item | Specification |
|---|---|
| Build intent | Build the confirmed primary capability. |
| Users | Primary owner users; excluded users cannot operate. |
| Modules | UI module, workflow module, data module. |
| Inputs | Valid user input, permission context, existing data. |
| Outputs | Completed result, persisted data, monitoring event. |
| Boundaries | No unrelated capability or unconfirmed product policy. |
| Done criteria | AC-001 passes and NFR-001 target is met. |
| AI non-decisions | AI must not decide permissions, pricing, compliance, or retention. |

## Traceability [PRD-TRACEABILITY]
| Requirement | Goal | Scenario | Evidence | Acceptance |
|---|---|---|---|---|
| FR-001 | GOAL-001 | SCN-001 | SRC-001 | AC-001 |
"""


AI_DATA_APPENDIX = """

## AI/Data Profile Coverage

- Evaluation method uses a representative Dataset.
- Confidence Threshold is defined before automated action.
- Human Review and Fallback flow handles low confidence.
- Monitoring Alert watches quality Drift.
- Cost and Latency targets are tracked.
- Lineage, Freshness, and Source Quality are recorded.
"""


CN_VALID_MODULE = """<!-- module-status: confirmed -->
<!-- sources: SRC-001 -->

## 文档控制 [PRD-CONTROL]
- 负责人：产品
- 受众：工程、设计、QA

## 背景 [PRD-BACKGROUND]
SRC-001 已确认问题与为何现在做。

## 目标 [PRD-GOALS]
- GOAL-001：将手动耗时从 20 分钟降到 5 分钟。

## 用户 [PRD-USERS]
- SCN-001：一个已确认的主要用户场景。

## 范围 [PRD-SCOPE]
- 范围内：已确认能力。
- 范围外：无关能力。

## 流程 [PRD-FLOWS]
主流程与备选流程已定义。

## 功能需求 [PRD-REQUIREMENTS]

### FR-001: 完成主操作
- 优先级：P0
- 追踪至：GOAL-001, SCN-001, SRC-001
- 业务规则：BR-001
- 需求：系统必须在有效确认后完成主操作。
- 验收标准：
  - AC-001: 假设输入有效，当用户确认，则可见已完成结果。

## 业务规则 [PRD-RULES]
- BR-001：确认需要有效输入。

## 异常 [PRD-EXCEPTIONS]
- 非法输入阻止确认并标出错误字段。

## 数据 [PRD-DATA]
- 存储已完成结果及其归属。

## 权限 [PRD-PERMISSIONS]

### 权限矩阵
| 角色 | 操作 | 数据范围 | 是否允许 | 是否审计 |
|---|---|---|---|---|
| 负责人 | 完成主操作 | 本人工作区 | 是 | 记录审计日志 |

## 集成 [PRD-INTEGRATIONS]
- 不适用，因为已确认范围无外部集成。

## 非功能需求 [PRD-NFR]

### NFR-001: 响应时间
- 类别：performance
- 追踪至：GOAL-001, SRC-001
- 目标：p95 响应时间 <= 500 ms。
- 验证：类生产环境压测。

## 指标 [PRD-METRICS]
- 度量完成率、错误率与护栏指标。

## 发布 [PRD-RELEASE]
- 灰度到 10%、50%、100%；平台与浏览器兼容性已确认；可禁用功能以回滚。

## 验收 [PRD-ACCEPTANCE]
- 所有 P0 需求通过正常、异常、权限测试。

## 风险 [PRD-RISKS]
- 风险与缓解由产品负责；运营负责支持影响。

## Vibe Coding 规格 [PRD-VIBE-SPEC]
| 条目 | 规格 |
|---|---|
| 构建意图 | 构建已确认的主能力。 |
| 用户 | 主要负责人用户；被排除用户不可操作。 |
| 模块 | UI 模块、流程模块、数据模块。 |
| 输入 | 有效用户输入、权限上下文、既有数据。 |
| 输出 | 已完成结果、持久化数据、监控事件。 |
| 边界 | 不含无关能力或未确认产品策略。 |
| 完成标准 | AC-001 通过且 NFR-001 目标达成。 |
| AI 不得决策 | AI 不得决定权限、定价、合规或留存。 |

## 可追溯性 [PRD-TRACEABILITY]
| 需求 | 目标 | 场景 | 证据 | 验收 |
|---|---|---|---|---|
| FR-001 | GOAL-001 | SCN-001 | SRC-001 | AC-001 |
"""


def create_workspace(
    root: Path,
    name: str = "Example",
    depth: str = "standard",
    profile: str = "general",
) -> Path:
    workspace, created = initialize(name, root, depth, profile)
    assert created
    return workspace


def make_valid_workspace(
    root: Path,
    name: str = "Example",
    depth: str = "standard",
    profile: str = "general",
    module_text: str | None = None,
) -> Path:
    workspace = create_workspace(root, name, depth, profile)
    source_notes = workspace / "inputs" / "source-notes.md"
    source_notes.write_text(
        source_notes.read_text(encoding="utf-8").replace("[TO CONFIRM]", "Confirmed"),
        encoding="utf-8",
    )
    for stage in SHAPING_STAGES:
        path = workspace / "shaping" / f"{stage}.md"
        cleaned = (
            path.read_text(encoding="utf-8")
            .replace("[TO CONFIRM]", "Confirmed")
            .replace("stage-status: draft", "stage-status: confirmed")
        )
        path.write_text(cleaned, encoding="utf-8")
    for review in REVIEW_FILES:
        path = workspace / "review" / f"{review}.md"
        cleaned = (
            path.read_text(encoding="utf-8")
            .replace("[TO CONFIRM]", "Confirmed")
            .replace("| Blocking decision | Confirmed |", "| Blocking decision | no |")
            .replace("| RA-001 | Confirmed | Confirmed | yes | open |", "| RA-001 | Confirmed | Confirmed | no | closed |")
            .replace("| RA-001 | self-check | Confirmed | Confirmed | yes | open | Confirmed |", "| RA-001 | self-check | Confirmed | Confirmed | no | closed | Confirmed |")
        )
        path.write_text(cleaned, encoding="utf-8")
    module_name = "01-complete"
    module_path = workspace / "prd" / "modules" / f"{module_name}.md"
    base = module_text if module_text is not None else BASE_VALID_MODULE
    content = base + (AI_DATA_APPENDIX if profile == "ai-data" else "")
    module_path.write_text(content, encoding="utf-8")
    metadata = load_json(workspace / "workspace.json")
    metadata["confirmed_stages"] = SHAPING_STAGES
    metadata["confirmed_modules"] = [module_name]
    metadata["review_status"] = {review: "confirmed" for review in REVIEW_FILES}
    write_json_atomic(workspace / "workspace.json", metadata)
    assemble(workspace)
    return workspace


def add_duplicate_requirement(workspace: Path) -> None:
    metadata = load_json(workspace / "workspace.json")
    module_name = metadata["confirmed_modules"][0]
    module_path = workspace / "prd" / "modules" / f"{module_name}.md"
    text = module_path.read_text(encoding="utf-8")
    duplicate = """
### FR-001: Duplicate definition
- Priority: P1
- Traces To: GOAL-001, SCN-001, SRC-001
- Business Rules: BR-001
- Requirement: The system must reject duplicate definitions.
- Acceptance Criteria:
  - AC-002: Given a duplicate definition, when validation runs, then validation fails.
"""
    module_path.write_text(
        text.replace("## Business Rules", duplicate + "\n## Business Rules"),
        encoding="utf-8",
    )
    assemble(workspace)
