# 五分钟上手 · USAGE

> 本文只讲怎么用。规范见 [SPEC.md](SPEC.md)，AI 技能用法见 [SKILL.md](SKILL.md)，成品账本见 [examples/](examples/)。
> 所有工具零依赖，只需 Python 3。下文 `$LEDGER` 代指你的账本路径（建议 `~/.config/judgment-ledger/ledger.json`，**不要放进公开仓库**）。
> 为了让输出可复现，示例里把日期用 `--stated-on` / `--on` / `--as-of` 钉死；日常使用省略这些参数，工具按当天处理。

```bash
git clone https://github.com/zarrddd/falsifiable-judgment-ledger
cd falsifiable-judgment-ledger
export LEDGER=/tmp/ledger.json        # 练习用；真实账本放在版本库之外
```

## 1. 立判断 · new_entry

一条判断必须同时带上**证伪条件**（什么情况算我错）和**到期日**。工具缺一不写，写前先校验。

```console
$ python3 tools/new_entry.py $LEDGER --claim "示例项目 DEMO-KIT 将在 2026-03-31 前发布 1.0 正式版。" --falsifier "至 2026-03-31 官方仓库无 1.0 正式 tag。" --track "产品发布" --stated-on 2026-01-10 --verify-by 2026-03-31
OK: J-2026-001

$ python3 tools/new_entry.py $LEDGER --claim "示例指标 Q1 均值将高于 100。" --falsifier "官方公布的 Q1 均值不高于 100。" --stated-on 2026-01-10 --verify-by 2026-04-20
OK: J-2026-002
```

编号 `J-YYYY-NNN` 自动分配，年份取 `stated_on`，序号永不复用。不可证伪的判断会被拒绝，账本不动：

```console
$ python3 tools/new_entry.py $LEDGER --claim "AI 行业会继续发展。" --falsifier "不会" --stated-on 2026-01-10 --verify-by 2026-12-31
REFUSED: falsifier too short (schema minLength 8) — write down what would prove you wrong (spec discipline 4)
```

写入后的文件长这样（纯 JSON，可以直接读、直接 diff）：

```json
{
  "ledger_version": "0.1",
  "entries": [
    {
      "id": "J-2026-001",
      "claim": "示例项目 DEMO-KIT 将在 2026-03-31 前发布 1.0 正式版。",
      "falsifier": "至 2026-03-31 官方仓库无 1.0 正式 tag。",
      "stated_on": "2026-01-10",
      "verify_by": "2026-03-31",
      "status": "pending",
      "track": "产品发布"
    },
    {
      "id": "J-2026-002",
      "claim": "示例指标 Q1 均值将高于 100。",
      "falsifier": "官方公布的 Q1 均值不高于 100。",
      "stated_on": "2026-01-10",
      "verify_by": "2026-04-20",
      "status": "pending"
    }
  ]
}
```

## 2. 校验 · validate

```console
$ python3 tools/validate.py $LEDGER
OK: 2 entries valid
```

退出 0 即结构合规：字段闭合（多一个字段就失败，防止私有信息混入公开层）、编号格式、日期合法、状态与 `resolved_on` 一致、无重复 id。
手工编辑过 JSON 之后务必再跑一次。

## 3. 到期巡检 · expiry_check

```console
$ python3 tools/expiry_check.py $LEDGER --as-of 2026-02-01
OK: no overdue judgments

$ python3 tools/expiry_check.py $LEDGER --as-of 2026-04-01
OVERDUE: J-2026-001 verify_by=2026-03-31 — judge it, on the record
```

第二条退出码为 1：到期未判即违规。建议把它放进每天/每周的例行命令里（或 cron），逾期就会一直响到你落判为止。

## 4. 落判 · resolve

只能在到期日**当日或之后**判，判了就是终局：

```console
$ python3 tools/resolve.py $LEDGER --id J-2026-001 --status correct --note "提前" --on 2026-03-01
REFUSED: J-2026-001 expires 2026-03-31 — judge on or after expiry (spec discipline 1: no early verdicts)

$ python3 tools/resolve.py $LEDGER --id J-2026-001 --status wrong --note "到期核对：仓库最新 tag 为 0.9.4，无 1.0。判错，原文照登。" --on 2026-03-31
OK: J-2026-001 -> wrong (resolved_on 2026-03-31)

$ python3 tools/resolve.py $LEDGER --id J-2026-001 --status correct --note "翻案" --on 2026-04-01
REFUSED: J-2026-001 already adjudicated as 'wrong' — verdicts are final; use corrections[] for factual slips

$ python3 tools/resolve.py $LEDGER --id J-2026-002 --status correct --note "官方公布 Q1 均值 104.2。判对。" --on 2026-04-20
OK: J-2026-002 -> correct (resolved_on 2026-04-20)
```

