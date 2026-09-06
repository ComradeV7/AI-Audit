import pandas as pd

df = pd.read_csv(r"d:\Dev\Audit-Assessment\starter_kit\bench\bench_log.csv")

# Test formula
test_rows = [(512, 16), (512, 32), (512, 64), (3584, 16), (3584, 24), (3584, 48)]

print("Formula Test: reported_tok_s = (prompt + gen) * requests / wall_clock")
print("prompt  batch  reported  computed   match")
for p, b in test_rows:
    r = df[(df['prompt_len'] == p) & (df['batch_size'] == b)].iloc[0]
    rep = r['reported_tok_s']
    calc = (r['prompt_len'] + r['gen_len']) * r['num_requests'] / r['wall_clock_s']
    match = "✓" if abs(rep - calc) < 0.5 else "✗"
    print(f"{p:6d}  {b:5d}  {rep:8.1f}  {calc:8.1f}   {match}")

print("\nConclusion: reported_tok_s includes prompt tokens (NOT goodput)")
print()

# Honest goodput
target = df[(df['prompt_len'] == 3584) & (df['batch_size'] == 24)].iloc[0]
gen_tokens = target['gen_len'] * target['batch_size']
goodput_e2e = gen_tokens / target['wall_clock_s']
goodput_steady = target['batch_size'] / (target['itl_ms_p50'] / 1000)

print("Honest Goodput (batch=24, prompt=3584):")
print(f"  Method (a) end-to-end: {gen_tokens} tokens / {target['wall_clock_s']:.2f}s = {goodput_e2e:.1f} tok/s")
print(f"  Method (b) steady-state: {int(target['batch_size'])} / {target['itl_ms_p50']:.2f}ms = {goodput_steady:.1f} tok/s")
print(f"  Gap: {abs(goodput_e2e - goodput_steady):.1f} tok/s (ttft wait time)")
print()

batch_48 = df[(df['prompt_len'] == 3584) & (df['batch_size'] == 48)].iloc[0]
goodput_48 = (batch_48['gen_len'] * batch_48['batch_size']) / batch_48['wall_clock_s']

print("REPORT_v0 Error:")
print(f"  Claimed: 'batch 48 will deliver ~3200 tok/s'")
print(f"  Actual reported_tok_s: {batch_48['reported_tok_s']:.1f} tok/s (includes prompts)")
print(f"  Honest goodput: {goodput_48:.1f} tok/s (generated tokens only)")
print()
print("Should have said:")
print(f"  'batch 24 delivers {goodput_e2e:.0f} tok/s goodput'")
print(f"  'batch 48 declines to {goodput_48:.0f} tok/s due to preemption'")
