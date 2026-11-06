# 示例账本 · Example Ledgers

> 本目录所有账本均为**虚构**（文件头 `"fictional": true`），仅演示格式与纪律；不含任何真实人物、机构或投资建议。
> All ledgers here are FICTIONAL and exist only to illustrate the format and the discipline.

每份账本都通过 `tools/validate.py` 与 `tools/expiry_check.py`（`--as-of 2026-11-01`，钉死检查日期以保证结果确定），即符合 v0.1 一致性定义。下面的输出由工具实际生成。

| 文件 | 内容 | 要点 |
|---|---|---|
| [`macro-2026.json`](macro-2026.json) | 宏观 / 市场判断（全部虚构经济体与指数） | 8 条，6 已判（对 2 · 部分 1 · 错 3），2 待判。演示金融类判断如何写成可裁决的句子——注意 J-2026-006 把『首次公布值』写进判据，后续数据修正不影响判定。无任何 `corrections[]`：判了就是判了。 |
| [`product-decisions.json`](product-decisions.json) | 一人公司的产品赌注 | 6 条，5 已判（对 2 · 部分 1 · 错 2），1 待判。『功能上线后 X 天内拿到第一位付费用户』这类赌注的写法；J-2026-003 展示 `partial` 必须写明口径。 |
| [`personal-forecasts.json`](personal-forecasts.json) | 日常可证伪预测 | 5 条，4 已判（对 1 · 部分 1 · 错 2），1 待判。证明这套纪律不限于专业领域：晨跑、读书、种番茄，一样能到期必判。 |

## 一键复核 · Re-run everything

```bash
for f in examples/*.json; do
  python3 tools/validate.py "$f"
  python3 tools/expiry_check.py "$f" --as-of 2026-11-01
  python3 tools/report.py "$f" --as-of 2026-11-01
done
```

## `macro-2026.json` — 宏观 / 市场判断（全部虚构经济体与指数）

```console
$ python3 tools/validate.py examples/macro-2026.json
OK: 8 entries valid

$ python3 tools/expiry_check.py examples/macro-2026.json --as-of 2026-11-01
OK: no overdue judgments

$ python3 tools/report.py examples/macro-2026.json --as-of 2026-11-01
entries: 8
pending: 2 (overdue: 0)
correct: 2  partial: 1  wrong: 3
hit rate strict (correct only): 2/6
hit rate lenient (partial counted): 3/6
```

<details><summary><code>report.py --md</code> 渲染结果</summary>

# 判断台账 · Judgment Ledger

> **FICTIONAL** — 本账本全部条目为虚构演示数据。

共 8 条 · 已判 6（对 2 / 部分 1 / 错 3） · 待判 2（逾期 0） · 严格命中 2/6 · 宽口径 3/6

| ID | 判断 | 证伪条件 | 到期 | 结果 |
|---|---|---|---|---|
| J-2026-001 | 示例经济体 ALPHA 的央行将在 2026-06-30 前至少下调政策利率一次。 | 至 2026-06-30，政策利率不低于 2026-01-10 的水平。 | 2026-06-30 | ✅ correct<br>到期核对：示例央行于 2026-05 会议下调 25 个基点。判对。 |
| J-2026-002 | 示例经济体 ALPHA 2026 年第一季度 CPI 同比均值将低于 3.0%。 | 官方公布的一季度三个月 CPI 同比算术均值不低于 3.0%。 | 2026-04-20 | ❌ wrong<br>公布均值 3.4%。判错，原文照登；错因是低估了示例经济体的服务业通胀粘性。 |
| J-2026-003 | 示例股指 OMEGA 2026-06-30 收盘点位将高于 2025-12-31 收盘点位。 | 2026-06-30 收盘点位小于或等于 2025-12-31 收盘点位。 | 2026-06-30 | ✅ correct<br>到期后一日按交易所收盘数据核对：上半年累计上涨 4.2%。判对。 |
| J-2026-004 | 示例经济体 BETA 的货币对示例经济体 ALPHA 的货币将在 2026-09-30 前贬值超过 5%（以 2026-01-15 中间价为基准）。 | 至 2026-09-30，期间任一交易日的贬值幅度均未超过 5%。 | 2026-09-30 | ❌ wrong<br>期间最大贬幅 1.8%，远未触及 5%。判错。事后看，判断把一次性冲击当成了趋势。 |
| J-2026-005 | 示例大宗商品 KAPPA 2026 年第三季度月度均价的平均值将高于第二季度。 | 官方月度均价口径下，三季度三个月均值小于或等于二季度三个月均值。 | 2026-10-05 | ◐ partial<br>部分的口径：按发表时写明的『官方月度均价』三季度高出 0.3%，字面成立；但按日均价口径持平，且差值小于该口径的四舍五入误差。记部分，不记全对。 |
| J-2026-006 | 示例经济体 ALPHA 2026 年 9 月失业率（10 月公布）将高于 4.5%。 | 官方首次公布的 9 月失业率小于或等于 4.5%。 | 2026-10-10 | ❌ wrong<br>首次公布值 4.3%。判错。注意：后续修正值不改变本判定——判据写明的是『首次公布』。 |
| J-2026-007 | 示例经济体 GAMMA 2026 年全年 GDP 增速初步核算值将高于 4.5%。 | 2027-01-31 前官方公布的初步核算值小于或等于 4.5%。 | 2027-01-31 | ⏳ pending |
| J-2026-008 | 示例经济体 ALPHA 央行资产负债表总规模在 2026-12-31 将低于 2025-12-31。 | 官方公布的 2026 年末资产负债表总规模大于或等于 2025 年末。 | 2027-01-15 | ⏳ pending |

