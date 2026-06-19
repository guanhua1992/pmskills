# PRD 结构契约（PRD Structure Contract）

## 稳定章节标记

默认用中文写叙述（仅在用户明确要求时切换）。叙述标题与字段标签可本地化（例如 `优先级`、`追踪至`、`业务规则`、`验收标准`，以及 `假设/当/则` 验收句式——全角 `：` 可接受），但以下标记、ID、frontmatter 键与状态值必须保持 ASCII，以保证确定性校验生效：

| 标记 | 必需内容 |
|---|---|
| `[PRD-CONTROL]` | 文档状态、负责人、受众、修订记录 |
| `[PRD-BACKGROUND]` | 背景、问题、为何现在做、证据 |
| `[PRD-GOALS]` | 目标、基线、目标值、护栏 |
| `[PRD-USERS]` | 角色、用户、干系人、JTBD |
| `[PRD-SCOPE]` | 范围内、范围外、暂缓 |
| `[PRD-FLOWS]` | 主流程、备选流程、异常流程与状态 |
| `[PRD-REQUIREMENTS]` | 功能需求 |
| `[PRD-RULES]` | 业务规则与状态流转 |
| `[PRD-EXCEPTIONS]` | 错误、空、边界、并发行为 |
| `[PRD-DATA]` | 字段、数据生命周期、保留、迁移 |
| `[PRD-PERMISSIONS]` | 角色、操作、数据权限 |
| `[PRD-INTEGRATIONS]` | API、外部系统、失败行为 |
| `[PRD-NFR]` | 性能、安全、隐私、可用性、可访问性 |
| `[PRD-METRICS]` | 指标树（`MET-*` 北极星/输入指标、`GUARD-*` 护栏）、埋点，以及 `EXP-*` 实验/验证计划；参见 `references/metrics-playbook.md` |
| `[PRD-RELEASE]` | 灰度、兼容性、运维、回滚 |
| `[PRD-ACCEPTANCE]` | 端到端验收与评审标准 |
| `[PRD-RISKS]` | 风险、缓解、依赖、待决策 |
| `[PRD-VIBE-SPEC]` | AI 开发意图、模块、输入、输出、边界、完成标准、非决策项 |
| `[PRD-TRACEABILITY]` | 目标/场景/来源/需求/验收 映射 |

最终 PRD 要用上每一个标记。当某节确实不相关时，写 `Not applicable because ...` 或 `不适用，因为...`；绝不悄悄省略。

## 需求格式

每个功能需求都使用以下可解析格式：

```markdown
### FR-001: 简短需求标题

- 优先级：P0
- 追踪至：GOAL-001, SCN-001, SRC-001
- 业务规则：BR-001
- 需求：系统必须……
- 验收标准：
  - AC-001: 假设……，当……，则……
  - AC-002: 假设……，当……，则……
```

> 英文字段标签（`Priority` / `Traces To` / `Business Rules` / `Acceptance Criteria`）与英文验收句式（Given/When/Then）同样被校验器接受。

规则：

- 每个 `FR-*` 只描述一个可观察行为。
- 使用"必须"（must）或同等无歧义的本地化表述。
- 避免使用诸如"快速、直观、适当、通常、及时、友好"等含糊词，除非已量化。
- 验收标准必须可观察、可验证。
- 在相关处覆盖正常、备选、异常、边界、权限与状态行为。
- 不要规定架构，除非它是一条已确认的约束。

## 非功能需求格式

```markdown
### NFR-001: 响应时间

- 类别：performance
- 追踪至：GOAL-002, SRC-004
- 目标：在 200 requests/second 下 p95 响应时间 <= 500 ms
- 验证：在类生产环境做压测
```

若不相关：

```markdown
### NFR-004: 离线模式

- 不适用，因为：已确认的范围是仅在线的后台管理流程。
```

## 模块计划

推荐的模块顺序：

1. `01-context-and-scope.md`
2. `02-experience-and-functional-requirements.md`
3. `03-data-permissions-and-integrations.md`
4. `04-quality-release-and-acceptance.md`
5. `05-decisions-and-traceability.md`

每个模块以这两行开头：

```markdown
<!-- module-status: draft -->
<!-- sources: SRC-001, SRC-002 -->
```

只有在用户明确确认后，才把 `module-status` 改为 `confirmed`，并把其文件名主干记录到 `workspace.json.confirmed_modules`。

## 可追溯性矩阵

最终矩阵必须映射：

| 需求 | 目标 | 场景 | 证据 | 验收 |
|---|---|---|---|---|
| FR-001 | GOAL-001 | SCN-001 | SRC-001 | AC-001, AC-002 |

每个 `FR-*` 必须至少有一个目标、场景、来源与验收标准。每个 `AC-*` 必须恰好归属于一个需求。
