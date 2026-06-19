# PMSkills

产品管理类 Agent 技能集合。每个技能都是自包含的（`SKILL.md` + 参考文档 + 纯标准库 Python 脚本），可在不同 Agent 平台上运行。

## 技能列表

| 技能 | 说明 |
|---|---|
| [`write-production-prd`](skills/write-production-prd/SKILL.md) | 通过证据收集、产品经理需求分析、Vibe Coding 意图工程、分阶段成形、受控模块确认、评审交接、安全装配与确定性质量门禁，产出可交付的生产级 PRD。**默认以中文输出 PRD。** |

## 安装（npx skills）

本仓库遵循 Agent Skills 规范，可用 [`npx skills`](https://github.com/vercel-labs/skills) 一键安装到 Claude Code、Codex、Cursor 等：

```bash
# 安装本技能
npx skills add guanhua1992/pmskills/write-production-prd

# 或只写仓库名，由 CLI 列出并选择
npx skills add guanhua1992/pmskills
```

## 跨平台运行

技能脚本只依赖 **Python 3 标准库**，无第三方依赖。脚本通过 `Path(__file__)` 自行定位技能目录，因此与当前工作目录无关——只要用技能目录的路径来调用脚本即可。

- **Claude Code**：将技能目录放入 `~/.claude/skills/`（或插件的 `skills/` 目录），技能经 `SKILL.md` frontmatter 触发。
- **Codex**：技能附带 [`agents/openai.yaml`](skills/write-production-prd/agents/openai.yaml)，按 Codex 的技能安装方式加入后，用 `$write-production-prd` 调用。
- **其它 Agent 工具**：直接将 `SKILL.md` 作为指令源；脚本以 `python3 "<技能目录>/scripts/<脚本名>.py"` 方式调用。

`SKILL.md` 内的所有命令都以 `$SKILL_DIR`（技能自身目录的绝对路径）为基准，不假设当前目录就是技能目录。

## 输出语言

PRD 默认以**中文**输出叙述与字段标签；稳定标记 `[PRD-*]`、ID（`SRC/GOAL/SCN/FR/NFR/AC/BR`）、frontmatter 键与状态值保持英文/ASCII，以保证确定性校验。初始化时可用 `--output-language` 覆盖（如 `en`、`follow-user`）。

## 投喂参考资料（编写前）

想让 PRD 基于已有材料（旧 PRD、竞品资料、调研、会议纪要、导出数据等），在编写前把它们投喂给技能：

1. **先建工作区**：手动跑一次 `init_workspace.py`（或让 Agent 先初始化），生成 `<名称>-workspace/`。
2. **放资料**：把文件拷进 `<工作区>/inputs/materials/`。
3. **开工**：技能会在塑形开始前**逐份读取** `materials/`，用 `add_source.py` 登记为 `SRC-*` 证据（按事实/假设分类、标注置信度），后续 PRD 引用即可追溯到原始资料。

```bash
# 1) 先建工作区
python3 "$SKILL_DIR/scripts/init_workspace.py" --name "你的产品名"
# 2) 把参考资料放进 <你的产品名-workspace>/inputs/materials/
# 3) 再让技能开始写 —— 它会先读 materials/ 并登记为证据
```

> 资料原件保留在 `inputs/materials/` 即可，技能不会复制到别处；目录内的 `README.md` 为占位说明，不会被当作资料读取。

## 运行测试

```bash
python3 -m unittest discover -s tests -v
```

> 可选 CI：仓库源码内含 `verify.yml`（校验技能结构 + 跑测试），因首次提交所用 token 缺 `workflow` 权限未一并推送；可在 GitHub 网页 Actions 新建 workflow 启用。
