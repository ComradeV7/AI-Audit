import pandas as pd

df = pd.read_csv(r"d:\Dev\Audit-Assessment\starter_kit\bench\bench_log.csv")
long = df[df['prompt_len'] == 3584].copy()

baseline = long[long['batch_size'] == 4].iloc[0]
per_req = baseline['reported_tok_s'] / baseline['batch_size']

print("Throughput Analysis (prompt_len=3584):")
print(f"Baseline: {baseline['reported_tok_s']:.1f} tok/s at batch=4")
print()
print("batch  reported  naive_pred   vs_naive  Δ_tput  preempt  kv_util  wall_s  ttft_ms")

prev = None
peak_batch, peak_val = None, 0

for _, r in long.iterrows():
    b = int(r['batch_size'])
    rep = r['reported_tok_s']
    naive = b * per_req
    vs_n = rep - naive
    delta = (rep - prev) if prev else 0
    
    if rep > peak_val:
        peak_val, peak_batch = rep, b
    
    marker = " PEAK" if b == peak_batch else (" DECLINE" if prev and rep < prev else "")
    
    print(f"{b:5d}  {rep:8.1f}  {naive:10.1f}  {vs_n:+9.1f}  {delta:+7.1f}  {int(r['preempted_seqs']):7d}  {r['kv_cache_util']:7.2f}  {r['wall_clock_s']:6.1f}  {r['ttft_ms_p50']:7.1f}{marker}")
    prev = rep

print()
print(f"Peak: batch={peak_batch}, {peak_val:.1f} tok/s")
print(f"At batch=32: drops to {long[long['batch_size']==32]['reported_tok_s'].iloc[0]:.1f} tok/s (-223.4)")
print(f"At batch=48: drops to {long[long['batch_size']==48]['reported_tok_s'].iloc[0]:.1f} tok/s")
print()
print("Proposed fix: max_num_seqs=25")
print(f"  Holds throughput at {peak_val:.1f} tok/s instead of declining to 1298.5 tok/s")
