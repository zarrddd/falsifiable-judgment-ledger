# Falsifiable Judgment Ledger · 可证伪判断台账规范

> **Disclaimer / 免责声明**：本仓库仅为记录方法论与数据规范，不含、不提供、不构成任何投资建议或投资咨询服务；所有示例数据均为虚构。This repository defines a bookkeeping methodology only. It contains no investment advice; all sample data is fictional.

**每条判断，都有到期日。** 发表判断时同时写定证伪条件与到期日；到期必判，错的照登，改的留痕。
本仓库提供这套纪律的最小规范、机器可校验的 schema，与三件配套工具。

## 内容

- [`SPEC.md`](SPEC.md) — 规范正文（v0.1-draft，六要素 · 七纪律 · 一致性定义）
- [`schema/`](schema/) — 条目与账本的 JSON Schema（闭合字段，结构性防泄露）
- [`demo/demo-ledger.json`](demo/demo-ledger.json) — **虚构**演示账本
- [`tools/validate.py`](tools/validate.py) — 一致性校验器（零依赖）
- [`tools/expiry_check.py`](tools/expiry_check.py) — 到期未判检测器
- [`tools/denylist_gate.py`](tools/denylist_gate.py) — 通用禁词门引擎（**词表自备**，bring your own blocklist：真实词表是敏感资产，应存放在版本库之外，默认路径 `~/.config/ledger-guard/blocklist.txt`；格式参考 [`blocklist.example.txt`](blocklist.example.txt)）
- [`guards/`](guards/) — pre-commit / pre-push 泄露闸钩子，`bash guards/install.sh` 一键安装

## 快速开始

```bash
python3 tools/validate.py demo/demo-ledger.json
python3 tools/expiry_check.py demo/demo-ledger.json --as-of 2026-07-01
```

两个命令都退出 0，即符合 v0.1 一致性定义。
（`--as-of` 钉死检查日期，保证演示结果确定；检查真实账本时省略该参数，按当天判逾期。）

## 方法公开，账本私有

本规范在维护者自己的一份私有研究台账上运行。规范与工具全部公开；账本内容不属于本仓库，
也不应属于任何强迫公开的场合——**可审计是一种自愿选择的纪律，不是表演**。

## License

代码：Apache-2.0（见 `LICENSE`）· 规范文本与 schema：CC BY-SA 4.0（见 `LICENSE-SPEC`）

Maintained by **Zarrddd · 军师台**
