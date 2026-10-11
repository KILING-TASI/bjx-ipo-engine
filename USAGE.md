# 北交所新股获配与资金研究：详细使用说明

当前安装与教学入口见[首页](README.md)，资料准备见[BEGINNER](BEGINNER.md)。历史下载说明见[版本记录](CHANGELOG.md)。以下保留具体命令、方法、样本和限制，历史案例按各自日期阅读。

## 实际结果示例

**预算增加不一定多获配一手，退款公告也不能直接当作资金到账证明。** 示例复用悦龙科技（920188）的公开发行字段，比较三种假设预算；个人余股、实际到账和收益仍未知。

[完整截图与生成说明](docs/preview-guide.md) · [保存的 HTML 示例](docs/preview/index.html) · [示例输入](docs/preview/input.json)

截图是已保存的历史报告；当前源码生成的页面还包含多方案比较和公开回购参考。GitHub 不一定直接显示 HTML，下载后在本地打开。教学预算、费用和现金日期不算真实账户验证。


## 能做什么，暂不支持什么

| 想核对的问题 | 当前能做的事 |
|---|---|
| 预算够不够跨过百股阶梯 | 按发行价、申购上限和百股单位取整，计算声明配售率下的比例整手 |
| 收益会受哪些条件影响 | 比较明确的配售率、涨幅、费用和机会成本；余股额外百股只作为条件情景 |
| 多只新股会不会撞资 | 按明确日期记冻结、退款、留存本金和卖出回款，保留资金不足与同日顺序不明的缺口 |
| 不同资金方案怎么比较 | 在同本金、同期间下比较声明方案；单列一条公开回购定盘参考及假设费用 |
| 公告字段从哪里来 | 保存来源、原件摘要、选定字段和更正线索，区分公告日期、取得时间及未知可得时点 |
| 日期是否有依据 | 使用2026年北交所计划交易日历，逐案核对申购、公告退款和上市日期 |

暂不支持自动申购或交易、个人余股排序预测、完整年度收益回放、经过校准的中签率预测。计划交易日不认证实际开市或券商到账；缺失费用和日期不填零，冲突来源不自动选值。真实账号验收由用户暂停。

金额用人民币，股数用股，收益率与费率用小数，例如 `0.0005` 表示0.05%。公告退款日、退款资金可用日、上市日和卖出现金可用日分别输入。详细口径见 [现金账](docs/cash-and-evidence.md)、[情景与敏感性](docs/scenario-sensitivity.md)和 [方法说明](docs/funding-history-methods.md)。


## 独立使用与项目身份

本仓是独立 Python 计算引擎，提供 CLI 和 JSON 接口；另提供 [Skill 调用指引](SKILL.md)，注册时须保留完整本仓资源。无需安装其他自家专业仓。[research-workbench](https://github.com/KILING-TASI/research-workbench)可以调用它，并负责公司经营研究、综合判断和报告组织；工作台不是本引擎的运行依赖。

源码教学入口无需安装。需要安装计算模块时，按上方“安装和首次试用”操作。

构建依赖为 setuptools>=77，安装时可能联网取得；计算运行无普通第三方依赖。旧 alpha.9 wheel 仅含计算模块。当前 alpha.13 的安装后 CLI 教学入口已验收；作为 Skill 使用仍须保留完整资源。已安装模块可用 `python -I -m api` 接收完整 JSON 请求，格式见 [接口说明](docs/workbench-contract.md)。

只有 PDF 原文核对需要可选组件：

```powershell
.\.venv\Scripts\python.exe -m pip install ".[pdf]"
```

声明版本为 pypdf==6.14.2。运行 PDF 入口时不要加 `-S`，否则已安装组件不可见。主动获取来源需显式使用 `capture --online`，不会自动下载私人或付费资料。安装与独立使用的实际验收范围见 [单仓验收](docs/standalone-acceptance.md)。

其他可复制的离线入口：

```powershell
python bjx.py public-sample examples/public-sample.json --out-dir local-data/yuelong-01
python bjx.py compare-plans examples/compare-plans.json --out-dir local-data/plans-01
python -S .github/scripts/check_scenarios.py --out-dir local-data/scenarios-01
```

前两项输出目录含 `report.md`、`report.html`、输入、结果和摘要；情景验收输出另含预期值与实际回执。[实例索引](docs/scenario-acceptance.md)包括预算阶梯、余股未知、费用、资金不足和逐案日期边界。机器入口保持 JSON 输出，失败原因和下一步保存在报告中。


## 验证、来源与许可

已完成 Windows/Linux、Python3.10/3.12工程检查，以及单仓源码归档和非editable wheel实际运行。情景验收包含手算或现金守恒预期；CI通过不等于投资有效、资料完整或账户收益已认证。

真实公开发行覆盖仍为一只、八项选定字段，另有一条回购定盘参考。第一份公告已在北交、规则端和工作台实际复用，但不代表所有仓库的数据已统一。完整更正链、可信历史首次公开时刻及全部报告视觉验收仍未完成。

- [公开发行样本与来源](docs/public-sample-920188.md) · [日历核验范围](docs/calendar-verification.md) · [公开回购参考](docs/public-repo-reference.md)
- [公告复用验收](docs/announcement-reuse.md) · [数据入口与版本说明](docs/data-contract-inventory.md) · [后续路线](docs/roadmap.md)

[![原创代码 MIT](https://img.shields.io/badge/原创代码-MIT-blue.svg)](LICENSE)

原创代码和有权授权的原创说明采用 [MIT许可](LICENSE)。两个复用公告模块保留 [research-workbench原许可](licenses/research-workbench-MIT.txt)；第三方公告、行情、研报和外部组件的权利独立，代码许可不授予其数据使用权，详见 [第三方说明](THIRD_PARTY_NOTICES.md)。不发布原始公告PDF、账户材料或私人缓存。

仅供学习与研究，不构成投资建议或交易指令；使用前核对本次来源、日期与假设，详见 [使用边界](DISCLAIMER.md)。

构建记录与版本边界见 [alpha.9发布准备](docs/release-alpha9.md)。


## 自然语言使用

向已注册本仓 Skill 的助手直接提问。助手整理输入、调用计算并先回答能确定的部分，再解释依据和缺口；无需安装工作台。新增指引自 v0.2.0-alpha.12 随包提供；更早的发行包保持原样。


## 验证范围

源码教学启动、软件环境查询和安装后教学入口分别验证；软件就绪不等于真实资料已取得。中文问答需要助手按本仓Skill准备已声明输入，没有宣称任意自然语言自动发现或全市场数据闭环。旧报告、历史tag与案例证据保留。


HTML报告增加“指标怎么读、金额怎么核”，先看结论和缺口，再展开口径。见 [REPORT_GUIDE.md](REPORT_GUIDE.md)。
