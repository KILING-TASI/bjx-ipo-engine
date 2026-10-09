# 历史发行档案、假设冻结与复盘

## 已有能力

已有事实候选、精确原文摘要绑定、公告版本比较、2026官方计划日历、显式多发行现金账和机会成本情景；本次复用它们，不新增未经验证的中签率模型。

## 首批新增：三个分离入口

```bash
python bjx.py freeze examples/freeze.json --out-dir local-data/frozen-01
python bjx.py archive examples/archive.json --out-dir local-data/actual-01
python bjx.py review review-input.json --out-dir local-data/review-01
```

### freeze

输入security、input_kind、information_cutoff、subscription_at、information_sources、assumptions。假设沿用情景测算完整契约。每项信息来源提供唯一id、basis及带时区available_at；晚于截止时间的来源拒绝。截止时间不得晚于现在或申购时间，假设中的申购日期须匹配声明申购时点。

frozen_at从本次实际本地时钟取得，不接受回填冻结时间；保存假设和摘要。现在补录已发生发行或声明historical_reconstruction时，记录必为历史重建。即使在申购前本地保存，也只是local_pre_subscription_snapshot；没有独立时间戳，不能证明外部首次公开或全部假设确实在当时可知。输入不得复用实际结果伪装成事前预测。

### archive

单独保存公开发行价、网上有效申购股数、网上发行股数、网上配售率、申购日期、公告退款日期和上市日期候选。字段限定在公开发行范围，不读取实际账户获配、资金可用或券商交易记录。input_kind为teaching或public_disclosure；后者必须将每项非空候选绑定原文PDF字节、来源URL、日期与定位。

candidate、单位、来源与规则版本完整保留，不自动裁决冲突。未知字段空候选列表，不补零。退款公告日不等于券商到账日，上市日不等于用户实际卖出日。余股未知独立标注。登记与原文摘要绑定成功不认证人工录入数值正确、实际规则适用或全市场完整覆盖。

### review

输入frozen_bundle、actual_bundle、comparison_values；证券身份须一致，两份包内容校验须通过。首批仅比较发行价和配售率，比较值必须已经存在于快照且单位匹配，不能根据实际结果再挑新预测值。compare值可以选择已保存某个配售率情景，但这不是选模验证或预测准确率。

缺值、冲突或单位不匹配时误差留空。数值可比较的已登记候选仍标recorded_unverified，差异不是原文已核准确度。事后档案不替换事前输入；复盘记录两份输入及结果摘要，原研究包独立保留。

review-input.json示例：

```json
{"frozen_bundle":"local-data/frozen-01","actual_bundle":"local-data/actual-01","comparison_values":{"issue_price":{"value":18,"unit":"CNY/share"},"online_allocation_rate":{"value":0.00033,"unit":"fraction"}}}
```

## 多发行现金与机会成本

review可附cash_comparison（沿用同本金/同期间两个显式计划），cash_basis只能为teaching或public_proportional_reconstruction。计划可包含多发行占用，但不会从公告配售率自动恢复实际个人获配或交易。

可附opportunity_cost_rate，须等于已冻结的资金成本年率。按声明资金日另算机会成本与扣成本现金盈亏；撞资时留空。现金替代差额仍用原现金对照值，不再减这项成本。现金重建为独立明确输入，不自动认证其与发行档案的对应关系。完整年度样本、实际账户验证和真实预测效果不在首批完成范围。

## 验收与暂停

首批工程验证涵盖历史补录标签、未来信息拒绝、无时区拒绝、冲突缺值、主体/单位/快照比较限制、内容篡改检测、现金与机会成本分列、独立安装包。示例为教学资料，没有新官方发行原文逐字段验收。本地摘要不抵抗输入及manifest联合伪造。

真实账户验收继续按用户要求暂停，不读取或索要账户资料，不自动恢复。后续优先核对一只明确公开发行的原公告及发行结果字段，再扩可复查公共样本；不能把工程测试数当研究样本数。

## 后续具体范围

- 同行估值：先指定同行池、行业及估值日期、发行PE利润口径，核对招股书同行原文；缺少可比口径不排名，暂不做全市场估值模型。
- 上市后流动性：先观察上市后1/5/20个交易日的成交额、换手及缺失，使用公告上市日期和有来源行情；成交不足或数据缺口单列，不输出未经回测的卖点。
- 历史回放：完整发行区间、版本和公告可得时点，事后回放与事前冻结样本分别统计，余股未知保留。不提前训练或宣称中签率模型改善。

调研文件中的“零竞争”等搜索结论未经复核，本项目不将其纳入事实、推广文案或验收依据。
