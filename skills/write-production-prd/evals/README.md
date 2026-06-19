# Evals

`evals.json` 是 `write-production-prd` 技能的**评测场景规格**：每个用例描述一段触发输入（`prompt`）与期望产出特征（`expect`），覆盖五类核心场景：

1. 模糊想法 → PRD
2. 从现有代码库反推 PRD
3. 修复不完整 PRD
4. B2B 画像门禁
5. AI/Data 画像门禁

## 怎么用

当前仓库**没有自动 eval runner**，`evals.json` 先作为：

- **触发回归**：核对技能在这些输入下是否被正确触发；
- **产出验收清单**：人工对照 `expect` 字段检查产出（是否提问、是否登记证据、19 个 `[PRD-*]` 是否齐全、严格校验是否通过、画像门禁是否生效）。

确定性部分可直接复用现有脚本验证产出工作区：

```bash
python3 ../scripts/validate_prd.py <生成的workspace> --strict
```

后续若需自动化，可加一个薄 runner：对每个 case 驱动技能生成 workspace，再用 `validate_prd.py --json` 比对 `expect`。
