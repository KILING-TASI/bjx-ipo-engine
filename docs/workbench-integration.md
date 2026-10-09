# research-workbench能力适配

## 本次补入

固定参考research-workbench公开提交051846168d7590991c75afc001abb97a89b1d3ed。复用范围限北交所和共用证据、交付方式，没有搬入基金、公司、宏观的整套依赖与私人数据。两个公告比较模块保留原MIT声明，其他能力通过轻量适配实现。

| 上游优势 | 本仓库落地 |
|---|---|
| 输入与报告版本绑定 | input/result/report文件SHA256及大小清单，verify检查改动、遗漏与额外内容 |
| 各研究阶段分列 | 获取、解析、计算、来源核验、视觉检查分别记入manifest，不自动升级状态 |
| 来源与公告版本核验 | 主动来源保存、预期摘要拒绝变更、候选事实绑定精确PDF字节 |
| 更正线索与原文比较分开 | versions仅检查声明的同证券标题；compare-pdf比较整份提取文本、保留页码和所有差异 |
| partial与失败记录 | 计算结果保留限制；缺依赖、输入错误和请求失败生成blocked研究包及下一步 |
| 独立安装和公开发布 | Windows/Linux、Python3.10/3.12自动检查，独立解压Git发行包、禁用site-packages运行基础例子 |

## 来源保存

准备输入JSON：`{"url":"https://www.bse.cn/fxrz_list/200025384.html"}`，保存为source-input.json。

```bash
python bjx.py capture source-input.json --online --out-dir local-data/source-01
python bjx.py verify local-data/source-01
```

可增加expected_sha256，必须为64位小写摘要。不同即失败，不静默替换旧资料。允许北交所、上交所、深交所及指定巨潮域名HTTPS；重定向也检查域名，拒绝凭据、非标准端口、超10MiB内容和伪PDF错误页。不绕过403、验证码、权限或访问限制。下载HTML可能只是访问提示，仍须人工阅读。

报告只写captured_not_verified。source.pdf/source.html/source.txt保存取得字节，result.json保存初始与最终URL、时区抓取时间和摘要；没有承诺HTML已解析、扫描件已识别或当前规则已适用核验。

## 事实绑定精确原文

facts输入可增加source_files：每项为id、path、sha256、url，最多5份10MiB以内PDF。字段候选增加source_id及document_sha256；须与该来源字节及URL一致，否则失败。包内保存original-000.pdf等附件，来源声明仍需核实。

绑定不自动选择冲突值，resolved_value仍为空。页码、数值、规则适用性与发行身份仍需人工复核；当前没有OCR或自动字段语义认证。所有本地附件须由调用者明确提供，不扫描私人目录。

## 公告版本

```bash
python bjx.py versions examples/versions.json --out-dir local-data/versions-01
```

documents含security、title、date、url；所有文档必须属于同一声明证券。该命令不联网，也不认证声明身份。出现“更正”等标题生成正文比较需求；无标题线索不证明没有更正。不会按最新日期自动覆盖已登记事实。

PDF比较按需安装本地已验证版本pypdf6.14.2：

```bash
python -m pip install pypdf==6.14.2
python bjx.py compare-pdf compare-input.json --out-dir local-data/pdf-diff-01
```

compare-input.json含before、after两份本地PDF路径、issuer_name与六位security。读取开头页检查声明主体和代码，拒绝空白/扫描页；比较全部提取行，输出差异块与页码。提取文本可能遗漏图片及表格结构，semanticReviewComplete始终为false。标题关系、提取字节、正文差异、人工语义复核是不同阶段。

## 检查边界

verify仅证明内容与当前manifest一致；manifest可被修改，不提供独立可信时间戳或防恶意联合改写的保证。HTML采用转义后的标题与表格阅读版，未认证完整视觉排版。研究包、原文附件与用户输入只放local-data或用户指定新目录，不作为公开发布附件。

2026-10-09基础流程在禁用site-packages后独立运行通过；32项计算、输入、摘要、更正线索及PDF提取差异检查通过。真实北交所规则网页字节主动获取成功，仅证明当次来源可获取，未核验整份适用规则。私有账户数据、官方日历和完整v0.2业务验收仍未完成。
