# AI 工程面试题库：扩展版使用说明

本扩展保留原 README 和上游作者署名，增加公开题库入口、公司专题与工程场景练习。构建完成后阅读 [扩展索引](expansion/README.md)，或下载分支后用浏览器打开 `expansion/index.html`。实际数量与失败来源见 [统计](expansion/stats.json) 和 [来源登记](expansion/SOURCES.md)；不把其他项目宣传的题数当成本项目的实测题数。

## 三种条目，不混为真题

| 类型 | 含义 | 证据边界 |
|---|---|---|
| `legacy_unverified` | 原 README 中继承的题目；固定原提交及行号 | 本次没有逐一复核原文的 Asked at 声明 |
| `community_question_bank` | 从许可允许的公开仓库自动提取的题目候选 | 不保证来自真实面试；自动提取仍需编辑审核 |
| `derived_practice` | 本次编写的 150 道工程场景练习，30 个公司专题 | 不是候选人面经；链接只是背景阅读 |

公司标签来自源文件名、目录或练习目标，不是考题发生地点的证明。多个转载来源保留在 `additional_sources`，不会被当作多次独立验证。未知面试日期为 null。原文可能带答案；本扩展只索引题目与原文，不复制长答案，不声称核对了全部答案的正确性。

## 目录

```text
expansion/
  README.md             # 公司、主题与数量入口
  companies/            # 公司标签索引
  topics/               # 主题索引（可重叠）
  questions.json        # 题目、类型和不可变来源定位
  sources.json          # 来源许可、版本、失败原因
  stats.json            # 实际构建统计
  SOURCES.md            # 可读来源登记
  REPORTED-SOURCES.md   # 官方面试资料与二手面经线索
  curated.json          # 原创场景练习
  seeds.json            # 采集仓库清单
  licenses/             # 上游原始许可证
  index.html            # 单文件离线搜索
```

原创练习的 30 个专题：ByteDance、Tencent、Baidu、Meituan、MiniMax、StepFun、Xiaomi、01.AI、Snowflake、Pinecone、Weaviate、Qdrant、Zilliz / Milvus、Elastic、MongoDB、Redis、Cloudflare、Modal、Baseten、Fireworks AI、Cerebras、LangChain、LlamaIndex、Vercel、Replit、Sourcegraph、Salesforce、IBM、Adobe、ServiceNow。主题覆盖检索、智能体、训练、对齐、推理、多模态、评测、安全与生产系统。

## 查询

Python 3.10+，已构建数据的查询无需网络、API key 或第三方 Python 包。

```bash
python tools/question_bank.py stats
python tools/question_bank.py search "cache" --kind community_question_bank
python tools/question_bank.py search --company Snowflake
python tools/question_bank.py search --topic agents --limit 100
python tools/question_bank.py validate
```

先按岗位选主题，再按公司标签补充场景。练习至少覆盖问题边界、正确性条件、失败模式、资源预算、评测设计、上线监控与回滚。公司索引是准备路径，不是押题保证。

## 收录、去重与版权

采集器只读取公开仓库的 Markdown，不执行第三方代码。每个来源固定到 commit SHA，保存文件路径及行号。去重方式为 Unicode NFKC、大小写折叠、删除空白和标点，这是文本去重，不是语义去重；翻译、近义问法、追问仍可能分开保留。

自动提取可能误收录目录中的疑问句、解释性条目或相似变体。可用稳定 ID 提交修订；不要把提取成功说成真实面经已核实。来源标签也不意味着题库作者的答案被本项目背书。

仅对 SPDX 为 MIT、Apache-2.0、BSD-2-Clause、BSD-3-Clause、CC0-1.0 或 Unlicense 的仓库提取题目标题，并保留上游许可和来源链接。其余许可、缺少许可、限制转载的资料只给入口，不复制题文。上游仓库仍可能含第三方转载或文件级限制，发现后应撤下对应内容；本项目不将所有第三方内容重新许可。

不绕过登录、付费墙或访问限制。未能读取的知乎、小红书原帖标记为二手线索，不计入已核实面试题。不得提交 NDA 材料、招聘方保密题单或候选人个人信息。

## 重新构建

在完整 Git checkout 中执行；需要网络，GitHub token 可选（提高 API 配额）。

```bash
python tools/test_catalog.py
python tools/collect_sources.py
python tools/question_bank.py validate
```

每次重新采集读取来源当时版本，结果可能变化；现有数据保存了本次的 commit 坐标。大小、超时、许可等失败会进入登记表，不伪装为成功。工作流只针对本扩展分支的首次 PR 打开事件，不会周期爬取，也不会自动合并或修改 main。
