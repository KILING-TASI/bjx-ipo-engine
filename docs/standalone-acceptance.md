# 单仓独立安装验收

2026-10-10 有界独立批。新目录、新虚拟环境、非 editable wheel 安装，只用本仓 git archive；没有复制其他仓、作者缓存或原始公告。宿主仍有其他仓和系统 Python，这是目录/进程隔离，不是全新 OS。

## 可重复流程与环境

在本仓运行 `python .github/scripts/check_standalone.py --out-dir /absolute/new/acceptance`。新目录中源码归档、构建 wheel、独立 venv、报告与 acceptance.json 分开。子进程清除 PYTHON*/RESEARCH_WORKBENCH*/CODEX*/BJX* 路径变量，空 HOME/USERPROFILE/应用缓存仅覆盖任务环境，不修改系统或删除缓存；禁用 pip 缓存和用户配置。声明构建依赖 setuptools>=77，计算运行依赖为空。wheel 非 editable 安装，不装其他自家仓；标准库路径来自宿主 Python 属于允许运行时。

验收在归档之外以 `python -I -m api` 真正计算例子，核模块 origin 位于新 venv；以 `python -S demo.py --out-dir NEW_DIR` 在解压单仓根目录完成 README 最短流程，核 demo/engine/audit origin 位于该归档。两条路径分开，wheel 不含 demo 和示例资源；这是明确打包范围，不宣称 wheel 单文件完成源码 demo。

## 已核项目和失败例

新报告保存输入、结果、HTML 与内容摘要，核一只真实发行字段记录及教学预算边界；204001 假设本金费用示例毛息11.44、净参考10.44，与声明方法一致，非真实账户收益。核 API 1.0、核心0.2.0-alpha.8、根 MIT/第三方完整许可及 Markdown 资源链接。输出文件摘要逐一匹配，不认证来源真实性。

实际运行输出目录已存在被拒绝；缺 pypdf 的实际 public-sample 原文入口返回 blocked 和缺组件原因/下一步，不填零。本例用本地占位文件触发依赖检查，未重新取得或公开公告；没有验证安装可选 PDF 后的成功取数。

完整命令、退出码/输出、sys.path/模块来源、包摘要与依赖版本在验收目录 acceptance.json；不可用 help 或普通测试代替。源码与 wheel 使用当前提交生成，各次包摘要以各自回执为准。远端 CI 每个任务仅 checkout 本仓，重复同一独立流程并保存回执/报告；CI 状态必须在运行后记录，不能以配置存在当已执行。

## 范围与结案

待审源码归档的最短 demo 与已安装 wheel 计算通过；已发布 Release 本批未实际解压安装，不冒称同样通过。无 Skill 包或自然语言发现验收，无新视觉/浏览器验收，无联网取数，无真实账号（用户暂停）。只补安装范围说明和验收脚本/CI，不新增计算功能。沿用 PR #1，不合并、发布或自动安装用户 Skill；本批以独立运行回执和明确余项结案。
