# 生活办事材料核验输出契约

## 产物

建议生成：

- `readiness-report.md`：面向用户的核验报告与出门前行动卡。
- `readiness.json`：供校验、复用和后续更新的结构化状态。

## JSON 根字段

| 字段 | 类型 | 规则 |
|---|---|---|
| `schema_version` | string | 固定为 `1.0` |
| `case` | object | 包含 `service`、`reference_date`、`profile_summary` |
| `sources` | array | 至少一项；ID 唯一 |
| `requirements` | array | 至少一项；ID 唯一 |
| `actions` | array | 可为空；ID 唯一 |
| `overall_status` | string | `ready`、`not_ready`、`needs_confirmation` |
| `questions` | string[] | 待确认问题 |
| `limitations` | string[] | 至少说明最终审核与来源当前性边界 |

## 来源对象

```json
{
  "id": "S1",
  "filename": "official-notice.pdf",
  "source_type": "user_provided_notice",
  "source_date": "2026-07-01",
  "currentness": "user_provided_current"
}
```

`currentness` 允许：

- `user_provided_current`
- `officially_verified`
- `unknown`
- `stale`

## 要求对象

```json
{
  "id": "R1",
  "item": "关系证明原件",
  "necessity": "conditional",
  "condition": "加入14周岁以下成员",
  "applicability": "applies",
  "status": "missing",
  "matched_inventory_ids": ["I07"],
  "reason": "仅有手机照片，通知要求原件",
  "evidence": [
    {
      "source_id": "S1",
      "locator": "第2页第3项",
      "quote": "须携带能证明关系的户口簿或出生证明原件"
    }
  ]
}
```

允许枚举：

- `necessity`：`required`、`conditional`、`optional`
- `applicability`：`applies`、`not_applicable`、`unknown`
- `status`：`ready`、`missing`、`expired`、`conflict`、`needs_confirmation`、`not_applicable`

约束：

- `conditional` 必须有非空 `condition`。
- `unknown` 必须对应 `needs_confirmation`。
- `not_applicable` 必须对应同名状态。
- `ready` 必须引用至少一个现有材料 ID。
- 每项要求至少有一个有效来源锚点。

## 行动对象

```json
{
  "id": "T1",
  "action": "在申请表和涂改处签名",
  "priority": "blocking",
  "evidence": [
    {"source_id": "S1", "locator": "第1页第4项", "quote": "涂改处须签名确认"}
  ]
}
```

`priority` 允许 `blocking`、`high`、`normal`。

## 整体状态算法

1. 任一适用要求为 `missing`、`expired` 或 `conflict` → `not_ready`。
2. 无阻断项且至少一项为 `needs_confirmation` → `needs_confirmation`。
3. 其余适用项均为 `ready` → `ready`。

## Markdown 报告模板

```markdown
# 办事材料核验报告

结论：未就绪｜2 个阻断项，1 个待确认项

## 先处理的阻断项
- [ ] 材料｜原因｜最短补救动作｜来源

## 待确认
- 条件｜为什么不能判断｜向谁确认

## 已齐全 / 不适用
- 材料｜状态｜来源

## 出门前行动卡
- [ ] 按依赖和时间排序的动作

## 来源与限制
- 来源日期、当前性、不可读部分、最终审核边界
```

