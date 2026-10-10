# alpha.9发布准备

候选软件版本v0.2.0-alpha.9 / Python0.2.0a9，未发布。基于已集成main81bdd2b，不增加算法。接口API1.0、核心计算方法alpha.8、规则/资料/历史快照版本各自不变。根MIT与上游完整许可、第三方数据权利保持。

交付源码ZIP、wheel和sdist。源码ZIP/sdist含demo、examples、data与文档资源；wheel仅计算模块。普通构建依赖声明setuptools>=77，计算运行标准库；可选PDF extra pypdf6.14.2，不安装工作台。无.git、build缓存、私人输出、账户或原始PDF。

候选资产保存于本任务outputs/bjx-alpha9-release-candidate，SHA256及构建提交写入assets.json；独立安装最短demo/wheelAPI及必要失败回执分开保存。最终main合并SHA若改变，须重新从精确main构建核验，不把PR资产自动当最终标签资产。总调度执行审合/tag/Release/旧分支清理，本任务不发布或删除。

发布后README拟调整：将“本次软件包候选……尚未发布”改为“当前软件发行版为v0.2.0-alpha.9”，拟发布入口改正式下载链接；保留wheel/源码资源差异、计算方法alpha.8/API1.0、旧资产冻结与缺口。发布前不声称已下载。

本批没有未提交草稿需要丢弃或纳入算法；原工作区干净。公开发行仍只有920188一只八字段、回购一条参考；教学预算不计真实覆盖。真实账户暂停，完整更正/历史时钟、年度和预测未认证。安装发现/视觉/实时取数不在发布验收。

## 正式发布补记 — 2026-10-10

[v0.2.0-alpha.9](https://github.com/KILING-TASI/bjx-ipo-engine/releases/tag/v0.2.0-alpha.9)已由总调度发布，最终构建main为d0b4b566b66e9644a22865e67dd447eca9c891fb。三种资产及SHA256SUMS.txt已上传；源码ZIP摘要48e70c8e8f324689b02f011926ff0da8dd48d10195ef46a2c41e6b07dbf383c9，wheel摘要32479524051e2b4465c5b322c73519c82faa04714f57cd6e841608c8b2370a45，sdist摘要022c3e3e651bc958ec296d778cf51b66ad8d75413075fa517502f84e33262ed1。本条核查Release元数据/已上传状态，不声称重新下载安装；本地最终资产独立验收范围保持原记录。上文候选准备为历史过程，不改写旧回执或版本。
