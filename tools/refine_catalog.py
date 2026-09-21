#!/usr/bin/env python3
"""Conservative postprocessing: remove navigation/reprints, merge reference wrappers, restore labels."""
from __future__ import annotations
import hashlib,json,re,subprocess
from collections import Counter
from datetime import datetime,timezone
import collect_sources as c

ALIASES={'Anthropic':'Anthropic','OpenAI':'OpenAI','Google DeepMind and Google AI':'Google DeepMind','Google DeepMind':'Google DeepMind','Meta (Superintelligence Labs, FAIR, Llama)':'Meta','Meta':'Meta','xAI':'xAI','Mistral AI':'Mistral AI','Cohere':'Cohere','DeepSeek':'DeepSeek','Moonshot AI (Kimi)':'Moonshot AI','Moonshot AI':'Moonshot AI','Zhipu AI (GLM)':'Zhipu AI','Zhipu AI':'Zhipu AI','Alibaba (Qwen)':'Alibaba / Qwen','Alibaba':'Alibaba / Qwen','Sarvam AI':'Sarvam AI','Microsoft':'Microsoft','Amazon (AWS)':'Amazon','Amazon':'Amazon','Apple':'Apple','NVIDIA':'NVIDIA','Tesla':'Tesla','Databricks':'Databricks','Groq':'Groq','Together AI':'Together AI','Hugging Face':'Hugging Face','Scale AI':'Scale AI','Perplexity':'Perplexity','Cursor (Anysphere)':'Cursor','Cursor':'Cursor','Cognition (Devin, Windsurf)':'Cognition','Cognition':'Cognition','Sierra':'Sierra','Harvey':'Harvey','Glean':'Glean','Character.AI':'Character.AI','ElevenLabs':'ElevenLabs','Abridge':'Abridge','Figure AI':'Figure AI','Waymo':'Waymo','Palantir':'Palantir','Uber':'Uber','Netflix':'Netflix','LinkedIn':'LinkedIn','Airbnb':'Airbnb','Pinterest':'Pinterest','Spotify':'Spotify'}
EXTRA={'llm_architecture':r'\b(attention|transformer|rope|rmsnorm|tokeniz\w*|bpe|moe|swiglu|mla|gqa|mqa)\b|注意力|位置编码|分词|模型结构','ml_foundations':r'\b(bias|variance|regression|classification|clustering|bayes\w*|entropy|cross.validation|overfit\w*|regulariz\w*)\b|过拟合|正则化|交叉熵|回归|分类|聚类|贝叶斯','data_engineering':r'\b(data quality|data pipeline|etl|dedup\w*|data leakage|contamination|data lineage)\b|数据清洗|数据质量|去重|数据泄露|数据配比|数据血缘','recommendation':r'\b(recommend\w*|ranking|ranker|click.through|ctr|collaborative filtering|two.tower)\b|推荐|点击率|排序模型','experimentation':r'\b(a/b test\w*|causal\w*|confidence interval|hypothesis test\w*|statistical significance|selection bias)\b|因果|置信区间|统计显著|选择偏差|假设检验','gpu_kernels':r'\b(cuda|triton|kernel\w*|roofline|simd|vliw|warp\w*|tensor core\w*)\b|算子|访存|带宽','distributed_training':r'\b(ddp|fsdp|deepspeed|all.reduce|all.to.all|tensor parallel\w*|pipeline parallel\w*|expert parallel\w*|zero.[123])\b|分布式训练|张量并行|流水线并行|专家并行|梯度同步','context_engineering':r'\b(prompt\w*|context window|context engineering|context budget|long.context|few.shot)\b|上下文|提示词|长会话','behavioral':r'\b(tell me about|describe a time|disagreement|stakeholder\w*|leadership|conflict|career)\b|自我介绍|实习经历|职业规划|项目经历|团队冲突'}
NAV=re.compile(r"^(how to (prep|prepare|contribute|use)|where to go next|what('?s new| it does| we found| we accept| this tests| this pr does| to contribute| i.d avoid| i.d watch for)|why (it.s used|it matters|it happens|this happens|this is hard)|design engineer|how it works|what.s wrong|why (this guide|this repository|this repo))\W*$",re.I)

def reason(r):
    p=r.get('source_path','').lower();q=r['question']
    if r['kind']!='community_question_bank':return None
    if '_archive/' in p:return 'archived_reprint_file_level_rights_not_verified'
    if any(x in p for x in ['contributing','.github/','mcp-server/','changelog']):return 'repository_administration_not_interview_question'
    if NAV.match(q) or q.startswith(('为什么做这本小册子','实现复杂，')):return 'navigation_or_answer_fragment'
    if q.startswith(('Design tools the way','Checkable constraints.','What you will learn','What you\'ll learn')):return 'instruction_or_answer_fragment'
    return None

