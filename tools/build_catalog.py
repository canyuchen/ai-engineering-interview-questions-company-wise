#!/usr/bin/env python3
"""Build the sourced catalog with answer-body filtering and inherited company labels."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from collections import Counter
import collect_sources as c

ORIGINAL_CANDIDATES = c.candidates
FILTERS: Counter[str] = Counter()
NAV = re.compile(r'^(?:how to (?:use|prepare|contribute|study)|where to (?:go|start|find)|what (?:they emphas|they emphasiz|we cover|you.ll learn|you get|is included)|why (?:this repo|this guide|this matters)|getting started|next steps|resources|references|sources|company context|roles & titles|the interview loop|interview loop|study plan|learning path|table of contents|contributing|contribution|license|acknowledg)',re.I)
ASK = re.compile(r'^(?:what|why|how|when|which|where|who|whose|can|could|would|should|is|are|do|does|did|will|explain|describe|compare|implement|design|derive|write|build|given|suppose|imagine|consider|tell|walk|discuss|prove|estimate|calculate|sketch|solve|debug|optimize|find|list|name)\b',re.I)
SCENARIO = re.compile(r'^(?:you|your|a|an|two|we|our|the|there|let|during|in production)\b',re.I)
ANSWER = re.compile(r'^(?:answer|solution|hint|explanation|discussion|答案|解答|解析)(?:\b|[:：\s])',re.I)
EXTRA_TOPICS = {
 'llm-architecture':['transformer','attention','tokeniz','rope','positional','moe','normalization','rmsnorm','架构','位置编码'],
 'ml-foundations':['regression','classification','clustering','decision tree','random forest','svm','bias','variance','pca','机器学习','过拟合','分类','回归'],
 'statistics':['probability','bayes','hypothesis','confidence interval','p-value','causal','a/b test','statistics','概率','统计','因果','假设检验'],
 'data-engineering':['dataset','data pipeline','data quality','data leak','dedup','etl','spark','数据集','数据清洗','数据泄漏'],
 'recommendation':['recommend','ranking','click-through','ctr','collaborative filtering','recsys','推荐','排序','召回'],
 'sql':['sql','join','window function','query plan','数据库'],
 'mlops':['mlops','monitor','drift','deployment','rollback','canary','feature store','监控','漂移','回滚'],
 'behavioral':['behavior','behaviour','stakeholder','project deep','mentoring','disagree','tell me about a time','项目经历','职业规划'],
 'prompt-engineering':['prompt','few-shot','zero-shot','context engineering','提示词'],
 'speech':['speech','audio','asr','tts','diarisation','语音','说话人'],
 'vision':['vision','image','vit','clip','图像','视觉'],
 'diffusion':['diffusion','denois','扩散']
}
ALIASES = {v.casefold():v for v in c.COMPANIES.values()}
ALIASES.update({'google':'Google DeepMind','google deepmind and google ai':'Google DeepMind','meta (superintelligence labs, fair, llama)':'Meta','amazon (aws)':'Amazon','alibaba (qwen)':'Alibaba / Qwen','qwen':'Alibaba / Qwen','moonshot ai (kimi)':'Moonshot AI','zhipu ai (glm)':'Zhipu AI','cursor (anysphere)':'Cursor','cognition (devin, windsurf)':'Cognition','tesla':'Tesla','linkedin':'LinkedIn','airbnb':'Airbnb','pinterest':'Pinterest','spotify':'Spotify'})

def mask_answers(text: str) -> str:
    output=[]; depth=0; scope=None; fenced=False
    for raw in text.splitlines():
        if re.match(r'^\s*(```|~~~)',raw):
            fenced=not fenced; output.append(raw if depth==0 and scope is None else ''); continue
        if fenced:
            output.append(raw if depth==0 and scope is None else ''); continue
        heading=re.match(r'^\s*(#{1,6})\s+(.+)',raw)
        if heading and depth==0:
            level=len(heading[1]); title=c.clean(heading[2])
            if scope is not None and level<=scope: scope=None
            if NAV.match(title) or ANSWER.match(title): scope=level
        opens=len(re.findall(r'<details\b',raw,re.I)); closes=len(re.findall(r'</details>',raw,re.I))
        summary=re.search(r'<summary[^>]*>(.*?)</summary>',raw,re.I)
        if summary:
            question=c.clean(summary[1])
            output.append('<summary>'+summary[1]+'</summary>' if scope is None and not ANSWER.match(question) else '')
        elif depth or opens or closes or scope is not None:
            output.append('')
            if raw.strip(): FILTERS['answer_or_navigation_body_lines']+=1
        else: output.append(raw)
        depth=max(0,depth+opens-closes)
    return '\n'.join(output)

def valid_prompt(q: str) -> bool:
    text=q.lstrip('"\'“” ').replace('**','')
    if NAV.match(text): return False
    if re.match(r'^(?:write your (?:lp|star)|prepare the values|culture screen|the values/culture|read:|see also)',text,re.I): return False
    if re.search(r'[\u4e00-\u9fff]',text): return True
    if ASK.match(text): return True
    return bool(SCENARIO.match(text) and ('?' in text or '？' in text))

def strict_candidates(text: str):
    masked=mask_answers(text); found={n:q for n,q in ORIGINAL_CANDIDATES(masked)}
    for n,line in enumerate(masked.splitlines(),1):
        match=re.match(r'^\s*#{1,6}\s+(?:Q\s*)?\d+[.):：]\s*(.+)',line,re.I)
        if match:
            q=c.clean(match[1])
            if 20<=len(q)<=650 and (ASK.match(q) or SCENARIO.match(q)): found.setdefault(n,q)
    for n,q in sorted(found.items()):
        if valid_prompt(q): yield n,q
        else: FILTERS['non_question_candidates']+=1

def enhanced_tags(q: str,path: str='') -> list[str]:
    text=(q+' '+path).casefold(); result=[]
    for topic,terms in {**c.TOPICS,**EXTRA_TOPICS}.items():
        for term in terms:
            if term=='rag': match=bool(re.search(r'(?<![a-z])rag(?![a-z])',text))
            elif re.search(r'[\u4e00-\u9fff]',term): match=term in text
            else: match=bool(re.search(r'(?<![a-z])'+re.escape(term),text))
            if match: result.append(topic); break
    return result or ['general']

def inherited_context(text: str):
    lines=text.splitlines(); context={}; company=None; topic=''; group=None
    for n,line in enumerate(lines,1):
        heading=re.match(r'^(#{2,4})\s+(.+)',line)
        if heading:
            level=len(heading[1]); title=c.clean(heading[2])
            if level==2: company=None; topic=title; group=None
            if level==3:
                company=ALIASES.get(title.casefold()); group=title if title.startswith('Consumer-Scale ML') else None
                if company is None: topic=title
            if level==4: topic=title
        context[n]={'company':company,'topic':topic,'group':group}
    return lines,context

def enrich() -> None:
    rows=json.loads((c.OUT/'questions.json').read_text(encoding='utf-8'))
    sources=json.loads((c.OUT/'sources.json').read_text(encoding='utf-8'))
    stats=json.loads((c.OUT/'stats.json').read_text(encoding='utf-8'))
    baseline=subprocess.check_output(['git','show',c.BASE_SHA+':README.md'],cwd=c.ROOT).decode('utf-8')
    lines,contexts=inherited_context(baseline)
    for row in rows:
        if row['kind']!='legacy_unverified': continue
        n=int(row['source_url'].rsplit('#L',1)[1]); context=contexts[n]; companies=set(row['companies']); evidence=[]
        if context['company']:
            companies.add(context['company']); evidence.append({'company':context['company'],'relation':'inherited_company_section_not_reverified','url':row['source_url']})
        if context['group']: row['company_group']=context['group']
        for k in range(n,min(n+8,len(lines))):
            if re.match(r'^(?:- |#{1,6} )',lines[k]): break
            if 'Asked at:' not in lines[k]: continue
            for name in re.findall(r'\[([^]]+)\]\(#[^)]+\)',lines[k]):
                name=ALIASES.get(name.casefold(),name); companies.add(name)
                evidence.append({'company':name,'relation':'inherited_asked_at_claim_not_reverified','url':row['source_url'].split('#')[0]+'#L'+str(k+1)})
        row['companies']=sorted(companies)
        if evidence: row['company_evidence']=evidence
        extra=enhanced_tags(row['question'],context['topic']); row['topics']=sorted(set(row['topics']+extra)-{'general'}) or ['general']
    stats['company_labels']=sorted({company for row in rows for company in row['companies']})
    stats['company_label_count']=len(stats['company_labels'])
    stats['counts_by_topic']=dict(sorted(Counter(topic for row in rows for topic in row['topics']).items()))
    stats['quality_filters']=dict(FILTERS)
    stats['quality_rules']='Answer details and navigation sections are excluded before counting; heuristic filtering is not a full editorial review.'
    c.save('questions.json',rows); c.save('stats.json',stats); c.render(rows,sources,stats)
    index=c.OUT/'README.md'
    index.write_text(index.read_text(encoding='utf-8')+'\n## Review and additional sources\n\n[Quality audit](REVIEW.md) · [Official guidance and reported-source leads](REPORTED-SOURCES.md) · [Expanded source notes](ADDITIONAL-SOURCES.md)\n',encoding='utf-8')
    report=['# Quality and coverage audit','',f"Snapshot: {stats['generated_at']}",'',f"Indexed prompts: {len(rows)}; company labels: {stats['company_label_count']}; topic labels: {len(stats['counts_by_topic'])}.",'','## Automated checks','', '- Answer bodies inside HTML details and explicit answer sections are excluded before question extraction.', '- Navigation, preparation instructions and source lists are excluded; original source line numbers remain unchanged.', '- Original company sections and Asked at claims are preserved as unverified inherited labels, with evidence locations.', '- Prompt IDs and normalized text are checked for duplicates; source commit, line and retained license are validated.', '- Topic matches overlap. Company labels do not imply authentic employer interviews.', '', '## Known limitations','', 'Heuristics can still miss questions or include non-question text. No answer is endorsed as correct. Lack of copyright restriction detection is not proof that every upstream file is free of third-party material. Question counts are indexed prompts, not independently verified interviews.','', '## Filter diagnostics','', '```json',json.dumps(dict(FILTERS),ensure_ascii=False,indent=2),'```']
    (c.OUT/'REVIEW.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('FINAL_VALIDATED_CATALOG_STATS\n'+json.dumps(stats,ensure_ascii=False,indent=2))

def self_test() -> None:
    text='## What they emphasise\n- What is a culture screen?\n## Questions\n### 1. What is attention?\n<details><summary>Answer</summary>\n- Why not use another model?\n</details>\n### 2. You need to process ten million events. Write the Python.\n<details>\n<summary>3. How does retrieval work?</summary>\n- What is an answer bullet?\n</details>\n## Sources\n- How to prepare\n'
    got=[q for _,q in strict_candidates(text)]
    assert got==['What is attention?','You need to process ten million events. Write the Python.','How does retrieval work?'],got
    assert 'retrieval' not in enhanced_tags('How does a dragon move?')
    assert 'retrieval' in enhanced_tags('How does RAG work?')
    _,context=inherited_context('## Frontier Labs\n### OpenAI\n#### Inference\n- What is batching?')
    assert context[4]['company']=='OpenAI'
    assert context[4]['topic']=='Inference'
    FILTERS.clear(); print('PASS: answer-body exclusion, navigation filtering, scenario headings, tags and inherited labels.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--self-test',action='store_true'); args=parser.parse_args()
    self_test()
    if not args.self_test:
        c.candidates=strict_candidates; c.tags=enhanced_tags
        c.collect(); enrich()
