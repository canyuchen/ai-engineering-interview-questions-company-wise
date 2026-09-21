# AI 工程面试题库：扩展版

本扩展保留原 README 和作者署名。请从 [扩展索引](expansion/README.md) 开始，或下载后用浏览器打开 `expansion/index.html` 离线检索。实际条目数以 [统计](expansion/stats.json) 为准，不采用其他题库自称的题数。

## 证据类型

| 类型 | 含义 | 注意 |
|---|---|---|
| legacy_unverified | 原 README 中提取并继承的条目 | 没有重新验证原文 Asked at 声明；也不是对原文每条题目的人工普查 |
| community_question_bank | 公开题库中提取的候选 | 经过规则清理，但仍需逐题编辑审核，不是已验证公司真题 |
| derived_practice | 本次原创的 150 道中文工程场景练习 | 30 个公司定向专题；不是面经，背景阅读不是考过的证据 |

公司标签来自原文分组、Asked at 声明、来源文件名或练习目标。原文把多家公司放在一个共同章节时，会保留多个标签；这不证明每家公司都考过该题。面试日期未知一律为 null。转载不是独立验证。

## 内容和查询

包含公司索引、主题索引、JSON 数据、单文件离线搜索、来源和许可证、原始面经线索、命令行查询与构建脚本。

```bash
python tools/question_bank.py stats
python tools/question_bank.py search "cache" --kind community_question_bank
python tools/question_bank.py search --company "Snowflake"
python tools/question_bank.py search --topic agents --limit 100
python tools/question_bank.py validate
```

查询已构建数据无需网络、API key 或第三方 Python 包。需要 Python 3.10+。题目提供稳定 ID、主题、来源类型和原文链接；自动采集来源固定到 commit SHA、文件和行号。原文可能带答案，但本扩展不复制长答案，也没有逐题核验其正确性。

## 清理与许可

从 34 个候选资料仓库建立登记表；仅提取允许列表内的许可，其余只保留入口。允许列表为 MIT、Apache-2.0、BSD-2-Clause、BSD-3-Clause、CC0-1.0、Unlicense，并保留完整许可文本。被读取的 11 个仓库中，也可能有仓库没有符合提取规则的条目；不要把来源数当成每个来源都贡献了题目。

除了规范化文本去重，还清理导航、仓库管理文字、部分答案片段和重复的交叉引用包装。对未单独核实再发布授权的 `_archive` 转载目录不保留题文。排除原因见 [excluded.json](expansion/excluded.json)，只记录标识和来源，不再次复制被排除题文。

这是规则清理和抽查，不是完整人工审核；语义相近的改写、翻译、不同追问可能仍分开保留。主题采用关键词规则，允许重叠；general 表示暂未准确分类。根目录许可证不能自动证明所有外部转载都获授权，发现文件级限制时应移除对应内容。

不绕过登录和付费墙。不可读取的知乎/小红书链接只作为二手线索，不计作已验证面经。不得提交 NDA 材料、保密题单、候选人个人信息或未授权长答案。

## 重新构建

在完整 Git checkout 中执行（采集需要网络，GH_TOKEN 可选）：

```bash
python tools/test_catalog.py
python tools/collect_sources.py
python tools/refine_catalog.py
python tools/question_bank.py validate
```

仅更新清理规则时，直接运行 `refine_catalog.py` 即可，无需重新采集。重新采集可能改变来源版本和数量。工作流仅服务本扩展分支的 PR 构建/修订，不定期采集，不自动修改或合并 main。

## 入口

[公司/主题索引](expansion/README.md) · [机器可读题库](expansion/questions.json) · [来源与许可](expansion/SOURCES.md) · [官方资料与面经线索](expansion/REPORTED-SOURCES.md) · [原创练习](expansion/curated.json) · [离线搜索](expansion/index.html)
