# Snapshot review / 数据复核

This snapshot contains **3761** indexed prompts after limited cleanup, versus **3763** in the original automatic collection.

- Removed 2 navigation or answer-fragment entries.
- Normalized 62 wiki-link repetitions, quoted follow-ups, or explicitly noted premises.
- Merged 0 additional normalized duplicates.
- Enriched 0 inherited records using their original company headings or Asked at labels. These labels remain unverified.

[Full audit](review-audit.json) · [Original automatic snapshot](questions.raw.json) · [Current index](README.md)

This is NOT a full question-by-question technical review or verification that an employer asked any question. Source answers remain unreviewed. Unicode/punctuation deduplication and a few markup rules do not amount to semantic deduplication.

Rebuild from a Git checkout with `python tools/collect_sources.py`, then `python tools/review_catalog.py`, then `python tools/question_bank.py validate`. The review step itself makes no network requests and is idempotent.
