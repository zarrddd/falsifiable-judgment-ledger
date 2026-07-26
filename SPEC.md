# 可证伪判断台账规范 · Falsifiable Judgment Ledger Specification

**版本 v0.1-draft** · 本规范随实践修订（欠承诺是刻意的）

> A judgment that cannot expire cannot be trusted.
> 不能到期的判断，不值得信任。

## 0. 目的

公开发表判断的人很多，愿意让判断被时间检验的人很少。本规范定义一种最小的记账格式，
使任何人的判断记录变得**可审计**：每条判断带证伪条件与到期日，到期必判，错的照登，改的留痕。

本规范只是会计准则。账本的内容、质量与所有权，永远属于记账的人。

## 1. 条目的六项必填要素

| 字段 | 含义 | 纪律 |
|---|---|---|
| `id` | 唯一编号 `J-YYYY-NNN` | 永不复用、永不重排——编号断档本身就是记录 |
| `claim` | 一句可检验的陈述 | 禁止用模糊措辞使其不可证伪 |
| `falsifier` | 证伪条件 | 发表时写明"什么情况算我错"，事后不得追加放宽 |
| `stated_on` | 发表日期 | ISO 8601 |
| `verify_by` | 到期日 | 发表时锁定；没有到期日的条目不合规 |
| `status` | `pending / correct / partial / wrong` | 只能在到期日当日或之后落判 |

## 2. 七条纪律

1. **到期必判**：`verify_by` 过期而 `status` 仍为 `pending`，即违规（工具 `expiry_check` 检测）。
2. **错的照登**：`wrong` 条目永不删除、永不改写 `claim` 原文。
3. **原地更正**：事实性笔误在 `corrections[]` 追加标注，原文保留。
4. **判据先行**：`falsifier` 与 `verify_by` 必须在发表时刻写定——判断与判据同龄。
5. **编号连续**：账本以 `id` 排序可审计；跳号与缺号需在账本层 `notes[]` 字段备注原因。
6. **三态诚实**：`partial` 是合法状态，但必须在 `resolution_note` 写明"部分"的具体口径。
7. **结构闭合**：schema 关闭附加字段（additionalProperties: false）——多带一个字段即校验失败，防止公开层意外携带私有信息。

## 3. 文件格式

见 `schema/entry.schema.json` 与 `schema/ledger.schema.json`。演示见 `demo/demo-ledger.json`
（**演示数据全部虚构**，文件头有 `"fictional": true` 声明）。

## 4. 合规注意（重要）

在中国大陆，对证券、期货标的向不特定公众提供分析、预测或建议并直接/间接收费，属于持牌业务。
**本规范不构成也不支持该类活动**：它是内容治理与自我问责的记账方法，与任何投资建议无关。
若你将本规范用于金融相关判断，请自行确保内容与传播方式符合所在法域的监管要求。

## 5. 一致性（Conformance）

一份账本称为符合本规范，当且仅当：
`tools/validate.py` 退出码 0，且 `tools/expiry_check.py` 退出码 0（或对逾期条目在账本层 `notes[]` 字段有书面说明）。
通过者可自愿声明：`Conforms to Falsifiable Judgment Ledger v0.1`。
