# Audit Notebook

## [01-09-2026] Setup

Read the brief. Starter kit: fertility.py, REPORT_v0.md, corpus_sample/ (English+Hindi, ~10 lines each), bench/model_spec.md, bench/bench_log.csv.

Setup venv with `uv`. Made requirements.txt.

Installed:
```
matplotlib==3.11.1, pandas==3.0.3, regex==2026.5.9
tokenizers==0.22.2, torch==2.12.0, transformers==5.12.0
```

Plan: audit A before B; B before C.

---

## [01-09-2026] First impressions

Read all starter files once through.

**REPORT_v0.md:** Claims Hindi 5.89× worse than English (1.27 vs 7.45 tok/word). Says tok/char "confirms" at 7.0×. Recommends 6× serving budget for Hindi. Also claims longer prompts give better throughput (1311 vs 883 tok/s) and projects 3200 tok/s at batch 48.

**fertility.py:** Lowercases all text, uses `line.split(" ")` for word counting, normalizes to NFC. Has `random.seed(1337)` but no random calls visible.

**Corpus samples:** 10 lines each. Both have double spaces (English line 7 "books  in", Hindi line 10 similar). This will break `split(" ")`.

**bench_log.csv:** 13 rows. Batch 48 shows 1298 tok/s with 23 preempted sequences, not the 3200 the report projected. Linear scaling assumption is wrong.

**Suspicious:**
- 5.89× vs 7.0× don't "agree"—they measure different things
- Word counting via `split(" ")` breaks on double spaces
- 10 lines is not enough data
- Lowercasing might hurt case-sensitive tokenization
- Report ignores actual data and fits naive curves

**Don't understand yet:**
- Why set random seed if not used?
- What's the KV cache math?
- Are preemptions causing throughput drop?
- Is Hindi tok/char high because of Unicode properties or tokenizer training?

---

## [01-09-2026] A1: Corpus construction

Need bigger corpus. Chose FLORES-200 (industry standard, parallel, professionally translated).

**Languages:** English (eng), Hindi (hin), Tamil (tam), Telugu (tel). Mix of Latin and Indic scripts.

**Preprocessing:** Keep punctuation, keep casing, apply NFC normalization.

Wrote `partA/scripts/build_corpus.py` to pull devtest split (1012 sentences per language).

**Issues:**
- facebook/flores gated, needed auth token. Pivoted to gsarti/flores_101 (ungated mirror).
- datasets v3.0+ blocks trust_remote_code. Pinned to v2.16.0.

**Result:** 1012 sentences × 4 languages. Avg length 130 chars (English/Hindi/Telugu), 152 chars (Tamil). Spot-checked sentence #42—looks correct.

**Caveat:** FLORES is formal (Wikipedia/news). Won't tell us about casual chat, slang, or code-switching (Hinglish/Tanglish) which is probably actual production traffic.

---

## [02-09-2026] Split bug

**Claim:** `split(" ")` creates phantom words from double spaces.

**Command:** `python partA/scripts/test_split_bug.py`

**Output:**
```
SPLIT BUG (split(' ') vs split()): 

English - Buggy: 1.265  Fixed: 1.283  Delta: +0.018
Hindi   - Buggy: 7.448  Fixed: 7.598  Delta: +0.150

Ratio - Buggy: 5.89x  Fixed: 5.92x  Delta: +0.03x
```

**Why it proves it:** Both samples have one line with double spaces. Buggy `split(" ")` creates empty strings in the list, inflating word count. Correct `split()` ignores extra whitespace. Fixing it increases fertility by removing phantom words from denominator.

**Reproduced intern's exact numbers** (1.265, 7.448), so isolation works.

Impact: +0.03× on ratio (0.5%). Confirmed bug but small on this sample.

---

## [02-09-2026] Math bug

**Claim:** Mean-of-ratios over-weights short sentences vs ratio-of-totals.

**Command:** `python partA/scripts/test_math_bug.py`

**Output:**
```
MATH BUG (mean-of-ratios vs ratio-of-totals): 

English - Buggy: 1.265  Fixed: 1.253  Delta: -0.012
Hindi   - Buggy: 7.448  Fixed: 7.403  Delta: -0.045

Ratio - Buggy: 5.89x  Fixed: 5.91x  Delta: +0.02x
```

**Why it proves it:** Intern uses `sum(ratios)/n` which gives equal weight to all lines. Short Hindi sentences have higher fertility (8.75 for 4-word line). Over-weighting them pulls average up. Correct method is `sum(tokens)/sum(words)`.

