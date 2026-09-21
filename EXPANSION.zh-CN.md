# AI 工程面试题库：扩展版

从 [公司/主题索引](expansion/README.md) 开始，或下载后在本地浏览器打开 `expansion/index.html` 离线检索。原 README、许可证与作者署名保留。实际数量以 [统计](expansion/stats.json) 为准，不采用其他题库自称的题数。

当前快照：4,546 个索引条目，其中原 README 提取候选 517 个、新收集公开题库候选 3,879 个、原创中文场景练习 150 个。共登记 42 个资料仓库，按 70 个公司标签和 20 个主题标签组织。标签可以重叠，不证明公司真实考过对应题目。

## 证据类型

| 类型 | 含义 | 限制 |
|---|---|---|
| `legacy_unverified` | 原 README 中提取并继承的候选 | 未重新验证原文 Asked at 声明；不是对原文全部题目的人工普查 |
| `community_question_bank` | 公开题库中提取的候选 | 经过规则清理和抽查，仍需编辑审核，不是已验证公司真题 |
| `derived_practice` | 本次原创的 150 道中文工程场景练习 | 30 个公司定向专题；不是面经，背景阅读不是考过的证据 |

公司标签来自原文分组、Asked at 声明、源文件名或练习目标。原文共用公司分组可以产生多个标签，但不代表各公司都独立考过该题；关联性质见条目的 `company_relation`（存在时）。未知面试日期为 null，转载次数不是独立验证次数。

## 查询与文件

包括公司与主题 Markdown 页面、`questions.json`、来源与许可证、面经线索、单文件离线搜索，以及 Python 查询和构建工具。

```bash
python tools/question_bank.py stats
python tools/question_bank.py search "cache" --kind community_question_bank
python tools/question_bank.py search --company "Snowflake"
python tools/question_bank.py search --topic agents --limit 100
python tools/question_bank.py validate
```

查询已生成的数据需要 Python 3.10+，不需要网络、API key 或第三方 Python 包。浏览器离线页面不需要 Python。每题有稳定 ID、类型、主题和原文链接；自动采集记录固定到源 commit SHA、文件和行号。原文可能有答案，本扩展不复制长答案，也不背书答案正确性。

## 清理与复用边界

42 个来源中，13 个通过许可规则并执行扫描，其余 29 个仅保留链接；扫描成功不表示每个来源都有新增题目。许可允许列表为 MIT、Apache-2.0、BSD-2-Clause、BSD-3-Clause、CC0-1.0、Unlicense，原始许可文本一并保留。根目录许可不能自动证明所有外部转载都获授权，发现文件级限制应撤下对应内容。

结构化解析器识别明确的 Q 标记、编号场景和问题表格，并在计数前过滤答案和导航。后处理清理引用包装、规范化重复以及未核实文件级转载授权的归档内容。排除记录只保留标识、来源和原因，不再复制被排除题文。

这是规则清理和抽查，不是全量人工审核。去重不是语义去重：改写、翻译和不同追问可能仍独立保留。主题采用关键词规则，允许重叠；`general` 表示暂未准确分类。不绕过登录、付费墙或访问限制；无法读取的面经只列线索，不计作已验证真题。不得提交 NDA 材料、保密题单、候选人个人信息或未经授权的长答案。

## 重新构建

在完整 Git checkout 中运行；采集需要网络，`GH_TOKEN` 可选且只发往 GitHub API：

```bash
python tools/test_catalog.py
python tools/rebuild.py --self-test
python tools/rebuild.py
python tools/question_bank.py validate
```

`rebuild.py` 是统一入口，调用 `collect_sources.py`、`extract_questions_v2.py`、`refine_catalog.py`，完成采集、结构化提取、许可边界过滤、去重、分类和审计。不要将其他历史实验脚本的中间结果当成最终快照。

重建可能改变来源版本与数量。单个来源失败会记录原因；扫描有体积、文件数和超时限制。GitHub Actions 仅响应扩展分支 PR 的相关文件改动，不定期采集，不自动修改或合并 main。发布遇到并发修改时只做普通快进推送；重试从远端最新代码重新构建，不强制覆盖远端历史。

## 入口

[公司/主题索引](expansion/README.md) · [机器可读题库](expansion/questions.json) · [来源与许可](expansion/SOURCES.md) · [官方资料与面经线索](expansion/REPORTED-SOURCES.md) · [补充来源说明](expansion/ADDITIONAL-SOURCES.md) · [原创练习](expansion/curated.json) · [离线搜索](expansion/index.html) · [质量审计](expansion/REVIEW.md)
