#!/usr/bin/env python3
"""Structure-aware question extraction, used by the canonical rebuild.

Recognizes explicit Q markers, numbered scenarios and Q tables while retaining
source line numbers. Source answers and interview claims remain unverified.
"""
from __future__ import annotations
import argparse
import re
import collect_sources as c

START = re.compile(r'^(?:what|why|how|when|which|where|who|explain|describe|compare|implement|design|derive|write|given|suppose|can you|walk me|discuss|tell me|build|debug|optimi[sz]e|estimate|diagnose|evaluate|propose|validate|prove|show|solve|analy[sz]e|differentiate|什么|为什么|如何|怎样|怎么|请|解释|比较|设计|实现|手写|推导|给定|说说|讲讲|介绍|分析|假设)', re.I)
EXPLICIT = re.compile(r'^(?:Q(?:uestion)?\s*\d+\s*[.:)\-：]|Question\s*[:：]|问题\s*\d+\s*[:：.、])\s*', re.I)
NUMBER = re.compile(r'^\d+\s*[.)、：:]\s*')
META = re.compile(r'^(?:what they (?:emphasi[sz]e|look for)|what they.?re really testing|what (?:this|the) (?:repo|guide)|how (?:to (?:prepare|prep|contribute|use (?:this|the))|answers are structured)|why (?:this (?:repo|guide)|contribute)|contributing|references|sources|resources|interview (?:format|process|loop)|related repositories|study plan|table of contents|how much prep|如何贡献|为什么要做这个)', re.I)
GENERIC = {c.norm(x) for x in ['What problem does it solve?', 'What are its limitations?', 'What is the key insight/approach?', "What's the key insight/approach?", 'What would you do differently or as a follow-up?', 'Why it matters', 'How it works', 'What it covers', 'What to expect', 'Where to start', 'How to run', 'How to use', 'What to study', 'What to do next', 'Why this matters']}


def plain(raw: str) -> str:
    raw = re.sub(r'<[^>]*>', '', raw)
    raw = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', raw)
    raw = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', raw)
    raw = raw.replace('**', '').replace('__', '').strip('*_` \t')
    return c.html.unescape(re.sub(r'\s+', ' ', raw)).strip()


def is_question(q: str) -> bool:
    if not 8 <= len(q) <= 650 or META.match(q) or c.norm(q) in GENERIC:
        return False
    if re.match(r'^(?:answer|solution|source|asked at|note|reference|答案|来源|参考)\s*[:：]?', q, re.I):
        return False
    if re.search(r'\b(?:this repo(?:sitory)?|star this|sponsor this)\b|如何贡献|为什么要做这个', q, re.I):
        return False
    if START.match(q) or '?' in q or '？' in q:
        return True
    return bool(re.match(r'^(?:you |your |a |an |the team |our |we |imagine |assume )', q, re.I) and re.search(r'\b(?:design|build|write|implement|debug|handle|choose|fix|explain|estimate|serve|deploy|evaluate|run|scale|detect)\b', q, re.I))


