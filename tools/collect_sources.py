#!/usr/bin/env python3
"""Collect public, permissively licensed question headings; never execute upstream code."""
from __future__ import annotations
import argparse, base64, hashlib, html, io, json, os, re, subprocess, sys, tarfile, time, unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'expansion'
ALLOWED = {'MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'CC0-1.0', 'Unlicense'}
MAX_ARCHIVE = 32 * 1024 * 1024
BASE_SHA = '14c0106e2794bd4d355e6a9145b375a19b912bac'
BASE_REPO = 'canyuchen/ai-engineering-interview-questions-company-wise'
COMPANIES = {'anthropic':'Anthropic','openai':'OpenAI','google-deepmind':'Google DeepMind','meta-ai':'Meta','xai':'xAI','mistral':'Mistral AI','deepseek':'DeepSeek','moonshot-ai':'Moonshot AI','zhipu-ai':'Zhipu AI','sarvam-ai':'Sarvam AI','microsoft':'Microsoft','amazon':'Amazon','apple':'Apple','nvidia':'NVIDIA','qwen-alibaba':'Alibaba / Qwen','databricks':'Databricks','scale-ai':'Scale AI','perplexity':'Perplexity','cursor-anysphere':'Cursor','cohere':'Cohere','hugging-face':'Hugging Face','together-ai':'Together AI','glean':'Glean','palantir':'Palantir','sierra':'Sierra','harvey':'Harvey','abridge':'Abridge','cognition-devin':'Cognition','groq':'Groq','elevenlabs':'ElevenLabs','character-ai':'Character.AI','waymo':'Waymo','figure-ai':'Figure AI','stripe':'Stripe','snowflake':'Snowflake','uber':'Uber','netflix':'Netflix','reddit':'Reddit','roblox':'Roblox','coinbase':'Coinbase','rippling':'Rippling'}
TOPICS = {'agents':['agent','tool call','mcp','智能体','工具调用'], 'retrieval':['rag','retriev','embedding','vector','检索','向量'], 'alignment':['rlhf','ppo','dpo','grpo','reward','偏好','强化学习'], 'inference':['inference','kv cache','quantiz','batching','推理','量化'], 'training':['train','lora','gradient','optimizer','训练','微调'], 'evaluation':['eval','metric','judge','评估','评测'], 'security':['security','injection','privacy','安全','隐私'], 'multimodal':['vision','image','speech','audio','video','多模态','语音','图像'], 'systems':['design','distributed','latency','system','架构','分布式','设计'], 'coding':['implement','code','python','coding','实现','手写','编程']}

def fetch(url: str, cap: int = 2*1024*1024) -> bytes:
    headers = {'User-Agent':'AI-Interview-Catalog/1.0','Accept':'application/vnd.github+json'}
    if urlparse(url).hostname == 'api.github.com' and os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=headers), timeout=45) as r:
                data = r.read(cap+1)
                if len(data)>cap: raise ValueError('response exceeds safety limit')
                return data
        except HTTPError as e:
            if e.code not in (429,500,502,503,504) or attempt==2: raise
        except (URLError, TimeoutError):
            if attempt==2: raise
        time.sleep(2**attempt)
    raise RuntimeError('request retries exhausted')

def api(path: str) -> dict:
    return json.loads(fetch('https://api.github.com/'+path))

