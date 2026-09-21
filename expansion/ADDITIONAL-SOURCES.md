# 第二轮补充来源

整理日期：2026-09-20（America/Chicago）。第二轮增加以下 8 个来源，使登记的种子仓库达到 42 个。是否允许提取、实际贡献数量和许可，均以 [来源登记](SOURCES.md) 为准，不把源项目宣传的题目数直接相加。

| 来源 | 准备方向 | 收录边界 |
|---|---|---|
| [alirezadir/AIMLInterviews](https://github.com/alirezadir/AIMLInterviews) | ML coding、基础知识、系统设计与行为面 | 个人经历与准备资料，不是招聘方认证题库 |
| [chiphuyen/ml-interviews-book](https://github.com/chiphuyen/ml-interviews-book) | ML 面试流程、知识与开放问题 | 仅链接，不复制书中文字 |
| [khangich/machine-learning-interview](https://github.com/khangich/machine-learning-interview) | 公司指南、面试经历、推荐与搜索设计 | 仅链接，具体经历需看原文核验 |
| [Sroy20/machine-learning-interview-questions](https://github.com/Sroy20/machine-learning-interview-questions) | 深度学习、基础 ML、数学 | 是否提取以许可检查为准 |
| [youssefHosni/Data-Science-Interview-Questions-Answers](https://github.com/youssefHosni/Data-Science-Interview-Questions-Answers) | 数据科学问题与答案入口 | 不复制或背书外链答案 |
| [youssefHosni/Data-Science-Interview-Preperation-Resources](https://github.com/youssefHosni/Data-Science-Interview-Preperation-Resources) | 数据科学准备资源 | 导航条目不直接计为面试题 |
| [wdndev/llm_interview_note](https://github.com/wdndev/llm_interview_note) | 中文 LLM 架构、训练、推理、RAG | 整理笔记，答案未经复核；许可不满足时只链接 |
| [anandtopu/AIEngineer](https://github.com/anandtopu/AIEngineer) | AI 工程练习、项目与模拟面试 | 不执行第三方仓库代码 |

## 质量与分类

结构化提取识别明确的 Q 标记、编号场景和问题表格，在保留原始行号的同时过滤答案、导航和管理文字。再做引用包装清理、规范化去重和文件级转载边界过滤。这不是完整抓取，也不是逐题人工审核。

公司标签可来自原 README 的章节、Asked at 声明、共享公司分组、来源文件或原创练习目标。所有继承关联均未独立验证；多个公司标签不证明每家公司都实际考过。当前字段和分类以 `questions.json` 为准，主题允许重叠，未准确分类的条目在 `general`。

## 统一重建入口

需要完整 Git checkout，采集阶段需要网络，离线查询不需要网络。

```bash
python tools/test_catalog.py
python tools/rebuild.py --self-test
python tools/rebuild.py
python tools/question_bank.py validate
```

`rebuild.py` 调用来源采集器、`extract_questions_v2.py` 结构化解析器和许可边界后处理器。其他历史实验脚本不是最终快照的推荐入口。最终结果见 [统计](stats.json)、[质量审计](REVIEW.md) 与 [来源登记](SOURCES.md)。
