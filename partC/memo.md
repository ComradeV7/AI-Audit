# Part C: Decision Memo

**Scenario:** The product team wants our assistant's replies to sound casual
and conversational in Hindi, Kannada, Tamil, Telugu, Bengali and
Marathi current output reads too formal. Three options: 

(a) SFT on synthetic pairs, 

(b) small rewriter model, 

(c) prompt engineering only. 

Constraints: one A100-80GB for 2 weeks, one native reviewer (Hindi+Kannada only) for 10h/week, launch in 3 weeks, no external API budget.

---

## 1. Assumptions

- **1-2 min/item** for natural/unnatural judgment. Generous if reviewer explains why, not just pass/fail.
- **LoRA fine-tune** on 4.2B model, hundreds of examples, tone shift only: single-digit GPU-hours.
- **10h/week is a hard cap**, not averaged across 3 weeks (30h total, but max 600 min/week). Everything below respects weekly limits.
- **A100-80GB GPU** usage is on demand.
- The **rewriter model** has a overhead due to two request calls each time.

---

## 2. Arithmetic

**Reviewer capacity:** 1,800 minutes total. **Zero coverage for Tamil, Telugu, Bengali, Marathi**, 4 of 6 languages have no native quality gate.

**Timeline if prompt engineering is tested first:**
- Week 1: 390 min (pilot + refine, ~260 items): **Gate A checkpoint**
- Week 2: 450 min (confirm, ~300 items): **Gate B checkpoint**. Cumulative: 840 min, ~560 items.
- Week 3 fallback if killed at Gate B: 600 min max = 500 min review + 100 min verification

**Fallback is tighter under strict caps:** ~330 training pairs (~165/language, vs 500 total if flexible), ~65 verification items (~33/language, vs 140 total). Survivable but thin, verification especially squeezed.

**Why prompt-as-bootstrap beats pure SFT:** Using an optimized prompt to generate SFT training candidates (vs raw model output) lowers reviewer rejection rates, fewer "this sounds robotic" rejections means the same 1,800 minutes covers more approved pairs. You're not choosing between prompting and SFT, you're using prompting's cheapness to make SFT's data better.

**Rewriter option:** Same reviewer budget as SFT. Adds permanent per-request latency but structurally separates correctness from tone (main model answers first, separate pass adjusts style). Worth considering if correctness-tone entanglement is a risk for sensitive content. Not the default, but not dismissed conditional on product priorities.

---

## 3. Recommendation

**Hybrid bootstrap approach:**

**Week 1:** Find best prompt variant (pilot + refine, ~390 min, ~260 items). Tests whether base model has casual register at all. Part A's tokenizer findings suggest non-English training data skews formal, so this early signal matters.

**Weeks 2-3:** Use that prompt to generate SFT training candidates for Hindi/Kannada. Review candidates (500 min, ~330 pairs), train (LoRA, single-digit GPU-hours), verify on fresh unseen prompts (100 min, ~65 items). Under strict weekly caps, this is tighter than ideal but workable.

**Deploy:** SFT for Hindi/Kannada (the 2 languages with native verification). Prompt-only for Tamil/Telugu/Bengali/Marathi (the 4 with zero reviewer coverage). This is permanent architecture, not a temporary workaround, training those 4 on unverified data is a worse risk than shipping formal text.

---

## 4. Success Metric

**Primary (Hindi/Kannada):** Pairwise win-rate ≥70%, reviewer sees formal baseline vs casual candidate side-by-side for same prompt, picks which sounds more natural. Relative judgment is far more reliable from single rater than absolute 1-5 scale (no second rater = no inter-rater calibration check). Include 0% semantic distortion gate: track % where casual rewrite changed meaning or added inappropriate content, must stay at zero. "More casual" and "still correct" are different things, metric checks both.

**Proxy (Other 4 languages):** Automated rule-based score delta. Weak proxy, tracks vocabulary shifts, not human naturalness but only signal available without native reviewers.

---

## 5. Kill Criteria (Staged)

**Gate A (Day 7, ~260 items reviewed):** If win-rate ≤0%, kill prompting entirely and pivot remaining ~23 hours to pure SFT. Tests whether base model knows casual at all.

**Gate B (Day 14, ~560 items reviewed):** If win-rate positive but <70%, lock prompt for the 4 unverified languages and route Hindi/Kannada into SFT bootstrap. Week 3's 600 min cap allows 500 min review (~330 pairs) + 100 min verification (~65 items).

Staged gates fail fast if prompting is hopeless but preserve the SFT path if it's just insufficient.

---

## 6. Day-1 Experiment

Draft 3 casual-tone prompt variants. Run against 10 real prompts per language × 2 languages = 60 items total, 90 minutes. Reviewer scores Hindi/Kannada same day via pairwise preference. Automated rule-based scoring for the other 4. Cheap test of whether base model's pretraining contains casual register before committing to dataset generation.
