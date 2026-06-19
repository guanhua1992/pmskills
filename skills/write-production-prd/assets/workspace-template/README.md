# {{PRODUCT_NAME}} — PRD 工作区

> 📄 **最终交付物 → [prd/PRD.md](prd/PRD.md)**
>
> 文档状态以 `prd/PRD.md` 顶部 frontmatter 的 `status` 为准（draft / review-ready / approved）；最新质量评分见 [prd/quality-report.md](prd/quality-report.md)。

- 深度：{{DEPTH}}　|　产品画像：{{PRODUCT_PROFILE}}

## 这个文件夹怎么看

- 只想看成品 → 打开 `prd/PRD.md`
- 想看怎么一步步推导出来的 → `shaping/`（按 00 → 06 顺序读）
- 想投喂参考资料 → 把文件放进 `inputs/materials/`（技能会在塑形前读取并登记为证据）
- 想看证据从哪来 → `inputs/source-notes.md`
- 想看质量门禁评分 → `prd/quality-report.md`

## 目录说明

| 路径 | 是什么 | 能不能手改 |
|---|---|---|
| `prd/PRD.md` | 最终 PRD（装配产物） | ❌ 勿手改，改了会被校验/装配拦住 |
| `prd/modules/` | PRD 源文件（分模块写） | ✅ 改内容改这里，再重新装配 |
| `prd/module-plan.md` | 模块计划（深度/画像/模块清单） | ✅ |
| `prd/quality-report.md` | 质量门禁报告 | ⚙️ 校验时自动生成 |
| `prd/_append-log.md` | 受控装配日志 | ⚙️ 装配时自动追加 |
| `shaping/` | 需求塑形过程：发现→价值→JTBD→规则→意图→范围→简报 | ✅ |
| `inputs/materials/` | 你投喂参考资料的地方（旧PRD/竞品/调研/纪要） | ✅ 放文件进去即可 |
| `inputs/source-notes.md` | 证据与来源账本 | ✅ |
| `review/` | 评审记录（自检/版本/内部/技术/公开/行动项） | ✅ |
| `workspace.json` | 工作区元数据与状态总账 | ⚙️ 脚本维护，勿手改 |

## 状态流转（什么时候、由谁改）

文档有两层状态，都由脚本写入；但每一步推进都要人点头，不会从沉默里自动通过：

| 层级 | 状态变化 | 何时发生 / 触发命令 | 谁拍板 |
|---|---|---|---|
| 阶段（`shaping/*.md`） | `draft → confirmed` | 人确认该阶段后 `confirm_item.py --kind stage` | 🧑 人确认 → ⚙️ 脚本翻转 |
| 模块（`prd/modules/*.md`） | `draft → confirmed` | 人确认该模块后 `confirm_item.py --kind module` | 🧑 人确认 → ⚙️ 脚本翻转 |
| 文档整体 | `draft → review-ready` | 质量门禁通过后 `validate_prd.py --set-status review-ready` | ⚙️ 脚本（需评分达标、零阻断） |
| 文档整体 | `review-ready → approved` | 人最终批准后 `validate_prd.py --set-status approved` | 🧑 **必须人显式确认** |

> 机器状态写在各文件顶部 `<!-- *-status -->` 注释、`prd/PRD.md` frontmatter 与 `workspace.json`；这些由脚本维护，勿手改。

## 谁来改：人 / AI / 脚本

| 角色 | 负责 |
|---|---|
| 🧑 人 | 关键决策与冲突裁决、逐阶段/模块确认、最终批准 `approved` |
| 🤖 AI | 起草 `shaping/` 与 `prd/modules/` 内容、登记证据、运行脚本、装配与校验 |
| ⚙️ 脚本 | 维护机器状态（frontmatter / `<!-- *-status -->` / `workspace.json`）、质量评分、装配日志 |

> 铁律：AI 不得自行拍板产品策略、权限、定价、合规、数据留存等；这类必须由人确认（见 PRD 的 `[PRD-VIBE-SPEC]` → "AI 不得决策"）。

## 改了内容怎么重新生成 PRD

1. 改 `prd/modules/` 下对应模块（**不要直接改 `prd/PRD.md`**）
2. 重新装配：`python3 <skill>/scripts/assemble_prd.py <workspace>`
3. 重新校验：`python3 <skill>/scripts/validate_prd.py <workspace> --strict`