*Format: Falsifiable Judgment Ledger v0.1 · as of 2026-11-01*

</details>

## `product-decisions.json` — 一人公司的产品赌注

```console
$ python3 tools/validate.py examples/product-decisions.json
OK: 6 entries valid

$ python3 tools/expiry_check.py examples/product-decisions.json --as-of 2026-11-01
OK: no overdue judgments

$ python3 tools/report.py examples/product-decisions.json --as-of 2026-11-01
entries: 6
pending: 1 (overdue: 0)
correct: 2  partial: 1  wrong: 2
hit rate strict (correct only): 2/5
hit rate lenient (partial counted): 3/5
```

<details><summary><code>report.py --md</code> 渲染结果</summary>

# 判断台账 · Judgment Ledger

> **FICTIONAL** — 本账本全部条目为虚构演示数据。

共 6 条 · 已判 5（对 2 / 部分 1 / 错 2） · 待判 1（逾期 0） · 严格命中 2/5 · 宽口径 3/5

| ID | 判断 | 证伪条件 | 到期 | 结果 |
|---|---|---|---|---|
| J-2026-001 | 示例产品 LEDGERKIT 的『导出到表格』功能上线后，将在 2026-03-15 前获得第一位为该功能付费的用户。 | 至 2026-03-15，后台无任何以导出功能为升级原因的付费订单。 | 2026-03-15 | ✅ correct<br>3 月 9 日出现首笔升级订单，升级问卷勾选原因为『导出』。判对。 |
| J-2026-002 | 把定价从仅月付改为默认年付后，2026-05-31 前的注册到付费转化率将不低于改版前三个月的均值。 | 改版后至 2026-05-31 的转化率低于改版前三个月均值。 | 2026-05-31 | ❌ wrong<br>改版前均值 2.1%，改版后 1.4%。判错，原文照登。年付默认抬高了首单门槛，这是发表时没想到的。 |
| J-2026-003 | 新上线的中文落地页将在 2026-06-30 前带来至少 50 位自然注册用户。 | 至 2026-06-30，来源标记为中文落地页的注册数少于 50。 | 2026-06-30 | ◐ partial<br>部分的口径：落地页来源注册 52 位，字面达标；但其中 23 位来自一次一次性的社群推广，不是『自然』注册，剔除后 29 位。按字面算对、按发表意图算错，记部分。 |
| J-2026-004 | 宣布停止维护示例插件 BRIDGE 后，至 2026-08-31 收到的用户投诉不会超过 3 封。 | 至 2026-08-31，支持邮箱与社区中与停更相关的投诉合计超过 3 封。 | 2026-08-31 | ✅ correct<br>共 1 封投诉。判对。砍功能的恐惧大于实际代价，这条值得记住。 |
| J-2026-005 | 示例产品 LEDGERKIT 2.0 将在 2026-10-31 前发布，且过程中不使用任何外包。 | 至 2026-10-31 未发布 2.0，或发布过程中有任何外包支出。 | 2026-10-31 | ❌ wrong<br>2.0 推迟到 11 月，且 9 月外包了图标设计。两个条件都没守住，判错。 |
| J-2026-006 | 示例产品 LEDGERKIT 2026 年 12 月的月度经常性收入将达到 2026 年 1 月的两倍以上。 | 2026 年 12 月账单口径的月度经常性收入小于 1 月的两倍。 | 2027-01-05 | ⏳ pending |