三种结果：`correct` / `partial` / `wrong`。`partial` 的 `--note` 必须写明"部分"的具体口径（哪部分成立、哪部分不成立）。`--on` 不许写未来日期。

## 5. 看战绩 · report

```console
$ python3 tools/report.py $LEDGER --as-of 2026-04-21
entries: 2
pending: 0 (overdue: 0)
correct: 1  partial: 0  wrong: 1
hit rate strict (correct only): 1/2
hit rate lenient (partial counted): 1/2
```

`--md` 输出整本账的 markdown 表（错的条目一并列出——这正是可信度的来源），可直接贴进博客、公众号或 README：

```console
$ python3 tools/report.py $LEDGER --as-of 2026-04-21 --md
# 判断台账 · Judgment Ledger

共 2 条 · 已判 2（对 1 / 部分 0 / 错 1） · 待判 0（逾期 0） · 严格命中 1/2 · 宽口径 1/2

| ID | 判断 | 证伪条件 | 到期 | 结果 |
|---|---|---|---|---|
| J-2026-001 | 示例项目 DEMO-KIT 将在 2026-03-31 前发布 1.0 正式版。 | 至 2026-03-31 官方仓库无 1.0 正式 tag。 | 2026-03-31 | ❌ wrong<br>到期核对：仓库最新 tag 为 0.9.4，无 1.0。判错，原文照登。 |
| J-2026-002 | 示例指标 Q1 均值将高于 100。 | 官方公布的 Q1 均值不高于 100。 | 2026-04-20 | ✅ correct<br>官方公布 Q1 均值 104.2。判对。 |

*Format: Falsifiable Judgment Ledger v0.1 · as of 2026-04-21*
```

命中率给两种口径（`partial` 算对 / 不算对），读者自己选更苛刻的那个。`report.py` 只做展示，不是闸门：一致性由 `validate.py` 与 `expiry_check.py` 同时退出 0 来认定（SPEC §5）。

## 三条铁律

1. **到期日必填**：没有 `verify_by` 的判断不是判断。`new_entry.py` 直接拒绝；`expiry_check.py` 让到期日无法被忽略。
2. **错的照登**：`wrong` 条目永不删除、永不改写 `claim` 原文。账本的可信度来自保留错误，不来自命中率好看。
3. **不事后修订**：`falsifier` 与 `verify_by` 在发表时写定，之后不得放宽；判定终局，不可翻案。事实性笔误（错别字、写错数字）只能在该条目的 `corrections[]` 里追加 `{"on": "YYYY-MM-DD", "note": "……"}`，原文保留，改完重跑 `validate.py`。

违反任何一条，这本账就失去意义——工具能拦住的都会拦，拦不住的靠你。

## 在已有的笔记仓库里采用

账本只是一个 JSON 文件，工具只是五个 Python 脚本，可以塞进任何已有仓库：

```bash
# 1. 把工具作为子目录引入（或直接复制 tools/ 下的 .py 文件）
git submodule add https://github.com/zarrddd/falsifiable-judgment-ledger vendor/judgment-ledger
# 2. 在仓库里建账本；真实账本若在私有仓库可以直接提交，若仓库公开请放到 .gitignore 并存放在别处
python3 vendor/judgment-ledger/tools/new_entry.py ledger/judgments.json --claim "……" --falsifier "……" --verify-by YYYY-MM-DD
# 3. 把巡检放进你已有的检查脚本 / CI / cron
python3 vendor/judgment-ledger/tools/validate.py ledger/judgments.json
python3 vendor/judgment-ledger/tools/expiry_check.py ledger/judgments.json
# 4. 发布战绩时渲染 markdown，粘进笔记或页面
python3 vendor/judgment-ledger/tools/report.py ledger/judgments.json --md > notes/judgment-scoreboard.md
```

几点建议：

- **方法公开，账本私有**：默认不要把真实账本放进公开仓库；要公开时用 `report.py --md` 导出，并先过泄露闸（`tools/denylist_gate.py --blocklist <你的私有词表>`，词表格式见 [blocklist.example.txt](blocklist.example.txt)；`tools/check_path_leaks.py` 另外拦截本机路径泄露，`bash guards/install.sh` 可把两道闸一并装进 git 钩子）。
- **一人一本**：`new_entry.py` / `resolve.py` 没有文件锁，不要并发写同一个账本。
- **多份账本也行**：按主题分文件（见 [examples/](examples/)），每份各自编号、各自校验。
- **用 `track` 分组**：可选字段，40 字以内，用来标记系列或框架，报表按 id 排序时仍能一眼看出归属。
- **不用 AI 也一样**：本仓库可作为 Claude 技能安装（见 [README.md](README.md)），但所有纪律由命令行工具强制，不依赖任何模型。

## 一致性声明

`validate.py` 与 `expiry_check.py` 对你的账本都退出 0，即可自愿声明：
`Conforms to Falsifiable Judgment Ledger v0.1`。
