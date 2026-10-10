# 有限公开回购参考及净费用适配

2026-10-09，PR #1 增量，未发布新版。方法 public-fixing-fee-adaptation.2（.1 为原冻结结果版本）。只有一条 204001 定盘参考，不是全市场报价服务。

## 已核选定字段

[上交所数据页](https://bond.sse.com.cn/data/standard/repocurve/onerepo/)：2026-10-08，利率（T 日）1.392%，页面更新时间 22:30（北京时间）。选定第一利率字段 RATE_1DAY；不把其余均值或其他期限字段当当前利率，不称收盘价。百分数转换后为 0.01392。记录见 [摘要](../data/public-repo-reference/204001-20261008.json)，原始字节 SHA256 和抓取时间保留。原始 HTML 某些中文标签有损坏，数值行、可见表、代码、时间与网页文本交叉核对；不宣称全文正确。

[定盘公式及交收说明](https://www.sse.com.cn/disclosure/bond/ratios/)给出首次交易日后首个工作日为首期结算日；到期日按品种天数并遇非交易日顺延，其后的首个工作日为到期结算日。[通用回购规则](https://www.sse.com.cn/lawandrules/sselawsrules2025/bond/trading/currency/c/c_20250606_10781048.shtml)第二十七条计息自然日区间为首次交收含、到期交收不含，年基数 365。第十一、十二条可核 1 天及代码 204*** 的期限关系。规则页文号 2022 年，2022-04-25 生效；不能把 URL 的 2025 路径当规则生效时间。网页工具无法读取 docx 附件时报告了不支持内容类型；随后通过公开原始附件下载并解包 XML 核对，摘要记录附件哈希；未复制上游全文。

[上交所国庆休市公告](https://www.sse.com.cn/disclosure/announcement/general/c/c_20260915_10832273.shtml)确认 10 月 8 日起开市、10 月 10 日周六休市。选定期间声明交易日为 8、9、12 日，非实际临时停市或清算认证。10 月 8 日 1 天参考对应首期 9 日、到期交收 12 日，计息 3 自然日；接口会校验声明交收与所供日历/期限规则一致，不接受任意计息日期。

## 费用与资金可用声明

本金 100000 元是假设；本金可用 10 月 9 日、利息可用 10 月 12 日为明确研究假设，不认证券商到账。费用公式 max(本金×声明费率, 最低费)+固定费，按分 ROUND_HALF_UP；毛利息也用显式研究取整约定，不认证券商实账取整。示例费率 0.00001，最低/固定 0，于 10 月 8 日支付，为 1 元；不是公开报价带来的券商收费事实。结果：毛利息 11.44，假设费用 1.00，参考净额 10.44 元。

fee.status=unknown 时仅展示毛利息，净额和现金计划阻断；不能默认费用为零。费用高于毛息时保留负参考净额。现金计划同时保留毛利息与单独费用事件，防重复扣费。现金比较另有 idle 方案，初始 100001 元预留当日费；若只有 100000 元，投入/付费同日组现金不足，不能先借未来释放资金。不自动将此日定盘延伸到整段 IPO 占款或滚动再投资。

```text
python -S bjx.py repo-reference examples/repo-reference.json --out-dir local-data/reference-01
python -S bjx.py compare-cash examples/public-reference-cash.json --out-dir local-data/reference-cash-01
python -S demo.py --out-dir local-data/reference-demo-01
```

默认离线状态 saved_review_record_not_rechecked；可明确传 raw_quote_path 对原始哈希与选定数值锚点复核，输出 exact_hash_and_selected_numeric_anchors_match。哈希和记录可修改，不是签名或独立可信时钟。错误通过现有研究包留 blocked 原因，不用教学 2% 回退；源抓取必须明确 --online，只新增官方 bond.sse.com.cn 允许域，重定向仍校验。

公开参考晚于当日交易收盘，不是事前可得样本；不声称以此成交、不计算真实账户收益。真实账户验收继续暂停。成交盘口、账户净费率、实际到账、其他日期与期限仍未知，余股未知。原创计算代码 MIT，选定公开数值及原始资料权利独立；本仓库只保存字段摘要、来源及哈希。

方法约束、历史分布与选择偏差见 [资金与历史统计方法卡](funding-history-methods.md)。明确免佣和取整为零的毛息仍保留数值，仅省略零现金移动，不将未知费用填零。
