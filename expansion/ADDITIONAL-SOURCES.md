# 第二轮补充来源与质量改进

核对日期：2026-09-20（America/Chicago）。这一轮增加 8 个来源，使种子仓库总数达到 42。是否允许提取、是否成功扫描、实际新增题数，均以 [来源登记](SOURCES.md) 为准；这里不把源项目宣传数量相加。

| 来源 | 用途 | 证据与复用边界 |
|---|---|---|
| [alirezadir/AIMLInterviews](https://github.com/alirezadir/AIMLInterviews) | ML coding、ML fundamentals、系统设计和行为面准备 | 作者个人经历与备考资料，不是招聘方确认题库；许可检查后提取 |
| [chiphuyen/ml-interviews-book](https://github.com/chiphuyen/ml-interviews-book) | ML 面试流程、知识问题与开放式系统问题 | 仅链接，不复制书中文字 |
| [khangich/machine-learning-interview](https://github.com/khangich/machine-learning-interview) | 公司指南、面试经历、推荐与搜索设计 | 仅链接；其中具体经历需进一步看原文核验 |
| [Sroy20/machine-learning-interview-questions](https://github.com/Sroy20/machine-learning-interview-questions) | 深度学习、基础 ML 与数学问题 | 许可检查后决定是否提取 |
| [youssefHosni/Data-Science-Interview-Questions-Answers](https://github.com/youssefHosni/Data-Science-Interview-Questions-Answers) | 数据科学问题与答案入口 | 只索引许可允许的题目，不复制或背书外链答案 |
| [youssefHosni/Data-Science-Interview-Preperation-Resources](https://github.com/youssefHosni/Data-Science-Interview-Preperation-Resources) | 数据科学面试准备资源导航 | 许可检查后提取；导航条目不计为题目 |
| [wdndev/llm_interview_note](https://github.com/wdndev/llm_interview_note) | 中文 LLM 架构、训练、推理、RAG 笔记 | 原作者注明是整理资料；许可检查后决定是否提取，答案未经复核 |
| [anandtopu/AIEngineer](https://github.com/anandtopu/AIEngineer) | AI 工程练习、项目、模拟面试 | 许可检查后提取；不自动执行第三方代码 |

## 题目质量处理

首轮宽松扫描得到的候选中包含少量备考说明、导航标题和答案内部反问。新版构建器在统计前过滤这些内容，同时保留源文件的原始行号。为了不误删，不满足规则的有效题也可能遗漏；本项目不承诺完整抓取或逐题人工审核。

原 README 的公司章节与 Asked at 声明现在进入 `company_evidence`，单独标注为继承且未重新核验，不把原作者的声明升级为本次已验证事实。公司合并章节不自动展开成每家公司都考过。

新增主题包括 LLM 架构、机器学习基础、概率统计、数据工程、推荐系统、SQL、MLOps、行为面、提示词工程、语音、视觉与扩散模型。主题标签允许重叠。

## 推荐重建方式

用以下命令替代仅运行低层采集器；两者都需要完整 Git checkout。采集阶段需要网络，读取已生成索引无需网络。

```bash
python tools/test_catalog.py
python tools/build_catalog.py --self-test
python tools/build_catalog.py
python tools/question_bank.py validate
```

`collect_sources.py` 是较宽松的底层采集器；`build_catalog.py` 加入答案正文过滤、导航过滤、公司证据继承、细分主题与质量审计。最终结果见 [统计](stats.json) 和 [质量审计](REVIEW.md)。
