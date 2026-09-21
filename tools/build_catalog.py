#!/usr/bin/env python3
"""Build a sourced catalog with answer-body filtering, then apply rights-aware refinement."""
from __future__ import annotations
import argparse
import re
import collect_sources as c
import refine_catalog
from question_bank import validate

ORIGINAL_CANDIDATES = c.candidates
NAV = re.compile(r'^(?:how to (?:use|prepare|contribute|study)|where to (?:go|start|find)|what (?:they emphas|we cover|you.ll learn|you get|is included)|why (?:this repo|this guide|this matters)|getting started|next steps|resources|references|sources|company context|roles & titles|the interview loop|interview loop|study plan|learning path|table of contents|contributing|contribution|license|acknowledg)', re.I)
ASK = re.compile(r'^(?:what|why|how|when|which|where|who|whose|can|could|would|should|is|are|do|does|did|will|explain|describe|compare|implement|design|derive|write|build|given|suppose|imagine|consider|tell|walk|discuss|prove|estimate|calculate|sketch|solve|debug|optimize|find|list|name)\b', re.I)
SCENARIO = re.compile(r'^(?:you|your|a|an|two|we|our|the|there|let|during|in production)\b', re.I)
ANSWER = re.compile(r'^(?:answer|solution|hint|explanation|discussion|答案|解答|解析)(?:\b|[:：\s])', re.I)

def mask_answers(text: str) -> str:
    """Blank filtered lines rather than deleting them, preserving source coordinates."""
    output=[]; depth=0; scope=None; fenced=False
    for raw in text.splitlines():
        if re.match(r'^\s*(```|~~~)', raw):
            fenced=not fenced
            output.append(raw if depth==0 and scope is None else '')
            continue
        if fenced:
            output.append(raw if depth==0 and scope is None else '')
            continue
        heading=re.match(r'^\s*(#{1,6})\s+(.+)', raw)
        if heading and depth==0:
            level=len(heading[1]); title=c.clean(heading[2])
            if scope is not None and level<=scope: scope=None
            if NAV.match(title) or ANSWER.match(title): scope=level
        opens=len(re.findall(r'<details\b',raw,re.I))
        closes=len(re.findall(r'</details>',raw,re.I))
        summary=re.search(r'<summary[^>]*>(.*?)</summary>',raw,re.I)
        if summary:
            question=c.clean(summary[1])
            output.append('<summary>'+summary[1]+'</summary>' if scope is None and not ANSWER.match(question) else '')
        elif depth or opens or closes or scope is not None: output.append('')
        else: output.append(raw)
        depth=max(0,depth+opens-closes)
    return '\n'.join(output)+'\n' if output else ''

def valid_prompt(q: str) -> bool:
    text=q.lstrip('"\'“” ').replace('**','')
    if NAV.match(text): return False
    if re.match(r'^(?:write your (?:lp|star)|prepare the values|culture screen|read:|see also|实现复杂|实现：)',text,re.I): return False
    if re.search(r'[\u4e00-\u9fff]',text): return True
    if ASK.match(text): return True
    # A scenario may finish in an imperative rather than a question mark.
    return bool(SCENARIO.match(text) and ('?' in text or '？' in text or re.search(r'\b(?:write|implement|design|build|explain|estimate|debug|optimize)\b',text,re.I)))

def strict_candidates(text: str):
    masked=mask_answers(text)
    found={n:q for n,q in ORIGINAL_CANDIDATES(masked)}
    for n,line in enumerate(masked.splitlines(),1):
        match=re.match(r'^\s*#{1,6}\s+(?:Q\s*)?\d+[.):：]\s*(.+)',line,re.I)
        if match:
            q=c.clean(match[1])
            if 20<=len(q)<=650 and (ASK.match(q) or SCENARIO.match(q)): found.setdefault(n,q)
    for n,q in sorted(found.items()):
        if valid_prompt(q): yield n,q

def self_test() -> None:
    text='## What they emphasise\n- What is a culture screen?\n## Questions\n### 1. What is attention?\n<details><summary>Answer</summary>\n- Why not use another model?\n</details>\n### 2. You need to process ten million events. Write the Python.\n<details>\n<summary>3. How does retrieval work?</summary>\n- What is an answer bullet?\n</details>\n## Sources\n- How to prepare\n'
    got=[q for _,q in strict_candidates(text)]
    assert got==['What is attention?','You need to process ten million events. Write the Python.','How does retrieval work?'],got
    assert not valid_prompt('Wherever we have an answer, it is linked below.')
    assert not valid_prompt('实现复杂，吞吐受影响；')
    assert len(mask_answers(text).splitlines())==len(text.splitlines())
    print('PASS: answer masking, navigation filtering, imperative scenarios and stable source lines.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args();self_test()
    if not args.self_test:
        c.candidates=strict_candidates
        c.collect()
        c.candidates=ORIGINAL_CANDIDATES
        refine_catalog.main()
        import json
        validate(json.loads((c.OUT/'questions.json').read_text(encoding='utf-8')))
