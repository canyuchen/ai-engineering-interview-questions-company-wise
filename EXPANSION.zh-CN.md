# AI 工程面试题库：扩展版

本扩展保留原 README、许可证和作者署名。从 [公司/主题索引](expansion/README.md) 开始，或下载后在本地浏览器打开 `expansion/index.html` 离线检索。实际条目数以 [统计](expansion/stats.json) 为准，不采用其他题库自称的题数。

## 证据类型

| 类型 | 含义 | 注意 |
|---|---|---|
| `legacy_unverified` | 原 README 中提取并继承的条目 | 未重新验证原文 Asked at 声明；不是对原文每道题的人工普查 |
| `community_question_bank` | 公开题库中提取的候选 | 经过规则清理和抽查，仍需逐题编辑审核，不是已验证公司真题 |
| `derived_practice` | 本次原创的 150 道中文工程场景练习 | 30 个公司定向专题；不是面经，背景阅读不是考过的证据 |

公司标签来自原文分组、Asked at 声明、来源文件名或练习目标，不能证明真实面试发生。原文明确的公司关联记录在 `company_evidence`；多个公司共用的泛化章节不会自动拆成每家公司都考过。面试日期未知一律为 null。转载不是独立验证。

## 内容与查询

包括公司和主题 Markdown 索引、JSON 数据、单文件离线搜索、来源与许可证、原始面经线索、命令行查询和构建脚本。候选来源清单共 42 个仓库；是否实际提取以及每个来源的贡献数见 [来源登记](expansion/SOURCES.md)。

```bash
python tools/question_bank.py stats
python tools/question_bank.py search "cache" --kind community_question_bank
python tools/question_bank.py search --company "Snowflake"
python tools/question_bank.py search --topic agents --limit 100
python tools/question_bank.py validate
```

查询已构建数据无需网络、API key 或第三方 Python 包，需要 Python 3.10+。题目提供稳定 ID、主题、来源类型和原文链接；自动采集来源固定到 commit SHA、文件和行号。原文可能带答案，但本扩展不复制长答案，也未逐题核验其正确性。

## 清理与许可

仅提取许可允许列表内的来源，其余保留入口。允许列表为 MIT、Apache-2.0、BSD-2-Clause、BSD-3-Clause、CC0-1.0、Unlicense，并保留完整许可文本。扫描成功的来源也可能没有符合提取规则的题目；不要把来源数理解为每个来源都贡献了题目。

新版构建在计数前过滤答案折叠正文、明确答案章节、导航、备考说明和管理文字，再清理交叉引用包装与重复。对未单独核实再发布授权的 `_archive` 转载目录不保留题文。后处理排除原因见 [excluded.json](expansion/excluded.json)，只记录标识和来源，不复制被排除题文。详细规则与局限见 [质量审计](expansion/REVIEW.md)。

去重采用 Unicode NFKC、大小写折叠、空白与标点处理，再做可识别的引用包装合并；不是语义去重。语义相近的改写、翻译和不同追问可能仍保留。主题为关键词规则，允许重叠；general 表示暂未准确分类。

根目录许可证不能自动证明所有外部转载已获授权，发现文件级限制时应移除对应内容。不绕过登录和付费墙；不可读取的知乎、小红书链接仅作为二手线索。不得提交 NDA 材料、保密题单、候选人个人信息或未经授权的长答案。

## 重新构建

在完整 Git checkout 中运行；采集需要网络，`GH_TOKEN` 可选且只发送到 GitHub API：

```bash
python tools/test_catalog.py
python tools/rebuild.py --self-test
python tools/rebuild.py
python tools/question_bank.py validate
```

`rebuild.py` 是统一入口，组合来源采集、答案过滤、转载边界处理、引用去重、公司归属恢复、主题细分和质量审计。底层模块分别为 `collect_sources.py`、`build_catalog.py`、`refine_catalog.py`，不建议单独运行后把中间产物误当成最终结果。

重新采集可能改变来源版本和数量。单个来源失败会进入登记表，不伪装成功；扫描有体积、文件数和超时限制。工作流仅服务扩展分支 PR 的相关文件改动，不定期采集，不自动修改或合并 main。

## 入口

[公司/主题索引](expansion/README.md) · [机器可读题库](expansion/questions.json) · [来源与许可](expansion/SOURCES.md) · [官方资料与面经线索](expansion/REPORTED-SOURCES.md) · [补充来源说明](expansion/ADDITIONAL-SOURCES.md) · [原创练习](expansion/curated.json) · [离线搜索](expansion/index.html) · [质量审计](expansion/REVIEW.md)
