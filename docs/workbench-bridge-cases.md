# 有界可选桥接：固定输入验收

2026-10-09，PR #1 增量，未合并或发布。工作台任务已收到本次用户授权的协调消息。本页区分独立接口测试、工作台原生桥接和旧工作台计算等价，三者不能互相替代。

## 输入与输出协议

本轮只用引擎原生 API 1.0 的 scenario.v1 / cash_ledger.v1。完整请求、请求 SHA256、完整预期响应和版本保存在 [九条固定案例](../examples/bridge-cases.json)。全部教学输入，真实样本数 0；不含账户资料、真实配售/到账认证或概率模型。

独立引擎仍为 0.2.0-alpha.8。原生情景本金/价格/费率是 JSON 数值；配售率和涨跌幅是小数比率，币种口径人民币元，股数单位股。全部费用和申购/退款可用/卖出现金可用日期显式给出，不默认税费或 T+3。正例去掉情景权重，不计算期望。比例整手与条件额外百股分支分别保留；条件分支不是实际个人余股。

工作台可以在自己的外壳里新增说明、输入版本和提交信息，但须保留 engine_response 的完整原生响应，含 API/引擎版本、input_sha256、status/result/error 和 warnings。不得截取净收益后丢弃未知余股或日期假设。声明计算 completed_with_limits、现金约束 infeasible、格式/版本 failed 必须区分，不能将拒绝补零或当成功。返回值的精确字符串/浮点类型保持，不静默舍入。

[现有版本契约](workbench-contract.md)仍适用。只读核对的工作台旧入口还有滑点、融资、百分数字符串和年度功能；本轮原生桥接不自动转换这些字段。非零滑点/融资或年度输入须留在旧入口或明确拒绝，不丢字段强行宣称等价。真实账户验收继续暂停。

## 九条联调案例

|案例|应保留的行为|
|---|---|
|joint-unweighted|无权重联合情景；完整收益/成本/未知余股限制|
|announcement-cap|先按发行上限截断股数，再算比例整手|
|retained-principal-ledger|退款后获配本金未结，不能变成完整账户已实现收益|
|same-day-shortage|现金不足停止，没有部分执行/自动融资|
|missing-refund-cash-date|拒绝；不猜可用日|
|missing-explicit-fee|拒绝；不把最低佣金缺值补零|
|wrong-native-number-type|拒绝；数值字符串不是原生数值输入|
|annual-operation-unsupported|拒绝 annual.v1；工作台年度入口不能被此接口替代|
|api-version-mismatch|拒绝未知 API 版本|

```text
python -S .github/scripts/check_bridge_cases.py --out-dir local-data/bridge-native-01
```

验收程序逐条用隔离子进程跑原生 stdin 协议，核对完整冻结响应及退出码。可显式给 --bridge-command-json 的 JSON argv 列表调用外部工作台 stdin 桥接；不使用 shell、不复制上游代码、输出另存。外部响应可直接是原生响应，或保留 engine_response 的外壳。更早的工作台入参拒绝应另记原因，不当作原生响应完全等价。

原生九条固定输入验收及下文所列工作台原生透传联调已经通过；workbench_checked=false 仍仅表示该次记录没有完成外部验收，不证明工作台旧实现等价。本轮不修改旧冻结输入/结果，无 annual.v1、真实个人余股或真实账户验收，也不扩大预测能力。

## 更严格的工作台入口边界

另有 [三条边界反例](../examples/bridge-boundary-cases.json)：额外滑点、融资率、年度发行只数。现有冻结 API 对这些未知字段会忽略，因此其 native 状态可能 completed_with_limits；这不能证明该参数参与计算。可选桥接须以字段白名单明确拒绝，不静默删除字段后计算。这三条验收的是 adapter 拒绝，与九条原生完整响应一致分开，不要求修改原生旧行为或伪造 native failed。概率模型和年度功能不进入此边界。

## 旧实现有限交集实跑

等待原生桥接期间，只读使用工作台已有 subscription_scenarios.evaluate 实跑前两条教学正例，每条三个联合情景。原生请求另外经 api.py 实跑并核对冻结响应；工作台请求使用显式单位映射：小数费率/涨跌幅乘 100 变成百分数字符串，滑点、融资率和借入占比明确声明零，合成代码 990000 仅作教学身份。

[实跑字段及两侧输入](../examples/bridge-legacy-overlap.json)保存了两方提交、工作台实际源码摘要及 36 个选定数值比较。整手股数、卖出费用、机会成本、本金日数、扣机会成本前现金利润和扣成本后净收益在绝对 1e-8 容差内匹配；股数身份需相同，无概率权重，无个人余股认证。完整 JSON 类型/字段不同，因此 full_result_equivalent=false。账户本金收益率、工作台预算/资金日年化分母、年度以及非零滑点/融资均未比较，也不将本次显式对照映射部署为生产桥。

## 已提交入口联合验收（2026-10-09）

工作台 PR #6 提交 `32e42b41a33688a47decd2540d823ff475b19b44`，网关 `scripts/bounded_engine_gateway.py` 实际 SHA256 `38123e66d683441a226987ab00ed6c25941615d222eee3f6769f871302c14945`。独立引擎本次实跑提交 `fe49372`，API 1.0 / 引擎 0.2.0-alpha.8。工作台方法 bounded-native-gateway-1；原生计算接口保持冻结。此前 801f224 / a2b80e 的运行记录留档，不作为新源码验收。

九条完整 engine_response 均与同输入独立 api.py 及冻结快照相等；请求原始字节 SHA、原生 input_sha256、API/引擎版本、两方提交、网关 SHA 和原生退出码核对通过。completed_with_limits / infeasible / failed 不混用；失败原生响应完整保留，未变成成功。三条额外滑点、融资率、年度字段在工作台边界明确 ValueError 拒绝，无原生结果，不声称与旧 permissive 行为等价。新验收包与历史包分开，manifest核验通过。

[联合摘要回执](../examples/bridge-joint-receipt.json)保存每例状态/输入摘要/退出码及三条拒绝原因。此回执只覆盖 BJX，不为组合、可转债或规则引擎验收，也不声明旧工作台完整模型/年度等价。全部是教学输入，账户继续暂停；个人余股、实际到账及无证据期望收益不补齐。

工作台可选原生调用（在其仓库目录内，显式指定可信本地引擎目录，REQUEST.json 为上述完整原生请求）：

```text
python scripts/bounded_engine_gateway.py bjx --project-dir ENGINE_DIR --input REQUEST.json --out-dir NEW_DIR
```

该入口不下载安装引擎、不自动替换原内置专题。完整跨进程核对使用本仓库 check_bridge_cases.py 和只供验收的 stdin→临时请求文件→工作台 run(...) 包装；包装不转换单位、不改字段，并按 native-response-preserved/blocked 保留退出状态。三条入口拒绝另记，不将其伪造为 native failed。联调不需要也没有请求真实账户材料。
