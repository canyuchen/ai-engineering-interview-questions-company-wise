# 数据复核与统计口径 / Snapshot review

本次最初提取 4,099 条候选，交付索引为 **3,761 条**。这是题目和练习候选索引，不是经过独立验证的公司真题数量。

## 清理记录

第一阶段合并 105 个格式变体，排除 231 条候选：200 条位于文件级转载权限尚未确认的归档目录，18 条属于仓库维护材料，11 条属于导航或答案片段，2 条属于说明性片段。第二阶段再移除 2 条导航或答案片段，并规范化 62 条引用或追问格式。最终数量为 4,099 − 105 − 231 − 2 = 3,761。

[排除记录](excluded.json) · [第二阶段审计](review-audit.json) · [第二阶段之前的快照](questions.raw.json) · [当前统计](stats.json)

questions.raw.json 是第一阶段清理后的 3,763 条快照，并非最初的 4,099 条，也不是额外题目。source_question 保留定点改写前的措辞。来源登记中的新增数采用当前题目的主要来源归属；其他出处保留在 additional_sources。

## 标签与局限

70 个公司标签来自原 README 的公司分组、Asked at 声明、其他资料文件名或原创练习目标。原 README 的消费级机器学习部分是六家公司共用的分组；关联标签不表示每家公司都问过同一题。20 个主题使用关键词规则，同一道题可属于多个主题，不能将主题计数相加作为总量。

已检查 ID 和规范化文本唯一性、来源定位、许可文件与计数一致性。规则清理与抽查不等于完整人工审核；仍可能有近义改写、误提取或未分类条目。原文答案未逐题核验。

## 重新构建

在完整 Git checkout 中执行：

```bash
python tools/test_catalog.py
python tools/build_catalog.py --self-test
python tools/build_catalog.py
python tools/refine_catalog.py
python tools/question_bank.py validate
```

build_catalog.py 读取来源的新快照并执行更严格的答案段落过滤，因此重建后的数量和 ID 可能变化。refine_catalog.py 可对现有快照进行文件级排除、标签整理与去重，无需再次下载来源。第二阶段的定点编辑记录保存在 review-audit.json，不代表整库人工审定。