def candidates(text: str):
    """Prefer explicit question boundaries over interrogative answer fragments."""
    lines = text.splitlines()
    explicit_count = numbered_count = 0
    for line in lines:
        raw = re.sub(r'^\s*(?:#{1,6}\s+|[-*+]\s+)', '', line).strip()
        p = plain(raw)
        if EXPLICIT.match(p):
            explicit_count += 1
        if re.match(r'^\s*#{1,6}\s+', line) and NUMBER.match(p) and is_question(NUMBER.sub('', p)):
            numbered_count += 1
    strict_explicit = explicit_count >= 2
    strict_numbered = numbered_count >= 2
    in_fence = False
    fence_char = ''
    detail_depth = 0
    suppressed_level = answer_level = None
    for n, line in enumerate(lines, 1):
        fence = re.match(r'^\s*(`{3,}|~{3,})', line)
        if fence:
            if not in_fence:
                in_fence = True
                fence_char = fence.group(1)[0]
            elif fence.group(1)[0] == fence_char:
                in_fence = False
            continue
        if in_fence:
            continue
        old_depth = detail_depth
        detail_depth = max(0, detail_depth + len(re.findall(r'<details\b', line, re.I)) - len(re.findall(r'</details\s*>', line, re.I)))
        summary = re.search(r'<summary\b[^>]*>(.*?)</summary\s*>', line, re.I)
        if summary:
            q = plain(summary.group(1))
            q = EXPLICIT.sub('', NUMBER.sub('', q)).strip()
            if old_depth <= 1 and is_question(q):
                yield n, q
            continue
        if old_depth or detail_depth:
            continue
        heading = re.match(r'^\s*(#{1,6})\s+(.+?)\s*#*$', line)
        bullet = re.match(r'^\s*(?:[-*+]\s+(?:\[[ xX]\]\s*)?|\d+[.)]\s+)(.+)', line)
        raw = heading.group(2) if heading else bullet.group(1) if bullet else line.strip()
        p = plain(raw)
        explicit = bool(EXPLICIT.match(p))
        numbered = bool(heading and NUMBER.match(p))
        if heading:
            level = len(heading.group(1))
            if suppressed_level is not None and level <= suppressed_level:
                suppressed_level = None
            if answer_level is not None and level <= answer_level:
                answer_level = None
            if META.match(p):
                suppressed_level = level
                continue
            if re.match(r'^(?:answer|solution|short answer|detailed (?:answer|explanation)|答案|解答)\b', p, re.I):
                answer_level = level
                continue
        if suppressed_level is not None and not explicit:
            continue
        if answer_level is not None and not explicit:
            continue
        if line.lstrip().startswith('|'):
            cells = [plain(x) for x in re.split(r'(?<!\\)\|', line.strip())[1:-1]]
            if len(cells) >= 2 and re.fullmatch(r'(?:Q\s*)?\d+', cells[0], re.I) and is_question(cells[1]):
                yield n, cells[1]
            continue
        if explicit:
            q = EXPLICIT.sub('', p).strip('*_` ')
            if is_question(q):
                yield n, q
            continue
        if strict_explicit or (strict_numbered and not numbered):
            continue
        if not heading and not bullet:
            continue
        if re.fullmatch(r'\[.*\]\(#[^)]*\)', raw.strip()):
            continue
        q = NUMBER.sub('', p).strip('*_` ')
        if is_question(q):
            yield n, q


def self_test() -> None:
    qa = '# What They Emphasize\n- Genuine commitment — why?\n## Interview Questions\n**Q1: Explain the KV cache.**\n- The answer raises a question: why?\n**Q2: Design a concurrent queue.**\n- Why is this answer incomplete?\n'
    assert list(candidates(qa)) == [(4, 'Explain the KV cache.'), (6, 'Design a concurrent queue.')]
    numeric = '## What they emphasise\n- Why this company?\n## Representative questions\n### 1. You need to run a model on 50000 documents. Write the Python.\n<details><summary>Answer</summary>\n- Why is this solution useful?\n</details>\n### 2. Design a memory store.\n## How to prepare\n- What books should you read?\n'
    assert [q for _, q in candidates(numeric)] == ['You need to run a model on 50000 documents. Write the Python.', 'Design a memory store.']
    table = '| # | Question | Answer |\n| Q1 | How does batching affect latency? | link |\n| Q2 | Explain attention masking. | link |\n'
    assert len(list(candidates(table))) == 2
    legacy = '### Anthropic\n#### Systems\n- Design an inference server.\n  - Answer: [Article](https://example.org)\n- You need to deploy a large model. Explain the trade-offs.\n'
    assert len(list(candidates(legacy))) == 2
    assert list(candidates('## How to prepare\n- What should I read?')) == []
    assert list(candidates('```python\n# How can this be code?\n```')) == []
    assert list(candidates('<details>\n<summary>1. Why use caching?</summary>\n- What is inside the answer?\n</details>')) == [(2, 'Why use caching?')]
    print('PASS: explicit Q markers, numbered scenarios, Q tables, answer exclusion, navigation exclusion, source lines.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        from rebuild import main
        main()