Reproduced intern's numbers exactly.

Impact: +0.02× on ratio (0.3%). Mathematically wrong but empirically small on this corpus.

---

## [02-09-2026] Lowercase bug (sample corpus)

**Claim:** Lowercasing breaks case-sensitive tokenization asymmetrically.

**Command:** `python partA/scripts/test_lower_bug.py`

**Output:**
```
LOWERCASE BUG (line.lower() vs line): 

English - Lowered: 1.283  Fixed: 1.247  Delta: -0.036
Hindi   - Lowered: 7.598  Fixed: 7.598  Delta: +0.000

Ratio - Lowered: 5.92x  Fixed: 6.09x  Delta: +0.17x
```

**Why it proves it:** Zero delta for Hindi proves asymmetry. English has proper nouns (NASA, ISRO) that tokenize differently when lowercased. GPT-2 learned "NASA" as 1 token but "nasa" splits. Hindi Devanagari has no case so lowercasing does nothing.

Impact: +0.17× on ratio (2.9%). This is the biggest bug so far. Asymmetric—only hurts English.

---

## [02-09-2026] Grapheme clusters

**Claim:** `len()` counts codepoints, not visual graphemes. Inflates character count for Devanagari.

**Command:** `python partA/scripts/test_graphemes.py`

**Output:**
```
GRAPHEME CLUSTER TEST (tok/char metric)

Example: Codepoints vs Graphemes
'किताबें' (Hindi): 7 codepoints, 3 graphemes
'Hello' (English): 5 codepoints, 5 graphemes
Corpus Analysis:

English - tok/codepoint: 0.221  tok/grapheme: 0.221  Inflation: 1.00x
Hindi   - tok/codepoint: 1.583  tok/grapheme: 2.441  Inflation: 1.54x

Distortion Analysis:
English distortion: +0.000 (codepoint-based is deflated)
Hindi distortion:   -0.859 (codepoint-based is deflated)
```

**Why it matters:** Invisible matras/viramas inflate denominator. Hindi's tok/char looks "good" (1.58) but true visual is 2.44.

**Verdict:** Not a code bug—code computes what it says (tok/codepoint). Metric interpretation issue. Should it measure tok/grapheme instead?

---

## [02-09-2026] Punctuation handling

**Claim:** Punctuation tokenized but not counted as words. Is this right?

**Command:** `python partA/scripts/test_punctuation.py`

**Output:**
```
PUNCTUATION HANDLING TEST:

Punctuation Density:
English: 0.128 marks/word
Hindi:   0.016 marks/word
Ratio:   7.8x difference

Fertility Analysis:
English - With: 1.269  Without: 1.128  Delta: -0.141
Hindi   - With: 7.525  Without: 7.492  Delta: -0.033

Punctuation Contribution:
English adds: 0.141 tok/word from punctuation
Hindi adds:   0.033 tok/word from punctuation
```

**Why it matters:** Production text has punctuation which costs tokens. Method is correct for cost estimation. But English has 8× more punctuation—this is corpus artifact, not a bug.

**Verdict:** Handling correct. Density difference actually helps intern's case (inflates English more, reduces gap).

---

## [02-09-2026] Unicode normalization

**Claim:** NFC happens after `strip()`. Could this break things?

**Command:** `python partA/scripts/test_unicode_normalization.py`

**Output:**
```
UNICODE NORMALIZATION TEST

Whitespace Character Analysis:

English - Regular: 69  NBSP: 0  Tab: 0
Hindi   - Regular: 52  NBSP: 1  Tab: 0

Non-standard Whitespace Found:
English: None (all standard)
Hindi:   1 NBSP, 0 tabs
```

Found 1 non-breaking space in Hindi (likely the double-space artifact).

**Verdict:** NFC is correct. Ensures consistent byte representation. `strip()` only removes U+0020 and newlines, not combining marks, so timing is fine.

---

## [03-09-2026] Lowercase bug on full corpus

Sample showed +0.17× from lowercase bug. Need to check if it holds on full 1012-sentence corpus.

**Command:** `python partA/scripts/test_lower_on_eval.py`

