# 北交所打新研究引擎

面向北交所网上发行的获配、现金占用与净收益情景研究。由四份设计材料整合修订，首版交付可运行的测算内核与统一设计规范。

**当前版本：v0.2.0-alpha.7，研究预览版。** 不含交易执行、自动申购、经过验证的预测模型或实盘收益承诺。教学示例不代表真实新股；data包含已核对的官方排期及一个公开发行样本，核验范围与资金假设分别标注。真实账户验收按用户要求暂停，其他公开资料工作继续。

## 已实现

- 根据预算、公告申购上限与100股单位计算有效申购金额。
- 成对输入配售率及上市涨跌幅，计算比例整手获配、卖出费用与资金成本。
- 支持无权重情景比较；只有声明完整概率及依据才计算加权期望、标准差与亏损概率。
- 比例整手为零仍计资金成本；不足百股余股获配保留未知。
- 使用显式申购、退款可用和卖出现金可用日期，包含获配本金后续占用。
- 输入校验、可复现教学示例与 GitHub Actions 检查。
- 发行事实候选登记：保留来源、单位、缺失和冲突，不自动认定原文已核验。
- 多只发行及回购事件现金账：同日冻结冲突、退款、获配本金留存、卖出回款。
- 显式交易日历覆盖检查，以及逐笔回购实际交收日计息。
- research-workbench优势适配：研究包绑定、来源保存、事实候选原文哈希绑定、公告版本线索和PDF正文差异比较。
- 获取/解析/计算/原文核验分别记录；失败保留原因与下一步，不用成功状态掩盖缺口。
- 同本金、同期间的两个显式现金方案对照；费用单列、精确小数现金保存，撞资或未回收本金时不比较盈亏。
- 根据已核对的北交所2026年度与专项休市公告生成计划交易日历，调休工作周末保持休市。
- 盈亏平衡卖出涨幅与额外100股条件敏感性，费用和留存本金重新计算，不虚构余股概率。
- 历史发行档案、事前本地快照与事后复盘分离；补录标为历史重建，信息时点与来源缺口保留。
- 一个官方历史发行样本：悦龙科技920188，八项字段/来源/版本核验记录、配售率复算及假设现金占用回放。

## 快速开始

Python 3.10及以上，基础情景、现金账和证据包无第三方依赖；PDF正文比较按需安装pypdf。在项目目录运行：

```bash
python engine.py examples/scenarios.json
python engine.py examples/scenarios.json --output result.json
python research.py facts examples/facts.json
python research.py ledger examples/ledger.json
python -m unittest discover -s tests -v
```

统一入口生成可读报告、输入快照、结果及摘要清单：

```bash
python bjx.py scenarios examples/scenarios.json --out-dir local-data/scenarios-01
python bjx.py facts examples/facts.json --out-dir local-data/facts-01
python bjx.py ledger examples/ledger.json --out-dir local-data/ledger-01
python bjx.py versions examples/versions.json --out-dir local-data/versions-01
python bjx.py compare-cash examples/compare-cash.json --out-dir local-data/cash-comparison-01
python bjx.py calendar data/bse-2026-schedule.json --out-dir local-data/calendar-2026-01
python bjx.py public-sample examples/public-sample.json --out-dir local-data/yuelong-01
python bjx.py verify local-data/scenarios-01
```

每份研究包含report.md、report.html、input.json、result.json和manifest.json。SHA256检查证明保存内容一致，不是数字签名、可信时间戳、来源认证或研究判断认证。HTML为转义后的标题与表格阅读版，结构检查不代替完整视觉验收。联网来源仅在capture模式主动指定--online时访问。

输出文件必须为新文件，避免覆盖研究记录。金额单位人民币，所有费率和收益率均为小数，例如0.0005表示0.05%，1.2表示120%。

真实使用时须替换示例发行价格、公告申购上限、现金日期、费用、情景及其依据。日期由调用方核实，不自动假定T+2；佣金、税费和券商舍入也应按实际发行期间与账单核实。

## 如何理解输出

`proportional_hands` 为比例部分百股手数；`probability_zero_proportional_hands` 为输入情景权重下比例整手为零的概率，**不等于最终零获配概率**。余股按申购数量与时间排序，当前未建模。破发时额外获配也可能增加损失。

`net_profit` 扣除了声明的机会成本；`account_period_return` 用账户本金作分母，只覆盖本次发行期间，不是全年或复利年化。未计算闲置现金收益，未默认叠加融资成本。

`listing_return` 当前为固定情景卖出收益假设，不代表首日卖点预测。最低佣金按 `max(成交额×佣金率,最低佣金)` 计算；示例假设一次卖出成交，没有分批最低费用。

## 文档

- [统一设计与模块边界](docs/design.md)
- [原方案纠错与版本变更](docs/corrections.md)
- [规则来源与类似项目](docs/sources.md)
- [开发路线和验收标准](docs/roadmap.md)
- [现金账和发行事实接口](docs/cash-and-evidence.md)
- [开发接续记录](docs/progress.md)
- [从research-workbench补入的能力与使用方式](docs/workbench-integration.md)
- [同期间现金方案对照口径](docs/cash-comparison.md)
- [官方交易日历核验记录](docs/calendar-verification.md)
- [盈亏平衡与余股敏感性](docs/scenario-sensitivity.md)
- [历史档案、冻结与复盘](docs/history-replay.md)
- [首个官方样本：悦龙科技](docs/public-sample-920188.md)

## 发布与复用

本仓库复用research-workbench的两个MIT许可公告比较文件，来源固定提交、版权及许可见[第三方说明](THIRD_PARTY_NOTICES.md)。不附Wind数据库、第三方公告附件或作者私人缓存。其他代码尚未统一授予开源许可证；公开可见不代表取得其复制、分发或商用许可。后续授权由仓库所有者决定。

研究输出不构成投资建议。实际配售、现金到账和费用以适用规则、发行公告及账户记录为准。

## 免责声明

本项目仅供学习与研究，不构成投资建议或交易指令，不保证收益或结果准确性。请在使用前阅读[免责声明与使用边界](DISCLAIMER.md)，并结合本次数据来源、假设与缺口独立判断。代码许可不包含第三方数据使用授权。
