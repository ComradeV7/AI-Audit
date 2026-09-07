# Audit Assessment Submission

## Quick Navigation

**Core Documents**
- `NOTEBOOK.md` — Chronological process log
- `AI_USAGE.md` — Where AI helped and where it misled me
- `requirements.txt` — Python dependencies

**Part A: Tokenizer Fertility Audit**
- `partA/results/A3_corrected_analysis.md` — Technical analysis (5.89× → 1.17×)
- `partA/results/A4_memo.md` — Recommendation memo
- `partA/results/fertility_grid.csv` — Full 4×4×3 grid results
- `partA/results/raw_counts.csv` — Token/word/byte/sentence counts
- `partA/scripts/` — Corpus builder, bug isolation tests, grid runner

**Part B: Serving Capacity Analysis**
- `partB/RESULTS.md` — Clean writeup (capacity reconciliation)
- `partB/scripts/` — KV cache math, throughput anomaly, goodput derivation
- `partB/outputs/` — Raw script outputs (B1-B3)

**Part C: Casual-Tone Strategy**
- `partC/memo.md` — Decision memo (bootstrap hybrid approach)

---

## Setup

```bash
python -m venv audit-env
audit-env\Scripts\activate
pip install -r requirements.txt
```

---

## Key Findings

**Part A:** Hindi 1.17× English (not 5.89×). Gap was GPT-2 training data, not script properties. Corrected range ~1.05-1.2× across languages.

**Part B:** KV cache ceiling = 25 sequences. Throughput peaks at batch 24 (1607 tok/s), declines at 32/48 due to preemption overhead. Honest goodput 201 tok/s (not 3200 tok/s).

**Part C:** Bootstrap hybrid strategy. Week 1 prompt testing (~260 items), weeks 2-3 SFT training for Hindi/Kannada only (~330 pairs). Strict 10h/week reviewer budget, 4-language verification gap.
