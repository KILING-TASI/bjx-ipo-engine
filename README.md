# 北交所打新研究引擎

研究北交所网上发行的比例获配情景、现金占用与公开发行证据，保存来源、假设和缺口。

## 版本与状态

已发布功能预览版：[v0.2.0-alpha.8](https://github.com/KILING-TASI/bjx-ipo-engine/releases/tag/v0.2.0-alpha.8)。源码计算版本为 `0.2.0-alpha.8`，工作台接口版本为 `1.0`；本次为文档快照整理，未新增计算能力。历史发布包保持冻结，主分支说明与下载包按各自版本阅读。

文档整理日期：2026-10-09。安装包见 [Releases](https://github.com/KILING-TASI/bjx-ipo-engine/releases)，变更见 [CHANGELOG](CHANGELOG.md)。真实账户验收按用户要求暂停，公开资料工作继续。

## 快速开始

Python 3.10 及以上。在仓库目录运行，基础示例不联网、不需要第三方组件：

```bash
python engine.py examples/scenarios.json
```

这是人为教学参数，不代表真实新股、用户账户或未来收益。生成可读报告与输入底稿：

```bash
python bjx.py scenarios examples/scenarios.json --out-dir local-data/scenarios-01
python bjx.py verify local-data/scenarios-01
```

输出目录必须是新目录，避免覆盖旧研究。PDF 原文比较按需使用 `pypdf`，当前验收版本为 6.14.2；基础例子不要求安装它。下载和代码许可不代表获得第三方资料使用权。

## 已实现与边界

| 能力 | 当前范围 |
|---|---|
| 获配与收益情景 | 预算、公告上限、百股单位、联合配售率/涨幅情景、费用、机会成本、平衡点及额外百股条件敏感性 |
| 现金账与对照 | 明确日期的多发行和回购事件；同本金同期间比较，撞资或未结清时保留缺口 |
| 来源与档案 | 主动来源保存、原文摘要绑定、更正标题线索、PDF 提取差异、假设快照与事后分离复盘 |
| 官方排期与样本 | 2026 年北交所计划交易日历；悦龙科技（920188）一只历史发行的八项选定字段 |
| 计算接口 | v1.0 情景与现金账接口，旧入口保留；与主工作台年度情景尚未证实等价 |

没有自动申购、交易执行、经过验证的中签率预测模型、全年完整回放或收益承诺。真实个人获配、余股、券商到账及卖出结果不能由公开汇总比例还原。教学案例不计入真实发行数量。

## 输入与关键口径

- 金额单位为人民币；收益率及费率用小数，例如 `0.0005` 表示 0.05%，`1.2` 表示 120%。
- 公告申购上限按股数输入，申购按 100 股单位取整；比例获配不等于最终个人获配。
- 申购日、公告退款日、退款资金可用日、上市日与卖出现金可用日分别记录，不自动猜 T+2 或上市日卖出。
- 最低佣金取 `max(成交额×佣金率, 最低佣金)`，示例假设一次成交。净回款中已扣的费用不得重复录入。
- 情景净收益扣声明的机会成本；现金替代差额直接比较回款，不再次扣同一机会成本。期间收益率不是全年或复利年化。
- 现在补录历史假设标为重建，不计成事前预测；本地时间与哈希不是外部可信时间戳。

详细契约见 [统一设计](docs/design.md)、[现金账](docs/cash-and-evidence.md)、[敏感性](docs/scenario-sensitivity.md)和 [工作台接口](docs/workbench-contract.md)。

## 输出、来源与缺失状态

研究包包括 `report.md`、`report.html`、`input.json`、`result.json` 和 `manifest.json`。HTML 表格经过转义；结构检查不代替完整视觉验收。摘要检查只证明保存内容一致，不认证来源真实性、计算正确性或研究判断。

资料获取、解析、计算、选定原文匹配和视觉状态分列。缺失不填零，冲突不自动选值；失败保留原因和下一步。离线复用记录与重新核对原文分别标注。仅 `capture --online` 主动访问指定来源。

可运行的其他入口：

```bash
python bjx.py compare-cash examples/compare-cash.json --out-dir local-data/cash-01
python bjx.py calendar data/bse-2026-schedule.json --out-dir local-data/calendar-01
python bjx.py public-sample examples/public-sample.json --out-dir local-data/yuelong-01
python bjx.py sample-validation examples/sample-validation.json --out-dir local-data/validation-01
```

公共样本入口复用真实发行字段，但预算及退款资金可用日仍是假设，不认证账户收益。来源和覆盖见 [官方日历](docs/calendar-verification.md)、[悦龙样本](docs/public-sample-920188.md)、[验收矩阵](docs/sample-validation.md)及 [历史档案](docs/history-replay.md)。

## 验证范围

alpha.8 已通过 72 项本地检查及 Windows/Linux、Python 3.10/3.12 检查，包含独立解压包、标准库例子和接口同输入对照。这是工程范围，不是 72 个真实研究样本或预测准确率。

真实发行覆盖为一只、八项选定字段；仍缺第二个发行、全部更正、可信历史首次公开时钟、真实个人余股及到账。报告完整视觉验收与实际账户验收未完成，后者处于用户暂停状态。

```bash
python -m unittest discover -s tests -v
python .github/scripts/check_docs.py
python .github/scripts/check_package.py
```

## 后续路线

优先补充公开发行样本及更正证据，再讨论更完整回放和跨包等价迁移。同行估值、上市后流动性只在指定范围和资料充分时研究，不扩全市场承诺。当前与历史状态见 [路线](docs/roadmap.md)、[开发记录](docs/progress.md)和 [版本变更](CHANGELOG.md)。

## 与其他仓库的关系

本仓库是轻量北交所计算与证据引擎；[research-workbench](https://github.com/KILING-TASI/research-workbench)负责更广的研究组织、资料与报告。当前仅提供 [版本化接口](docs/workbench-contract.md)，不修改主包，也不要求删除尚无等价实现的功能。复用范围见 [适配说明](docs/workbench-integration.md)。

## 许可与第三方资料

两个复用公告模块保留 research-workbench 的 MIT 许可，见 [第三方说明](THIRD_PARTY_NOTICES.md)和 [许可原文](licenses/research-workbench-MIT.txt)。其他代码尚未统一授予开源许可；本次未新增或更换 LICENSE，公开可见不代表获得复制、分发或商用授权。

不附 Wind 数据库、用户账户、私人缓存或完整原公告。行情、公告、研报、商标及外部组件的权利独立适用；代码许可不授予第三方数据使用权。

## 免责声明

仅供学习与研究，不构成投资建议或交易指令，不保证收益、获配或结果准确性。使用前请阅读 [免责声明与使用边界](DISCLAIMER.md)，核对本次来源、日期和假设。
