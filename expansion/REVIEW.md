# Quality and coverage audit

Current snapshot: **4546** indexed prompts; **70** company labels; **20** topic labels.

The structure-aware extractor recognizes explicit Q markers, numbered scenarios and question tables, preserving original source line coordinates. Answer and navigation text is filtered before counting. The rights-aware refiner excludes archived reprints with unverified file-level reuse rights and records metadata without republishing excluded text.

[Extraction changes](extraction-audit.json) · [Rights exclusions](excluded.json) · [Source licenses](SOURCES.md) · [Statistics](stats.json) · [Official guidance and reported-source leads](REPORTED-SOURCES.md)

IDs, normalized prompt uniqueness, evidence labels, license files, source coordinates, per-source contributions and category counts are validated. Company tags may originate from shared source sections or inherited Asked at claims; they are not independent proof that an employer asked a question. Topics overlap. Rules can miss valid questions or retain noise; answers are linked and not endorsed. This is not exhaustive editorial review or semantic deduplication.

Rebuild in a full Git checkout with `python tools/rebuild.py`, then validate with `python tools/question_bank.py validate`. Offline catalog search does not require rebuilding.
