# Part B: Capacity Reconciliation 

All calculations below are derived programmatically from model_spec.md and bench_log.csv using the Part B scripts.

---

## B1. KV Cache Capacity & Sequence Limits

**KV cache bytes per token:**
```
2 × 28 layers × 8 KV heads × 128 head_dim × 2 bytes (fp16)
= 114,688 bytes/token
```

**Bytes per full 4096-token sequence:**
```
114,688 bytes/token × 4096 tokens
= 469,762,048 bytes
= 0.470 GB
```

**VRAM budget (using decimal GB: 1 GB = 1e9 bytes, matching NVIDIA vendor convention):**
```
Total VRAM:        24 GB × 0.92 utilization = 22.08 GB
- Weights:         8.4 GB (4.2B params × 2 bytes fp16)
- Overhead:        1.6 GB (activations, CUDA graphs)
= Available:       12.08 GB for KV cache
```

**Maximum concurrent 4096-token sequences:**
```
12.08 GB / 0.470 GB per sequence
= 25.72 sequences
= 25 sequences (floor)
```

**Validation against bench_log.csv (prompt_len=3584):**

| batch | predicted preempt | actual | predicted util | actual |
|-------|-------------------|--------|----------------|--------|
| 4     | 0                 | 0      | 0.16           | 0.16   |
| 8     | 0                 | 0      | 0.31           | 0.31   |
| 16    | 0                 | 0      | 0.62           | 0.62   |
| 24    | 0                 | 0      | 0.93           | 0.93   |
| 32    | 7                 | 7      | 1.00           | 0.97   |
| 48    | 23                | 23     | 1.00           | 0.97   |

Predicted ceiling matches preemption counts exactly at every batch size. One discrepancy: predicted 1.00 utilization at batch 32/48, actual caps at 0.97, likely due to block-allocation granularity or reserved scheduler margin, not a flaw in the capacity math.

---

## B2. Throughput Anomaly & Proposed Fix

**Baseline:** batch=4 delivers 565.4 tok/s. Naive linear scaling predicts per-request rate holds constant at 141.35 tok/s/request.

**Actual vs naive prediction:**

| batch | reported tok/s | naive prediction | vs naive | Δ throughput | preempt | kv_util | wall_s | ttft_ms |
|-------|----------------|------------------|----------|--------------|---------|---------|--------|---------|
| 4     | 565.4          | 565.4            | +0.0     | —            | 0       | 0.16    | 29.0   | 483.2   |
| 8     | 902.6          | 1130.8           | -228.2   | +337.2       | 0       | 0.31    | 36.3   | 519.0   |
| 16    | 1311.4         | 2261.6           | -950.2   | +408.8       | 0       | 0.62    | 50.0   | 498.3   |
| 24    | 1607.4         | 3392.4           | -1785.0  | +296.0       | 0       | 0.93    | 61.2   | 500.5   |
| 32    | 1384.0         | 4523.2           | -3139.2  | **-223.4**   | 7       | 0.97    | 94.7   | 636.9   |
| 48    | 1298.5         | 6784.8           | -5486.3  | **-85.5**    | 23      | 0.97    | 151.4  | 955.4   |

**Peak:** batch=24, 1607.4 tok/s.

**Decline:** Throughput drops in absolute terms at batch=32 (-223.4 tok/s) and again at batch=48 (-85.5 tok/s). This isn't sublinear scaling—it's regression.

**Mechanism:**

At batch=32, the system exceeds the 25-sequence KV ceiling established in B1. The scheduler starts preempting (7 sequences). KV cache utilization hits the cap (0.97). Wall clock jumps 55% (94.7s vs 61.2s at batch=24). Median time-to-first-token spikes 27% (636.9ms vs 500.5ms). Preemption overhead—swapping KV cache blocks in and out of VRAM, recomputation for evicted sequences—dominates, erasing the benefit of additional batch size.

At batch=48, the pattern intensifies: 23 sequences preempted, wall clock 2.5× the batch=24 baseline, ttft nearly doubles (955.4ms).

**Proposed fix:**

Set `max_num_seqs=25` for the 3584-4096 token prompt-length regime.

**Predicted effect:**

Throughput holds at 1607.4 tok/s (the batch=24 peak) instead of declining to 1298.5 tok/s at batch=48. Eliminates 23 preemptions. Prevents ttft from spiking to 955ms, keeping latency under 600ms for acceptable UX.

---

## B3. The Misread Metric & Honest Goodput

**Formula test (6 rows from bench_log.csv):**

| prompt | batch | reported | computed | match |
|--------|-------|----------|----------|-------|
| 512    | 16    | 883.2    | 883.4    | ✓     |
| 512    | 32    | 1489.6   | 1489.5   | ✓     |
| 512    | 64    | 2267.3   | 2267.2   | ✓     |
| 3584   | 16    | 1311.4   | 1311.5   | ✓     |
| 3584   | 24    | 1607.4   | 1607.3   | ✓     |
| 3584   | 48    | 1298.5   | 1298.5   | ✓     |

**Formula:** `reported_tok_s = (prompt_len + gen_len) × num_requests / wall_clock_s`

This proves reported_tok_s includes prefill tokens, counted at the same weight as decode tokens. For long prompts (3584 tokens), this inflates the metric by 7-8×—prefill is one-time overhead, not user-visible per-token generation.

**Honest goodput (batch=24, prompt=3584):**

**Method (a) — End-to-end average:**
```
generated_tokens = 512 × 24 = 12,288
goodput = 12,288 / 61.16s = 200.9 tok/s
```

**Method (b) — Steady-state decode rate:**
```
itl_ms_p50 = 96.07ms
goodput = 24 / 96.07ms = 249.8 tok/s
```

**Gap: 48.9 tok/s (24.3%)**

The gap exists because itl_ms_p50 is a median. Extrapolating from it (512 generation steps × 96.07ms + ttft ≈ 49.6s) predicts wall clock far shorter than the actual 61.16s. The true per-step latency distribution is right-skewed: most steps complete quickly, but some take longer (memory pressure, scheduling jitter), pulling the mean above the median. Method (a), using the full wall clock, captures this reality. Method (b) is a best-case steady-state figure, not what users experience end-to-end.

**Honest goodput at batch=48:**
```
(512 × 48) / 151.41s = 162.3 tok/s
```

**What REPORT_v0 should have said:**

"batch 24 delivers 201 tok/s of goodput (generated tokens only). batch 48 declines to 162 tok/s due to preemption overhead."

Not "batch 48 will deliver ~3200 tok/s." That projection (based on a naive linear fit) is 16-20× higher than actual goodput. Even the logged reported_tok_s at batch=48 (1298.5 tok/s) includes prefill tokens and overstates user-visible throughput by 8×.

---

## B4. Production Monitoring

Track `kv_cache_swaps_per_second` or `preemption_rate` in a live dashboard. Under proper limits (batch ≤ 25 for long prompts), this counter should stay flat at zero. If it spikes above 0.1 swaps/sec while `p95_ttft_ms` simultaneously exceeds 700ms, you've passed the KV ceiling—goodput is declining even as batch size climbs, the same mechanism observed at batch=32-48 in this analysis. Cross-reference with wall clock per request: if wall time grows faster than batch size, scheduler thrashing is confirmed.
