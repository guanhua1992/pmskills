---
name: write-production-prd
description: Analyze product requirements and produce production-ready Product Requirements Documents (PRDs) through evidence collection, product-manager requirement analysis, Vibe Coding intent engineering, staged shaping, controlled module approval, review handoff, safe assembly, and deterministic quality gates. Use when the assistant must clarify a product idea, turn raw requests or an existing codebase into a PRD, define functional and non-functional requirements, prepare a requirement review, improve an incomplete PRD, or produce an AI-development-ready product specification. Works on any agent platform (Claude Code, Codex, and other tools). Do not use to implement the product after the PRD is approved.
---

# 编写生产级 PRD

产出一份基于证据的 PRD，让工程、设计、QA、运维和干系人无需猜测即可评审和执行。要像一名资深产品开发经理那样工作：验证需求是否真实、把产品意图定义到足以支撑 AI 辅助开发的程度，并保留不确定性而不是臆造事实。

## 运行脚本（任意平台）

本技能可在任意 Agent 平台运行（Claude Code、Codex 及其他工具）。脚本仅依赖 Python 3 标准库。

先确定本技能目录（包含本 `SKILL.md` 的文件夹）的绝对路径，存为 `SKILL_DIR`，之后所有脚本都通过它调用：

```bash
SKILL_DIR="<本技能目录的绝对路径>"
python3 "$SKILL_DIR/scripts/init_workspace.py" --help
```

工作区会创建在当前工作目录（或 `--root` 指定处），它与 `SKILL_DIR` 相互独立。不要假设当前目录就是技能目录。

## 开始或恢复

1. 在当前目录、其上级目录、以及同名的同级工作区中查找 `workspace.json`。
2. 找到已有工作区则恢复它。绝不在一个工作区内部再创建工作区。
3. 否则初始化一个（PRD 默认输出中文；用 `--output-language` 可覆盖）：

```bash
python3 "$SKILL_DIR/scripts/init_workspace.py" --name "<产品或功能名>" --depth auto --product-profile auto
```

4. 开展工作流之前，先读 `references/workflow-contract.md`。
5. 只读取当前阶段所需的额外参考文档：
   - PRD 结构与模块格式：`references/prd-contract.md`
   - 深度与产品画像专项覆盖：`references/depth-and-profiles.md`
   - 发现与假设验证：`references/discovery-playbook.md`
   - 指标树与实验验证：`references/metrics-playbook.md`
   - 产品经理需求分析：`references/pm-analysis-playbook.md`
   - 面向 AI 开发的 Vibe Coding 意图工程：`references/vibe-product-manager.md`
   - 需求评审交接：`references/review-playbook.md`
   - 画像专项门禁：`references/profile-gates.md`
   - 语义质量评审清单：`references/semantic-quality-rubric.md`
   - 评分与定稿规则：`references/quality-gate.md`
   - 质量基准样例：`references/complete-example.md`

## 不可妥协的铁律

- PRD 叙述与字段标签默认写中文；仅当用户明确要求其他语言时才切换（`workspace.json.output_language` 记录该选择）。
- 无论叙述用什么语言，机器解析的骨架一律保持 ASCII：稳定的章节标记 `[PRD-*]`，稳定 ID 如 `SRC-001`、`ASM-001`、`GOAL-001`、`SCN-001`、`FR-001`、`NFR-001`、`AC-001`、`BR-001`、`MET-001`、`GUARD-001`、`EXP-001`，frontmatter 键，以及状态值（`draft`、`review-ready`、`approved`）。本地化字段标签（如 `优先级`、`追踪至`、`业务规则`、`验收标准`）和 `假设/当/则` 验收句式，校验器均已支持。
- 代码、文档、图片、链接、数据、用户口述，在被当作事实使用前，先登记为证据。
- 把缺乏支撑的结论标为假设，把未知项标为 `[待确认]` 或 `[TO CONFIRM]`。
- 暴露相互冲突的证据并让用户裁决。绝不私自选边。
- 每轮最多问 3-5 个实质性问题。
- 每轮只完成一个塑形阶段或一个 PRD 模块，然后请求确认。
- 未经用户明确确认，不得把某阶段或模块标记为已确认。
- 在产出任何面向 AI 开发的交接物之前，先定义好产品意图、系统边界、输入、输出、约束与完成标准。
- 不要实现该功能或产品。在 PRD 批准与交接处停止。

## 工作流

### 1. 塑形需求

按顺序完成并确认以下文件：

1. `shaping/00-discovery.md`
2. `shaping/00-intake.md`
3. `shaping/01-value-and-truth.md`
4. `shaping/02-jtbd.md`
5. `shaping/03-business-rules.md`
6. `shaping/04-system-intent.md`
7. `shaping/05-scope-and-version.md`
8. `shaping/06-shaped-brief.md`

存在未解决的关键问题时不得继续推进。未解决的非关键问题要保持可见，并标注负责人与解决条件。

### 2. 规划 PRD

依据 `references/depth-and-profiles.md` 选定 `brief`、`standard` 或 `enterprise`。提出 `prd/module-plan.md`，解释所选深度/画像，并等待确认。
确认后，把选定的深度与画像记录到 `workspace.json`。

### 3. 编写已确认的模块

在 `prd/modules/` 下一次只写一个文件。每个模块必须：

- 引用 `SRC-*` 证据，或显式标注为假设；
- 保留稳定的需求与验收 ID；
- 在相关处覆盖正常、备选、异常、空、权限与边界行为；
- 标明业务规则、状态流转、数据影响与依赖；
- 当该模块将指导 AI 辅助实现时，包含 Vibe Coding 约束；
- 进入下一个模块前先被确认。

### 4. 安全装配

确认过的模块就绪后：

```bash
python3 "$SKILL_DIR/scripts/assemble_prd.py" <workspace>
```

装配器会拒绝覆盖被手动改过的 `prd/PRD.md`。请解决其报告的冲突，而不是强行覆盖。

### 5. 校验与定稿

```bash
python3 "$SKILL_DIR/scripts/validate_prd.py" <workspace> --strict
```

修复阻断项后重新校验。评分低于 85、存在未解决的关键不确定性、可追溯性断裂、证据冲突、ID 重复或需求不可测试，都会阻止定稿。
画像专项阻断项同样会让严格校验失败。B2B 的 PRD 需覆盖权限/状态/审计/数据范围；B2C 需覆盖漏斗/隐私/空状态/兼容性/风险；AI/Data 需覆盖评估/置信度/人工兜底/监控/成本延迟。

仅可如此推进状态：

```bash
python3 "$SKILL_DIR/scripts/validate_prd.py" <workspace> --strict --set-status review-ready
python3 "$SKILL_DIR/scripts/validate_prd.py" <workspace> --strict --set-status approved
```

只有在用户明确确认 review-ready 的 PRD 之后，才能推进到 `approved`。

## 完成输出

汇报：

- 工作区路径与选定的深度/画像；
- 已确认的阶段与模块；
- 校验评分、阻断项与警告；
- 最终 PRD 路径与遗留决策；
- 文档当前处于 `draft`、`review-ready` 还是 `approved`。
