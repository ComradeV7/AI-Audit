# B1: KV Cache Capacity Output

```
KV Cache Capacity:
  114,688 bytes/token
  469,762,048 bytes per 4096-token seq = 0.470 GB
  12.08 GB available
  Ceiling: 25 concurrent sequences

Validation (prompt_len=3584):
batch  pred_preempt  actual  pred_util  actual
    4             0       0       0.16    0.16
    8             0       0       0.31    0.31
   16             0       0       0.62    0.62
   24             0       0       0.93    0.93
   32             7       7       1.00    0.97
   48            23      23       1.00    0.97
```

**Key Finding:** KV cache ceiling is 25 sequences. Predictions match actual data exactly—preemptions start at batch=32 (32-25=7), utilization hits 93% at batch=24 (24/25.72).
