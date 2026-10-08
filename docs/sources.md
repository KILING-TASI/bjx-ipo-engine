# 来源与参考项目

核对日期：2026-10-09。链接用于规则依据和设计参考，不保证后续规则不变，也不替代逐只适用公告核验。

## 规则来源

- [北交所证券发行与承销管理细则发布公告](https://www.bse.cn/fxrz_list/200025384.html)：第十一条描述比例配售及不足百股部分按数量优先、同数量时间优先分配。当前实现仅覆盖比例整手部分。
- [上交所债券通用质押式回购交易指引](https://www.sse.com.cn/lawandrules/sselawsrules2025/bond/trading/currency/c/c_20250606_10781048.shtml)：实际占款天数按首次至到期交收日期计算，不能以名义期限代替。
- [上交所2017年回购新规说明](https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/c_20170519_4313753.shtml)：提供跨节假日实际占款示例。历史说明用于理解机制，非当前报价来源。

## 类似项目

| 项目 | 可参考部分 | 适用边界 |
|---|---|---|
| [ipo-allotment-predictor](https://github.com/thesky30/ipo-allotment-predictor) | 数据时点隔离、公告抽取、扩张窗口回测、预测展示 | 主要是网下中签率；README自述结果未独立复验，不能套到网上配售 |
| [AKShare](https://github.com/akfamily/akshare) | 新股、配售和行情数据接口 | 逐项核验北交所覆盖、单位与历史完整性；首版不依赖联网接口 |
| [a-stock-data](https://github.com/simonlin1212/a-stock-data) | 日历、公告、多源降级 | 不同数据源对北交所覆盖不同，公开字段不等于原文已核验 |
| [xgzh](https://github.com/youzi530/xgzh) | 打新卡片、日历、前后端组织 | README标注All Rights Reserved，不复制其代码 |
| [ipo-ai](https://github.com/gagandt/ipo-ai) | 历史IPO数据与相似案例展示 | 印度市场制度不可直接套用 |

本仓库未复制以上项目代码或附带第三方数据；用户设计稿中的市场样本数、收益率、默认行情参数未作为事实采纳。