def main():
    rows=json.loads((c.OUT/'questions.json').read_text());sources=json.loads((c.OUT/'sources.json').read_text());stats=json.loads((c.OUT/'stats.json').read_text())
    excluded=json.loads((c.OUT/'excluded.json').read_text()) if (c.OUT/'excluded.json').exists() else []
    seen={};kept=[];merges=0
    for r in rows:
        why=reason(r)
        if why:
            excluded.append({'id':r['id'],'source_url':r['source_url'],'reason':why});continue
        q=r['question']
        match=re.match(r'^\[\[(.*?)\]\]\s*\([^)]*\)\s*:\s*(.*)$',q)
        if match:q=match.group(2).strip() or match.group(1).strip()
        key=c.norm(q)
        if key in seen:
            target=seen[key];target['companies']=sorted(set(target['companies'])|set(r['companies']))
            target.setdefault('additional_sources',[]).append({'url':r['source_url'],'source_id':r['source_id'],'company_label':None})
            target.setdefault('additional_sources',[]).extend(r.get('additional_sources',[]));merges+=1;continue
        if q!=r['question']:
            r['previous_ids']=[r['id']];r['question']=q;r['id']='q-'+hashlib.sha256(key.encode()).hexdigest()[:14]
        seen[key]=r;kept.append(r)
    baseline=subprocess.check_output(['git','show',c.BASE_SHA+':README.md'],cwd=c.ROOT).decode('utf-8')
    lookup={int(r['source_url'].rsplit('#L',1)[1]):r for r in kept if r['kind']=='legacy_unverified'}
    section=[];current=None
    for number,line in enumerate(baseline.splitlines(),1):
        if line.startswith('## '):section=[];current=None
        if line.startswith('### '):
            h=line[4:].strip();current=None
            section=['Uber','Netflix','LinkedIn','Airbnb','Pinterest','Spotify'] if h.startswith('Consumer-Scale ML Companies') else ([ALIASES[h]] if h in ALIASES else [])
        if number in lookup:
            current=lookup[number];current['companies']=sorted(set(current['companies'])|set(section));current['company_relation']='inherited_section_or_asked_at_label_not_reverified'
        if current is not None and re.search(r'^\s*-\s*Asked at:',line):
            labels=[ALIASES[name] for name in re.findall(r'\[([^\]]+)\]\(',line) if name in ALIASES]
            current['companies']=sorted(set(current['companies'])|set(labels))
    for r in kept:
        text=r['question']+' '+r.get('source_path','');topics=set(r['topics'] if r['kind']=='derived_practice' else [])
        for topic,words in c.TOPICS.items():
            for w in words:
                pat=re.escape(w) if any(ord(ch)>127 for ch in w) else r'\b'+re.escape(w)+r'\w*\b'
                if re.search(pat,text,re.I):topics.add(topic);break
        topics.update(k for k,v in EXTRA.items() if re.search(v,text,re.I));topics.discard('general');r['topics']=sorted(topics) or ['general']
    stats.setdefault('initial_candidate_count',stats['total_questions'])
    stats['refined_at']=datetime.now(timezone.utc).isoformat(timespec='seconds')
    stats['total_questions']=len(kept);stats['new_questions']=len(kept)-stats['baseline_questions'];stats['counts_by_kind']=dict(Counter(r['kind'] for r in kept))
    stats['postprocess_duplicates_merged']=stats.get('postprocess_duplicates_merged',0)+merges
    stats['excluded_count']=len(excluded);stats['exclusion_reasons']=dict(Counter(r['reason'] for r in excluded))
    stats['company_labels']=sorted({x for r in kept for x in r['companies']});stats['company_label_count']=len(stats['company_labels'])
    stats['counts_by_topic']=dict(sorted(Counter(t for r in kept for t in r['topics']).items()));stats['topic_count']=len(stats['counts_by_topic'])
    stats['baseline_count_warning']='Extracted normalized candidates, not a manual census of all original questions.'
    stats['company_label_warning']='Inherited company claims, grouped sections, source-file labels or practice targets; none prove actual interview occurrence.'
    counts=Counter(r['source_id'] for r in kept if r['kind']=='community_question_bank')
    for s in sources:
        s.setdefault('initial_candidates_added',s['questions_added']);s['questions_added']=counts[s['id']]
    c.save('questions.json',kept);c.save('sources.json',sources);c.save('stats.json',stats);c.save('excluded.json',excluded);c.render(kept,sources,stats)
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
