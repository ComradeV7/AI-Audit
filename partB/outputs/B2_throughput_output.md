# B2: Throughput Anomaly Output

```
Throughput Analysis (prompt_len=3584):
Baseline: 565.4 tok/s at batch=4

batch  reported  naive_pred   vs_naive  Δ_tput  preempt  kv_util  wall_s  ttft_ms
    4     565.4       565.4       +0.0     +0.0        0     0.16    29.0    483.2
    8     902.6      1130.8     -228.2   +337.2        0     0.31    36.3    519.0
   16    1311.4      2261.6     -950.2   +408.8        0     0.62    50.0    498.3
   24    1607.4      3392.4    -1785.0   +296.0        0     0.93    61.2    500.5 PEAK
   32    1384.0      4523.2    -3139.2   -223.4        7     0.97    94.7    636.9 DECLINE
   48    1298.5      6784.8    -5486.3    -85.5       23     0.97   151.4    955.4

Peak: batch=24, 1607.4 tok/s
At batch=32: drops to 1384.0 tok/s (-223.4)
At batch=48: drops to 1298.5 tok/s

Proposed fix: max_num_seqs=25
  Holds throughput at 1607.4 tok/s instead of declining to 1298.5 tok/s
```

**Key Finding:** Throughput actually declines (not just sublinear) once batch > 25. At batch=32, preemptions start (7 seqs), wall clock jumps 55% (94.7 vs 61.2s), ttft spikes 27% (637 vs 501ms). Scheduler thrashing dominates.