def clean(s: str) -> str:
    s = re.sub(r'<[^>]*>', '', s)
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s)
    s = html.unescape(s).strip().strip('*_` ')
    s = re.sub(r'^(?:(?:Q(?:uestion)?\s*)?\d+[.)：:]\s*|Q\s*[:：]\s*)', '', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip('*_` ')

def norm(s: str) -> str:
    return re.sub(r'[^\w\u4e00-\u9fff]+','',unicodedata.normalize('NFKC',s).casefold())

def candidates(text: str):
    fenced = False
    for n,line in enumerate(text.splitlines(),1):
        if re.match(r'^\s*(```|~~~)',line): fenced = not fenced; continue
        if fenced: continue
        raw = line.strip()
        m = re.match(r'^(?:#{1,6}\s+|[-*+]\s+(?:\[[ xX]\]\s*)?|\d+[.)]\s+)(.*)',raw)
        if m: raw=m.group(1)
        elif '<summary' in raw.lower(): pass
        else: continue
        if re.fullmatch(r'\[.*\]\(#[^)]*\)',raw): continue
        q=clean(raw)
        if not 8<=len(q)<=650: continue
        if re.search(r'\b(this repo(?:sitory)?|contributing|star this|sponsor this)\b|如何贡献|为什么要做这个',q,re.I): continue
        if re.match(r'^(answer|source|asked at|note|reference|答案|来源|参考)\s*[:：]',q,re.I): continue
        if not (re.match(r'^(what|why|how|when|which|where|explain|describe|compare|implement|design|derive|write|given|suppose|can you|walk me|discuss|什么|为什么|如何|怎样|怎么|请|解释|比较|设计|实现|手写|推导|给定)',q,re.I) or '?' in q or '？' in q): continue
        yield n,q

def tags(q: str, path: str='') -> list[str]:
    s=(q+' '+path).lower()
    return [k for k,words in TOPICS.items() if any(w in s for w in words)] or ['general']

def save(name: str, obj) -> None:
    p=OUT/name; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def collect() -> None:
    OUT.mkdir(exist_ok=True)
    seeds=json.loads((OUT/'seeds.json').read_text(encoding='utf-8'))
    groups=json.loads((OUT/'curated.json').read_text(encoding='utf-8'))
    retrieved=datetime.now(timezone.utc).isoformat(timespec='seconds')
    records=[]; registry=[]; seen={}; baseline=set(); duplicates=0
    readme=(ROOT/'README.md').read_text(encoding='utf-8')
    baseline_text=subprocess.check_output(['git','show',BASE_SHA+':README.md'],cwd=ROOT).decode('utf-8')
    for n,q in candidates(baseline_text):
        key=norm(q)
        if key in seen: continue
        record={'id':'legacy-'+hashlib.sha256(key.encode()).hexdigest()[:14], 'question':q,'companies':[], 'topics':tags(q), 'kind':'legacy_unverified','review_status':'inherited_not_reverified','source_url':f'https://github.com/{BASE_REPO}/blob/{BASE_SHA}/README.md#L{n}','source_id':'original-readme','retrieved_at':retrieved,'interview_date':None}
        records.append(record); seen[key]=record; baseline.add(key)
    baseline_count=len(records)
    for group in groups:
        for q in group['questions']:
            key=norm(q)
            if key in seen: duplicates+=1; continue
            record={'id':'practice-'+hashlib.sha256(key.encode()).hexdigest()[:14],'question':q,'companies':group.get('companies',[]),'topics':group['topics'],'kind':'derived_practice','review_status':'original_practice_not_reported','source_url':group['sources'][0],'reading_references':group['sources'],'source_id':group['id'],'retrieved_at':retrieved,'interview_date':None}
            records.append(record); seen[key]=record
    for seed in seeds:
        repo=seed['repo']; source_id=repo.replace('/','--')
        state={'id':source_id,'repository':repo,'url':'https://github.com/'+repo,'retrieved_at':retrieved,'status':'pending','questions_added':0,'duplicates_merged':0,'kind':'community_question_bank','answers_reviewed':False}
        print('COLLECT',repo,flush=True)
        try:
            meta=api('repos/'+repo)
            if meta.get('private'): raise ValueError('private sources are not collected')
            commit=api('repos/'+repo+'/commits/'+quote(meta['default_branch'],safe=''))
            sha=commit['sha']; state['commit']=sha; state['description']=meta.get('description'); state['default_branch']=meta['default_branch']
            state['snapshot_url']=f'https://github.com/{repo}/tree/{sha}'
            if not seed.get('extract',True): state['status']='link_only'; registry.append(state); continue
            try:
                lic=api('repos/'+repo+'/license?ref='+sha)
            except HTTPError as e:
                if e.code==404: state['status']='link_only_license_not_found'; registry.append(state); continue
                raise
            spdx=lic.get('license',{}).get('spdx_id'); state['license']=spdx
            if spdx not in ALLOWED: state['status']='link_only_license_not_allowlisted'; registry.append(state); continue
            license_text=base64.b64decode(lic['content']).decode('utf-8')
            if len(license_text.strip())<100: raise ValueError('license text unexpectedly short')
            p=OUT/'licenses'/f'{source_id}.txt'; p.parent.mkdir(exist_ok=True)
            p.write_text(license_text,encoding='utf-8'); state['license_file']='licenses/'+p.name
            archive=fetch(f'https://codeload.github.com/{repo}/tar.gz/{sha}',MAX_ARCHIVE)
            count=0
            with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tar:
                for member in sorted(tar.getmembers(),key=lambda m:m.name):
                    if not member.isfile() or member.size>1024*1024 or not member.name.lower().endswith(('.md','.markdown')): continue
                    path=member.name.partition('/')[2]
                    if any(x in path.lower().split('/') for x in ['node_modules','.git','vendor']): continue
                    if count>=500: break
                    count+=1
                    stream=tar.extractfile(member)
                    if stream is None: continue
                    text=stream.read().decode('utf-8',errors='replace')
                    company=next((COMPANIES[x.lower()] for x in [Path(path).stem]+list(Path(path).parts[:-1]) if x.lower() in COMPANIES),None)
                    for line,q in candidates(text):
                        key=norm(q); url=f'https://github.com/{repo}/blob/{sha}/{quote(path,safe="/")}#L{line}'
                        evidence={'url':url,'source_id':source_id,'company_label':company}
                        if key in seen:
                            seen[key].setdefault('additional_sources',[]).append(evidence)
                            state['duplicates_merged']+=1; duplicates+=1; continue
                        record={'id':'q-'+hashlib.sha256(key.encode()).hexdigest()[:14],'question':q,'companies':[company] if company else [],'company_relation':'source_file_label_not_verified_interview','topics':tags(q,path),'kind':'community_question_bank','review_status':'machine_extracted_needs_editorial_review','source_url':url,'source_id':source_id,'source_commit':sha,'source_path':path,'source_line':line,'license':spdx,'retrieved_at':retrieved,'interview_date':None}
                        records.append(record); seen[key]=record; state['questions_added']+=1
            p=OUT/'licenses'/f'{source_id}.txt'; p.parent.mkdir(exist_ok=True)
            p.write_text(license_text,encoding='utf-8'); state['license_file']='licenses/'+p.name
            state['markdown_files_scanned']=count; state['status']='indexed'
        except Exception as exc:
            state['status']='partial' if state['questions_added'] else 'failed'; state['error']=f'{type(exc).__name__}: {str(exc)[:240]}'
        registry.append(state)
    for record in records:
        record['duplicate_of_original']=norm(record['question']) in baseline
        record['companies']=sorted(set(record['companies']) | {s['company_label'] for s in record.get('additional_sources',[]) if s.get('company_label')})
    stats={'generated_at':retrieved,'baseline_commit':BASE_SHA,'baseline_questions':baseline_count,'new_questions':len(records)-baseline_count,'total_questions':len(records),'normalized_duplicates_merged':duplicates,'deduplication':'Unicode NFKC + casefold + punctuation/whitespace removal; NOT semantic deduplication','counts_by_kind':dict(Counter(r['kind'] for r in records)),'source_count':len(registry),'source_statuses':dict(Counter(s['status'] for s in registry)),'company_labels':sorted({c for r in records for c in r['companies']}),'interview_authenticity':'No automatically indexed item is asserted to be an actual employer interview question.'}
    save('questions.json',records); save('sources.json',registry); save('stats.json',stats)
    render(records,registry,stats)
    marker='<!-- AI-INTERVIEW-EXPANSION -->'
    if marker not in readme:
        intro=marker+'\n> **Expanded catalog / 扩展题库:** [Browse the sourced question index](expansion/README.md) · [中文使用说明](EXPANSION.zh-CN.md) · [Source registry](expansion/SOURCES.md). Original content is preserved; evidence types are explicitly separated.\n\n'
        (ROOT/'README.md').write_text(intro+readme,encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=False,indent=2))