**Output (ratio-of-totals method):**
```
Loading evaluation corpus...
Loaded: eng=1012, hin=1012, tam=1012, tel=1012

Initializing tokenizer...
Tokenizer ready. Processing...

LOWERCASE BUG - Intern's Method (mean-of-ratios):
eng - Lowered: 1.287  Original: 1.244  Delta: -0.043
hin - Lowered: 7.867  Original: 7.867  Delta: -0.000
tam - Lowered: 25.252  Original: 25.251  Delta: -0.001
tel - Lowered: 20.830  Original: 20.824  Delta: -0.006

Hindi/English Ratio:
  Lowered:  6.11x
  Original: 6.32x
  Delta:    +0.21x

LOWERCASE BUG - Correct Method (ratio-of-totals):
eng - Lowered: 1.278  Original: 1.235  Delta: -0.043
hin - Lowered: 7.827  Original: 7.826  Delta: -0.000
tam - Lowered: 25.049  Original: 25.047  Delta: -0.001
tel - Lowered: 20.714  Original: 20.708  Delta: -0.006

Hindi/English Ratio:
  Lowered:  6.12x
  Original: 6.34x
  Delta:    +0.21x
```

**Why it matters:**
- Asymmetry confirmed: English -0.043, Indic languages ~0.000
- Effect grew from +0.17× (sample) to +0.21× (full corpus)
- Holds across both aggregation methods (tested intern's mean-of-ratios and correct ratio-of-totals)
- Tamil (25×) and Telugu (21×) also show asymmetry

**Verdict:** Lowercase bug is systematic. Underestimates Latin-vs-Indic differences by measuring text users never send.

---

## [03-09-2026] Random seed

Noticed `random.seed(1337)` in fertility.py but no `random.*` calls anywhere.

**Evidence:** Searched code. Zero usage.

**Impact:** None. Dead code.

---



## [03-09-2026] Full grid run

**Command:** `python partA/scripts/fertility_full_grid.py`

Ran all 4 denominators × 4 languages × 3 tokenizers on the full 1012-sentence corpus. Output saved to `partA/results/fertility_grid.csv` and `partA/results/raw_counts.csv`.

---

## [03-09-2026] Denominator tests (Test 1 + Test 2)

**Claim:** Does swapping to a fair tokenizer collapse the gap (Test 1), and does the "worst language" ranking hold across denominators (Test 2)?

**Command:** `python partA/scripts/denominator_tests.py`

**Numbers (Test 1, shrink fraction 1-(ai4bharat/gpt2)):**
```
tam: 0.932
tel: 0.918
hin: 0.842
eng: -0.001
```

**Numbers (Test 2, ratio to English under ai4bharat):**
```
hin: word=0.999  graph=1.795  byte=0.458  sent=1.169
tam: word=1.371  graph=1.390  byte=0.329  sent=1.050
tel: word=1.374  graph=1.832  byte=0.397  sent=1.063
```

**Numbers (Test 2 extended, worst performer per metric):**
```
tok_per_word  : worst=tel (1.374)
tok_per_graph : worst=tel (1.832)
tok_per_byte  : worst=hin (0.458)
tok_per_sent  : worst=hin (1.169)
```

**Why it matters:** Shrink is near-total for all three Indic languages (84-93%). Most of the report's claimed gap was GPT-2's training data, not the language. Worst performer splits two-and-two between Hindi and Telugu depending on which denominator you pick. Tamil never ranks worst on anything.

**Verdict:**

Test 1's shrink fraction is identical across all four denominators for a given language because the denominator cancels out algebraically, it reduces to total_tokens_ai4bharat / total_tokens_gpt2. Test 1 measures pure tokenizer efficiency, independent of unit choice. Test 2 is the opposite: same tokenizer, same token counts, but "worst language" changes because the denominator changes what's held constant. GPT-2 was the dominant source of the report's error (Test 1). Denominator choice is a real, separate design decision, not a tie-breaker (Test 2).


---

## [03-09-2026] A3 conclusion

Chosen metric: tok/sentence (ratio-of-totals), ai4bharat tokenizer. Corrected range: ~1.05-1.2× English, not the report's 5.89-6×. tok/sentence holds meaning constant, which is what GPU cost actually track,s users send sentences with intent, not arbitrary word or byte counts.

## [03-09-2026] A4 memo

Wrote recomendation memo of REPORT_v0 at `partA/results/A4_memo.md`. Uses tok/sentence + ai4bharat numbers from A3: Hindi 1.17× English, Tamil/Telugu ~1.05-1.06×. Corrected range ~1.05-1.2× not 5.89-6×. Root cause: 84-93% shrink for Indic languages proves gap was GPT-2's training data, not script properties. Caught and fixed direction error during review (English marginally worse under ai4bharat, not better—shrink was -0.001, meaning slight increase as expected for multilingual tokenizer vs English-native one). Part A done.


---

## [04-09-2026] B1: KV cache capacity

**Claim:** Can compute max concurrent sequences from KV cache math, validate against preemptions.

**Command:** `python partB/scripts/kv_cache_math.py`

Script now runs successfully (path issues fixed). Output below supersedes earlier hand-traced numbers.

**Numbers (KV cache math):**
```
KV bytes/token: 114,688 bytes/token
Bytes per 4096-token sequence: 469,762,048 bytes = 0.470 GB
Available VRAM: 12.08 GB
Max concurrent sequences: 25 (floor)
```

**Numbers (validation against bench_log.csv, prompt_len=3584):**
```
batch  pred_preempt  actual  pred_util  actual
    4             0       0       0.16    0.16
    8             0       0       0.31    0.31
   16             0       0       0.62    0.62
   24             0       0       0.93    0.93
   32             7       7       1.00    0.97
   48            23      23       1.00    0.97
```

**Why it proves it:** Ceiling is 25 concurrent 4096-token sequences. At batch=24, util hits 0.93 (24/25.72). At batch=32, starts preempting exactly batch-25=7 sequences. Prediction matches logged data perfectly.

**Verdict:** KV cache limit confirmed. batch>25 triggers preemptions. GB vs GiB: used decimal (1 GB = 1e9 bytes) to match NVIDIA's convention.


---

## [04-09-2026] B2: Throughput anomaly

**Claim:** Throughput peaks then declines. Where and why?

**Command:** `python partB/scripts/throughput_anomaly.py`

Script now runs successfully. Output below supersedes earlier hand-traced numbers.

**Numbers (prompt_len=3584 sweep):**
```
Baseline: 565.4 tok/s at batch=4

batch  reported  naive_pred   vs_naive  Δ_tput  preempt  kv_util  wall_s  ttft_ms
    4     565.4       565.4       +0.0     +0.0        0     0.16    29.0    483.2
    8     902.6      1130.8     -228.2   +337.2        0     0.31    36.3    519.0
   16    1311.4      2261.6     -950.2   +408.8        0     0.62    50.0    498.3
   24    1607.4      3392.4    -1785.0   +296.0        0     0.93    61.2    500.5 PEAK
   32    1384.0      4523.2    -3139.2   -223.4        7     0.97    94.7    636.9 DECLINE
   48    1298.5      6784.8    -5486.3    -85.5       23     0.97   151.4    955.4
```

**Why it proves it:** Throughput peaks at batch=24 (1607.4 tok/s), then actually declines at batch=32 (-223.4 tok/s delta) and batch=48 (-85.5 tok/s). This isn't just sublinear scaling—it's absolute regression. At batch=32, preemptions start (7 seqs), kv_util hits ceiling (0.97), wall clock jumps 55% (94.7 vs 61.2s), ttft spikes 27% (636.9 vs 500.5ms). Preemption overhead dominates.

**Verdict:** Mechanism confirmed. Once batch > 25-sequence KV ceiling, scheduler thrashes. Proposed fix: set `max_num_seqs=25` for 3584-4096 token regime. Predicted effect: throughput holds at 1607.4 tok/s (batch=24 peak) instead of declining to 1298.5 tok/s at batch=48. Avoids 23 preemptions and prevents ttft from spiking to 955ms.


---

## [04-09-2026] B3: Goodput derivation

**Claim:** reported_tok_s includes prompt tokens (not goodput). Compute honest goodput.

**Command:** `python partB/scripts/goodput_derivation.py`

Script now runs successfully. Output below supersedes earlier hand-traced numbers. Hand-traced version had one arithmetic slip: batch=32/prompt=512 row showed 1489.9 (hand-trace) vs 1489.5 (actual)—a ~0.03% error. Caught and fixed, same as earlier path/table errors.

**Numbers (formula test on 6 rows):**
```
prompt  batch  reported  computed   match
   512     16     883.2     883.4   ✓
   512     32    1489.6    1489.5   ✓
   512     64    2267.3    2267.2   ✓
  3584     16    1311.4    1311.5   ✓
  3584     24    1607.4    1607.3   ✓
  3584     48    1298.5    1298.5   ✓

Formula: reported_tok_s = (prompt_len + gen_len) * num_requests / wall_clock_s
```

**Numbers (honest goodput, batch=24, prompt=3584):**
```
Method (a) - End-to-end average:
  generated_tokens = 512 * 24 = 12,288.0
  goodput = 12,288.0 / 61.16s = 200.9 tok/s

Method (b) - Steady-state decode:
  itl_ms_p50 = 96.07ms
  goodput = 24 / 96.07ms = 249.8 tok/s

Gap: 48.9 tok/s (ttft wait time)
```

**Why they differ:** Method (a) is end-to-end (includes 500ms ttft wait). Method (b) is instantaneous decode rate once generation starts. End-to-end is lower because prompt processing time is in the denominator but doesn't contribute generated tokens to numerator.

**Numbers (batch=48):**
```
Honest goodput: (512 * 48) / 151.41s = 162.3 tok/s
```

**What REPORT_v0 should have said:** "batch 24 delivers 201 tok/s of goodput (generated tokens). batch 48 declines to 162 tok/s due to preemption overhead." Not "batch 48 will deliver ~3200 tok/s"—that number (1298.5 actual reported_tok_s) includes prompt tokens and is still 8× too high vs real goodput.

**Verdict:** reported_tok_s is total tokens processed (prompt + generated). Misreading it as goodput overstates user-visible throughput by 6-8×.


---

## [04-09-2026] B4: Production counter

**What to monitor:** Track `kv_cache_swaps_per_second` or `preemption_rate` in a live dashboard.

**Expected pattern:** Should be near-zero when batch ≤ 25 for long prompts. Spikes above 0.1 swaps/sec indicate scheduler thrashing—throughput will be declining even if batch size is climbing. Cross-reference with `p95_ttft_ms` (should stay < 600ms for good UX). If preemption_rate > 0 and p95_ttft > 700ms simultaneously, you're past the KV ceiling and goodput is dropping, same mechanism we saw at batch=32-48.


---

## [04-09-2026] C: Decision memo

**Scenario:** Product wants casual replies in 6 languages (Hindi, Kannada, Tamil, Telugu, Bengali, Marathi). Current output too formal. Three options: SFT, rewriter, or prompt-only. Constraints: one A100 for 2 weeks, one reviewer (Hindi+Kannada) for 10h/week strict cap, 3 weeks to launch.

**Binding constraint:** Reviewer budget. 30h total (1,800 min) at 1.5 min/item = 1,200 max items. Zero coverage for 4 languages. Training on unverified synthetic data for those 4 is worse than shipping formal—teaches bad habits, not just fails to teach good ones.

**Decision:** Bootstrap hybrid. Week 1: Test 3-5 prompt variants on 10-20 real prompts (~390 min, ~260 items). Route Hindi/Kannada to reviewer for immediate pairwise check. Tests if base model has casual register before committing to dataset generation. Weeks 2-3: If prompting works, use best variant to generate SFT candidates for Hindi/Kannada. Review ~330 pairs, train LoRA (single-digit GPU-hours), verify on ~70 fresh items. Deploy SFT for Hindi/Kannada, prompt-only for the 4 unverified languages. Permanent architecture—bootstrap makes SFT more efficient (optimized prompt → fewer rejections → same budget covers more approved pairs).

**Success metric:** Pairwise win-rate ≥70%—reviewer sees formal baseline vs casual candidate side-by-side, picks which sounds more natural (relative judgment far more reliable from single rater than absolute 1-5 scale, no second rater = no calibration check). Plus 0% semantic distortion gate: track % where rewrite changed meaning or added inappropriate content, must stay zero. "More casual" and "still correct" are different, metric checks both. For the 4 unverified: automated formality-score delta (weak proxy, only signal available).

**Kill gates (staged):** Gate A (day 7, ~260 items): win-rate ≤0% → kill prompting, pivot remaining 23h to pure SFT. Gate B (day 14, ~560 items): win-rate <70% → lock prompt for 4 unverified languages, route Hindi/Kannada to SFT with 600-min fallback (400 for training, 200 for verification).

**Alternative:** Rewriter model kept as conditional option if correctness-tone entanglement is severe (sensitive content—trades per-request latency for structural separation). Not default—same reviewer bottleneck as SFT, plus Part B's 25-sequence KV penalty.

**Wrote:** `partC/memo.md`. Arithmetic under strict 10h/week caps. Fallback tighter than flexible averaging would allow (330 pairs vs 500 if pooled), but workable.

Assignment complete.

