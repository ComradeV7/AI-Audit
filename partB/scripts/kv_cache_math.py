import pandas as pd

# Model specs
LAYERS, KV_HEADS, HEAD_DIM, BYTES_PER_ELEM = 28, 8, 128, 2
MAX_MODEL_LEN = 4096

# Hardware
TOTAL_VRAM_GB, GPU_MEMORY_UTIL = 24, 0.92
WEIGHTS_GB, NON_KV_OVERHEAD_GB = 8.4, 1.6

# Calculate
kv_bytes_per_token = 2 * LAYERS * KV_HEADS * HEAD_DIM * BYTES_PER_ELEM
bytes_per_seq = kv_bytes_per_token * MAX_MODEL_LEN
available_vram = TOTAL_VRAM_GB * GPU_MEMORY_UTIL - WEIGHTS_GB - NON_KV_OVERHEAD_GB
max_seqs = available_vram * 1e9 / bytes_per_seq
ceiling = int(max_seqs)

print("KV Cache Capacity:")
print(f"  {kv_bytes_per_token:,} bytes/token")
print(f"  {bytes_per_seq:,} bytes per {MAX_MODEL_LEN}-token seq = {bytes_per_seq/1e9:.3f} GB")
print(f"  {available_vram:.2f} GB available")
print(f"  Ceiling: {ceiling} concurrent sequences")
print()

# Validate
df = pd.read_csv(r"d:\Dev\Audit-Assessment\starter_kit\bench\bench_log.csv")
long = df[df['prompt_len'] == 3584]

print("Validation (prompt_len=3584):")
print("batch  pred_preempt  actual  pred_util  actual")
for _, r in long.iterrows():
    b = int(r['batch_size'])
    pred_p = max(0, b - ceiling)
    pred_u = min(b / max_seqs, 1.0)
    print(f"{b:5d}  {pred_p:12d}  {int(r['preempted_seqs']):6d}  {pred_u:9.2f}  {r['kv_cache_util']:6.2f}")
