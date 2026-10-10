# 引用与复用说明

以下文件从research-workbench公开仓库复用，保留MIT授权及版权声明：

- vendor/announcement_versions.py
- vendor/compare_original_versions.py

来源：[KILING-TASI/research-workbench](https://github.com/KILING-TASI/research-workbench)，固定提交 `051846168d7590991c75afc001abb97a89b1d3ed`，原路径 `modules/bjx-newshare-toolkit/scripts/`。原始版权：Copyright (c) 2026 research-workbench contributors。完整许可见[research-workbench MIT](licenses/research-workbench-MIT.txt)。

严格输入、研究包、阶段状态与报告绑定方式参考同项目设计，新增适配代码位于audit.py及bjx.py。依赖pypdf仅在PDF比较时按需安装，未随本仓库分发，其许可独立适用。

复用许可不授予行情、公告、研报、商标或用户附件的再分发权。来源下载只保存用户主动请求的公开资料，研究包及原文应放local-data中；不要将私人账户、研究记录或无权分享的原文提交到GitHub。

## 原创及第三方范围清单

用户于2026-10-09授权本仓库原创代码和有权授权的原创说明采用根[MIT许可证](LICENSE)，权利人标识沿用仓库所有者KILING-TASI。不改变上游两个文件的版权及许可。

| 范围 | 处理 |
|---|---|
| 原创Python计算、接口、报告/demo代码及原创说明 | 根MIT；计算版本保持alpha.8，包装元信息采用PEP 440的0.2.0a8 |
| vendor/announcement_versions.py、vendor/compare_original_versions.py | research-workbench原MIT、版权及固定提交来源保留；完整许可在licenses目录 |
| data目录的官方排期、发行字段与来源记录 | 公开资料数值摘要和证据定位，不整体授予MIT文档/行情再分发权 |
| docs/preview和screenshots中的混合展示 | 原创布局/生成代码适用MIT；公开字段及其来源独立，截图不是原公告页图，不包含账户、字体或第三方logo |
| 原公告PDF、行情、研报、品牌、字体、库 | 按各自权利范围处理；原文全文不随包分发，pypdf等组件不随源码内嵌，仅按需依赖 |

未发现本轮仓库误附账户、商业数据库、原文全文或私人缓存；这是本次文件清点范围，不承诺全部外部资料授权已认证。来源摘要与链接保留，不因许可整理删除证据。来源或权利不明确的后续材料不得仅改署名后视作原创，应先隔离、链接或确认范围。

本轮许可改动在主分支，旧发行包仍保持旧版冻结；不自动创建新版本。免责声明不替代许可证，也不将第三方数据变成MIT授权材料。

本轮新增研究复查、报告说明及合成教学为作者原创MIT；同作者随包通用I/O代码独立保留，不要求其他仓库安装。规则有限事实和来源链接不改变原文权利；未捆绑实际公告/研报PDF或私人账户资料。