def safe(s: str) -> str:
    return html.escape(str(s)).replace('|','&#124;').replace('\n',' ').replace('[','&#91;').replace(']','&#93;')

def render(records, sources, stats) -> None:
    lines=['# Expanded AI engineering interview catalog','', '> Community question banks are not verified company interview reports. Practice is explicitly labeled. Answers are linked, not reproduced or fact-checked.','',f"Snapshot: {stats['generated_at']}",'',f"**{stats['total_questions']} unique normalized prompts = {stats['baseline_questions']} inherited + {stats['new_questions']} additions.**",'', '[Sources and license audit](SOURCES.md) · [Machine-readable data](questions.json) · [Statistics](stats.json) · [Offline search](index.html) · [中文说明](../EXPANSION.zh-CN.md)','', '## Types','']
    for kind,n in stats['counts_by_kind'].items(): lines.append(f'- `{kind}`: {n}')
    lines+=['','## Company labels','', '> A company label means a source file or a practice target, NOT a proven interview at that company.','']
    directory=OUT/'companies'; directory.mkdir(exist_ok=True)
    for old in directory.glob('*.md'): old.unlink()
    for company in stats['company_labels']:
        slug=re.sub(r'[^a-z0-9]+','-',company.lower()).strip('-') or hashlib.sha256(company.encode()).hexdigest()[:12]
        matches=[r for r in records if company in r['companies']]
        lines.append(f'- [{safe(company)}](companies/{slug}.md): {len(matches)}')
        page=[f'# {company}','', '> Source-file labels and targeted practice only. Do not interpret this page as a list of verified interview questions.','']
        for r in matches: page.append(f"- **{r['id']}** `{r['kind']}` — {safe(r['question'])} [Source / reading]({r['source_url']})")
        (directory/(slug+'.md')).write_text('\n'.join(page)+'\n',encoding='utf-8')
    lines+=['','## Topic index','']
    topics_dir=OUT/'topics'; topics_dir.mkdir(exist_ok=True)
    for old in topics_dir.glob('*.md'): old.unlink()
    for topic in sorted({t for r in records for t in r['topics']}):
        matches=[r for r in records if topic in r['topics']]
        lines.append(f'- [{topic}](topics/{topic}.md): {len(matches)} (topic membership can overlap)')
        page=[f'# {topic}','', '> Automatic keyword tags; counts overlap across topics. Machine-extracted candidates require editorial review. These are not verified company interviews.','']
        for r in matches: page.append(f"- **{r['id']}** `{r['kind']}` — {safe(r['question'])} [Source / reading]({r['source_url']})")
        (topics_dir/(topic+'.md')).write_text('\n'.join(page)+'\n',encoding='utf-8')
    (OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    source_lines=['# Source registry and reuse audit','', '> Only question headings from allowlisted permissive licenses are indexed. Other sources remain links. Original license notices are retained separately; this project does not relicense third-party material.','', '| Repository | Status | License | Added | Merged duplicates | Snapshot |','|---|---|---|---:|---:|---|']
    for s in sources:
        license_link=f"[{s.get('license','unknown')}]({s['license_file']})" if s.get('license_file') else s.get('license','unknown')
        source_lines.append(f"| [{s['repository']}]({s['url']}) | {s['status']} | {license_link} | {s['questions_added']} | {s['duplicates_merged']} | [snapshot]({s.get('snapshot_url',s['url'])}) |")
    for s in sources:
        if s.get('error'): source_lines.append(f"\nCollection error for `{s['repository']}`: {safe(s['error'])}\n")
    (OUT/'SOURCES.md').write_text('\n'.join(source_lines)+'\n',encoding='utf-8')
    payload=json.dumps(records,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=(ROOT/'tools/catalog-template.html').read_text(encoding='utf-8')
    (OUT/'index.html').write_text(template.replace('__DATA__',payload),encoding='utf-8')

def self_test() -> None:
    sample='# How does attention work?\n- [How does attention work?](#how)\n- Answer: because\n```python\n# Why is this code?\n```\n<summary><b>2. Why use caching?</b></summary>\n- 如何设计一个多租户检索系统？\n'
    got=[q for _,q in candidates(sample)]
    assert got==['How does attention work?','Why use caching?','如何设计一个多租户检索系统？'],got
    assert norm('What is KV-cache?')==norm('what is KV cache')
    assert clean('[Why?](https://example.org)')=='Why?'
    assert 'retrieval' in tags('RAG retrieval')
    assert '<' not in safe('<script>')
    print('Parser, deduplication, tagging and escaping tests passed.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--self-test',action='store_true'); args=p.parse_args()
    if args.self_test: self_test()
    else: collect()
