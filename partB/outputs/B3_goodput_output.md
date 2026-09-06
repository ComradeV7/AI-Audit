# B3: Goodput Derivation Output

```
Formula Test: reported_tok_s = (prompt + gen) * requests / wall_clock
prompt  batch  reported  computed   match
   512     16     883.2     883.2   ✓
   512     32    1489.6    1489.9   ✓
   512     64    2267.3    2267.4   ✓
  3584     16    1311.4    1311.5   ✓
  3584     24    1607.4    1607.4   ✓
  3584     48    1298.5    1298.5   ✓

Conclusion: reported_tok_s includes prompt tokens (NOT goodput)

Honest Goodput (batch=24, prompt=3584):
  Method (a) end-to-end: 12288 tokens / 61.16s = 200.9 tok/s
  Method (b) steady-state: 24 / 96.07ms = 249.8 tok/s
  Gap: 48.9 tok/s (ttft wait time)

REPORT_v0 Error:
  Claimed: 'batch 48 will deliver ~3200 tok/s'
  Actual reported_tok_s: 1298.5 tok/s (includes prompts)
  Honest goodput: 162.3 tok/s (generated tokens only)

Should have said:
  'batch 24 delivers 201 tok/s goodput'
  'batch 48 declines to 162 tok/s due to preemption'
```

**Key Finding:** reported_tok_s includes prompt tokens misreading it as goodput overstates user-visible throughput by 6-8×. REPORT_v0's "3200 tok/s" claim is off by 16-20×.
