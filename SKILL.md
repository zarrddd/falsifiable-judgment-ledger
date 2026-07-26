---
name: judgment-ledger
description: 可证伪判断台账 — 立判断必带证伪条件与到期日，到期必判，错的照登。Use when the user wants to 记一条判断 / 立个判断 / 到期判定 / 落判 / 判断复盘 / 看战绩 / 晒战绩 / 初始化判断台账, or mentions a falsifiable judgment ledger. Not for generic note-taking or todo lists.
---

# 可证伪判断台账 · Judgment Ledger Skill

把「说过的判断」变成可审计的账：每条判断在**发表时**就写定证伪条件与到期日；
到期必判；错的照登、永不删除。规范见 [SPEC.md](SPEC.md)，本文件只讲怎么用。

## 账本位置

首次使用时问用户账本放哪，之后沿用。默认建议：`~/.config/judgment-ledger/ledger.json`。
**真实账本永远不放进公开仓库**（方法公开，账本私有）。以下命令中 `$LEDGER` 代指该路径，
`$SKILL` 代指本技能目录。

## 四个动作

### 1. 立判断（最重要的一步在写入之前）

用户口述的判断往往不可证伪。写入前先按三问打磨，不合格就追问，不许替用户放水：

- **可检验**：claim 是不是一句到期时能明确核对的陈述？「AI 行业会继续发展」不合格；
  「X 产品将在 2027-06-30 前公开发布」合格。
- **判据先行**：falsifier 要写明「什么情况算我错」，且第三方按字面就能裁决。
  禁止「可能」「大概率」「中长期」这类留后路的措辞进入 claim 或 falsifier。
- **有到期日**：verify_by 是一个具体日期。用户说不出日期，就问「最晚什么时候见分晓」。

三问过了才写入：

```bash
python3 $SKILL/tools/new_entry.py $LEDGER \
  --claim "……" --falsifier "……" --verify-by YYYY-MM-DD [--track "分类"]
```

编号自动分配（J-YYYY-NNN，永不复用）；工具会先校验再落盘，拒绝时账本不动。

### 2. 到期巡检

```bash
python3 $SKILL/tools/expiry_check.py $LEDGER
```

列出所有已过期仍未判的条目。逾期不是小事——到期日的意义就是不许被忽略。

### 3. 落判

到期日当日或之后才能判（工具强制，早判会被拒；`--on` 也不许写未来日期——不许把判定预填到未来时点）：

```bash
python3 $SKILL/tools/resolve.py $LEDGER \
  --id J-YYYY-NNN --status correct|partial|wrong --note "判定依据"
```

- `wrong` 照登，永不删除、永不改写 claim 原文。
- `partial` 必须在 note 里写明「部分」的具体口径。
- 已判条目不可复判。事实性笔误走 corrections：直接编辑 JSON，在该条目
  `corrections[]` 追加 `{"on": "YYYY-MM-DD", "note": "……"}`（原文保留），
  改完必须跑 `python3 $SKILL/tools/validate.py $LEDGER` 确认仍合规。

### 4. 看战绩

```bash
python3 $SKILL/tools/report.py $LEDGER        # 计数与命中率（严格/宽两种口径）
python3 $SKILL/tools/report.py $LEDGER --md   # markdown 战绩表，可直接发布
```

`--md` 输出整本账（含错的条目——这正是可信度的来源），适合贴进公众号/博客/README。

## 红线

- 不删条目、不改历史、不事后放宽 falsifier——违反任何一条，这本账就失去意义。
- 公开发布前先过泄露闸：`python3 $SKILL/tools/denylist_gate.py --blocklist <私有词表> <文件>`
  （词表自备，放在版本库之外；格式见 [blocklist.example.txt](blocklist.example.txt)）。
- 金融类判断注意 [SPEC.md §4](SPEC.md) 合规提示：本方法是自我问责的记账纪律，
  不构成投资建议；向公众传播需自行确保符合所在法域监管要求。

## 一致性

`validate.py` 与 `expiry_check.py` 都退出 0，即符合规范，可自愿声明
`Conforms to Falsifiable Judgment Ledger v0.1`。