*Format: Falsifiable Judgment Ledger v0.1 · as of 2026-11-01*

</details>

## `personal-forecasts.json` — 日常可证伪预测

```console
$ python3 tools/validate.py examples/personal-forecasts.json
OK: 5 entries valid

$ python3 tools/expiry_check.py examples/personal-forecasts.json --as-of 2026-11-01
OK: no overdue judgments

$ python3 tools/report.py examples/personal-forecasts.json --as-of 2026-11-01
entries: 5
pending: 1 (overdue: 0)
correct: 1  partial: 1  wrong: 2
hit rate strict (correct only): 1/4
hit rate lenient (partial counted): 2/4
```

<details><summary><code>report.py --md</code> 渲染结果</summary>

# 判断台账 · Judgment Ledger

> **FICTIONAL** — 本账本全部条目为虚构演示数据。

共 5 条 · 已判 4（对 1 / 部分 1 / 错 2） · 待判 1（逾期 0） · 严格命中 1/4 · 宽口径 2/4

| ID | 判断 | 证伪条件 | 到期 | 结果 |
|---|---|---|---|---|
| J-2026-001 | 我将在 2026-03-31 前完成连续 60 天的晨跑打卡。 | 至 2026-03-31，打卡记录中不存在任何一段连续 60 天的晨跑。 | 2026-03-31 | ❌ wrong<br>最长连续 41 天，第 42 天因出差中断。判错，照登。 |
| J-2026-002 | 2026 年上半年我将读完 12 本书（以读完最后一页为准）。 | 至 2026-06-30 读完的书少于 12 本。 | 2026-06-30 | ✅ correct<br>读完 13 本。判对。 |
| J-2026-003 | 阳台上 3 月播种的番茄将在 2026-08-15 前结出第一个完全成熟的果实。 | 至 2026-08-15 没有任何一个果实完全转红。 | 2026-08-15 | ◐ partial<br>部分的口径：8 月 13 日有一个果实开始转色，但到期日当天仍未完全转红；『结果』成立、『完全成熟』不成立。记部分。 |
| J-2026-004 | 我将在 2026-09-30 前把个人网站从旧系统完整迁移到静态站点生成器。 | 至 2026-09-30，仍有任一页面由旧系统提供服务。 | 2026-09-30 | ❌ wrong<br>约 60% 页面完成迁移，归档页仍在旧系统。判错。 |
| J-2026-005 | 我将在 2026-12-31 前独立滑完一条初级雪道且全程不摔倒。 | 至 2026-12-31 没有任何一次全程不摔的初级道完整滑行。 | 2026-12-31 | ⏳ pending |

*Format: Falsifiable Judgment Ledger v0.1 · as of 2026-11-01*

</details>

## 这些示例刻意展示的几件事

- **错的照登**：三本账的严格命中率分别是 2/6、2/5、1/4。真实账本大多如此——可信度来自错误被保留，而不是来自命中率好看。
- **`partial` 必须写口径**：每条 `partial` 的 `resolution_note` 都写明了『哪部分成立、哪部分不成立、按什么口径』。
- **判据先行**：`falsifier` 里写的是『官方首次公布值』『来源标记为……的注册数』这类第三方按字面即可裁决的条件，不是事后解释。
- **没有事后修订**：没有任何条目的 `claim` 或 `falsifier` 被改写；`corrections[]` 只用于事实性笔误（本目录无此情况），且原文保留。
- **待判条目有到期日**：所有 `pending` 条目的 `verify_by` 都晚于 2026-11-01，所以 `expiry_check --as-of 2026-11-01` 退出 0；把 `--as-of` 改到 2027-02-01 再跑一次，就能看到逾期是什么样子。
