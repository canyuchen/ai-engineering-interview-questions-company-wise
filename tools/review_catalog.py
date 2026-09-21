#!/usr/bin/env python3
"""Deterministic post-processing of a collected snapshot; does not access the network."""
from __future__ import annotations
import hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
from collect_sources import ROOT, OUT, BASE_SHA, norm, render

ALIASES={'Google DeepMind and Google AI':'Google DeepMind','Meta (Superintelligence Labs, FAIR, Llama)':'Meta','Moonshot AI (Kimi)':'Moonshot AI','Zhipu AI (GLM)':'Zhipu AI','Alibaba (Qwen)':'Alibaba / Qwen','Alibaba':'Alibaba / Qwen','Amazon (AWS)':'Amazon','Cursor (Anysphere)':'Cursor','Cognition (Devin, Windsurf)':'Cognition'}
EXCLUDED={norm(x) for x in ['How to use this','How to Use This Guide','实现复杂，吞吐受影响；','实现：需要更精细的 batched expert 计算（Megablocks）。']}

def canonicalize(text):
    match=re.match(r'^\[\[([^\]]+)\]\]\s*(?:\([^)]*\))?\s*[:：]\s*(.+)$',text)
    if match and norm(match[1])==norm(match[2]):text=match[1]
    match=re.match(r'^["“](.+[?？])["”]\*{0,2}\s*(?:[-—:]|\()',text)
    if match:text=match[1]
    return text.strip()

def main():
    rows=json.loads((OUT/'questions.json').read_text())
    sources=json.loads((OUT/'sources.json').read_text())
    stats=json.loads((OUT/'stats.json').read_text())
    # A second review is a no-op. A fresh collector run removes this marker.
    if stats.get('review_version')==1:
        print('Review v1 already applied; no changes.');return
    (OUT/'questions.raw.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    original_stats=dict(stats)
    if (ROOT/'.git').exists():
        baseline=subprocess.check_output(['git','show',BASE_SHA+':README.md'],cwd=ROOT).decode()
    else:
        baseline=(ROOT/'README.md').read_text()
        if baseline.startswith('<!-- AI-INTERVIEW-EXPANSION -->'):
            baseline=baseline.split('\n\n',1)[1]
    lines=baseline.splitlines(); sections={};heading='';heading_line=0
    for line_no,line in enumerate(lines,1):
        if line.startswith('## '):heading='';heading_line=0
        if line.startswith('### '):heading=line[4:].strip();heading_line=line_no
        sections[line_no]=(heading,heading_line)
    known=set(stats['company_labels'])|{'Tesla','Uber','Netflix','LinkedIn','Airbnb','Pinterest','Spotify'}
    audit={'version':1,'snapshot_generated_at':stats['generated_at'],'before':original_stats,'excluded':[],'normalized':[],'merged':[],'company_records_enriched':0,'limitations':'This is a limited deterministic cleanup, not full editorial or interview-authenticity verification.'}
    output=[];seen={};extra_merges=Counter()
    for row in rows:
        old=row['question']; q=canonicalize(old)
        if norm(q) in EXCLUDED:
            audit['excluded'].append({'id':row['id'],'question':old,'source_url':row['source_url'],'reason':'navigation or declarative answer fragment'});continue
        if row['id']=='q-935053635f8f6b':
            q='Does temperature = 0 guarantee deterministic outputs? Distinguish decoding policy from end-to-end reproducibility.'
            row['editorial_note']='Rephrased to test, rather than assume, the original premise. The source wording is retained in source_question.'
        if q!=old:
            row['source_question']=old;row['question']=q
            audit['normalized'].append({'id':row['id'],'before':old,'after':q})
        if row['kind']=='legacy_unverified':
            n=int(row['source_url'].rsplit('#L',1)[1]);section,section_line=sections.get(n,('',0))
            row['source_section']=section
            labels=set(row['companies']);name=ALIASES.get(section,section)
            if name in known:labels.add(name)
            for following in lines[n:n+8]:
                if following.startswith(('- ','#')):break
                if 'Asked at:' in following:
                    for label in re.findall(r'\[([^\]]+)\]\(',following):
                        label=ALIASES.get(label,label)
                        if label in known:labels.add(label)
            if labels!=set(row['companies']):audit['company_records_enriched']+=1
            row['companies']=sorted(labels)
            row['company_relation']='inherited_unverified_labels_not_independent_confirmation'
        key=norm(q)
        if key in seen:
            previous=seen[key]
            previous['companies']=sorted(set(previous['companies'])|set(row['companies']))
            previous['topics']=sorted(set(previous['topics'])|set(row['topics']))
            previous.setdefault('additional_sources',[]).append({'url':row['source_url'],'source_id':row['source_id'],'company_label':None,'merged_record_id':row['id']})
            previous['additional_sources'].extend(row.get('additional_sources',[]))
            audit['merged'].append({'from':row['id'],'into':previous['id']})
            extra_merges[row['source_id']]+=1
        else:seen[key]=row;output.append(row)
    primary_counts=Counter(r['source_id'] for r in output if r['kind']=='community_question_bank')
    for source in sources:
        source['initial_questions_added']=source['questions_added']
        source['questions_added']=primary_counts[source['id']]
        source['duplicates_merged']+=extra_merges[source['id']]
    counts=Counter(r['kind'] for r in output)
    stats.update({'review_version':1,'initial_collection_total':len(rows),'baseline_questions':counts['legacy_unverified'],'new_questions':len(output)-counts['legacy_unverified'],'total_questions':len(output),'counts_by_kind':dict(counts),'company_labels':sorted({c for r in output for c in r['companies']}),'normalized_duplicates_merged':stats['normalized_duplicates_merged']+len(audit['merged']),'review_excluded':len(audit['excluded']),'review_extra_duplicates':len(audit['merged'])})
    for name,obj in [('questions.json',output),('sources.json',sources),('stats.json',stats),('review-audit.json',audit)]:
        (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    render(output,sources,stats)
    note=f'''# Snapshot review / 数据复核\n\nThis snapshot contains **{len(output)}** indexed prompts after limited cleanup, versus **{len(rows)}** in the original automatic collection.\n\n- Removed {len(audit['excluded'])} navigation or answer-fragment entries.\n- Normalized {len(audit['normalized'])} wiki-link repetitions, quoted follow-ups, or explicitly noted premises.\n- Merged {len(audit['merged'])} additional normalized duplicates.\n- Enriched {audit['company_records_enriched']} inherited records using their original company headings or Asked at labels. These labels remain unverified.\n\n[Full audit](review-audit.json) · [Original automatic snapshot](questions.raw.json) · [Current index](README.md)\n\nThis is NOT a full question-by-question technical review or verification that an employer asked any question. Source answers remain unreviewed. Unicode/punctuation deduplication and a few markup rules do not amount to semantic deduplication.\n\nRebuild from a Git checkout with `python tools/collect_sources.py`, then `python tools/review_catalog.py`, then `python tools/question_bank.py validate`. The review step itself makes no network requests and is idempotent.\n'''
    (OUT/'REVIEW.md').write_text(note)
    index=OUT/'README.md';index.write_text(index.read_text().replace('[Sources and license audit](SOURCES.md)','[Review and raw snapshot](REVIEW.md) · [Sources and license audit](SOURCES.md)'))
    print(json.dumps({k:stats[k] for k in ['total_questions','new_questions','baseline_questions','review_excluded','review_extra_duplicates']},ensure_ascii=False))

if __name__=='__main__':main()
