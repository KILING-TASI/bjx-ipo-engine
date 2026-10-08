# 发行事实与现金账预览接口

## 事实候选

`python research.py facts examples/facts.json`

`security`标识证券，`rule_version`保存适用版本声明，`required_fields`列出必需字段。`fields`每个字段为候选列表，空列表代表缺失。候选须有value、unit、basis、source。basis可为original、third_party、assumption、derived。

原文/第三方候选还须有HTTPS来源、document_date、带时区的retrieved_at和locator。派生候选须有dependencies。当前只校验元数据结构，不下载或核对原文，不追溯派生依赖，也不自动消除单位差异。

相同值和单位记为recorded_unverified；不同候选或不同单位记为conflict。resolved_value始终留空，禁止将登记成功称为已核验发行事实。原文抽取、哈希绑定与人工裁决在后续版本实现。

## 现金账

`python research.py ledger examples/ledger.json`

`initial_cash`为期初可用现金；不自动加入期初已冻结资产、信用额度或外部资金。`calendar`声明覆盖起止日、完整有序且唯一的交易日期、source与basis。模块不凭周末和调休推断交易日，也不认证日历完整性。示例仅教学日历。

事件含唯一id、instrument、date、kind、amount与evidence，金额以人民币小数输入，可用字符串保存精度。事件类型：

| kind | amount与状态 |
|---|---|
| freeze | 冻结申购本金，减少可用现金，增加该发行留存本金 |
| refund | 退回未获配本金，不能超过该发行留存本金 |
| sale | 扣费后净现金回款；principal_released另列卖出对应本金，回款可为零 |
| repo_open | 逆回购投入本金，减少现金 |
| repo_principal | 本金重新可用，不计作收益 |
| repo_interest | 输入净利息到账，需此前有对应回购投入 |

不会根据发行配售预测自动生成账户成交记录。同一instrument应为单只发行或单笔回购独立身份；不恢复卖出剩余股数、券商账单舍入或余股配售。

同日事件全有非负整数order及timing_evidence时，按order依次执行。同一order的投入仍先检查已有可用现金，不使用该组同时释放资金。只要当日任一事件缺顺序证据，整日退回先投入、后释放的保守规则。声明为assumption的顺序仅代表教学假设，不代表真实到账认证。

同组投入合计超过现金时，返回executable=false和缺口，停止回放，不替用户选择执行哪只，也不扣减部分订单。此时final_available_cash为冲突前余额，**不是计划期末余额**。金额不足、不可能退款、超出日历和重复事件需修正输入，不能以零兜底。

## 逐笔回购利息

`research.repo_interest(trade, Calendar(calendar))`，CLI为`python research.py repo INPUT.json`。

trade必填principal、annual_rate、fee、trade_date、principal_available_date、first_settlement_date、maturity_settlement_date、evidence。日期均须落在声明交易日历内。

实际占款天数=到期交收日−首次交收日的自然日差；利息=本金×年率×天数/365−费用。本金可用日与利息到账日分别作为现金事件输入，不能当作同一日期。当前不自动推导期限交收规则，不内置报价，不将利息计算成功称为券商账单认证。

现金账原始回款不扣机会成本。未来现金方案对照应在同本金和同区间比较真实净回款，避免从已扣机会成本收益再次扣对照现金收益。
