import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def get_encoder():
    try:
        import tiktoken
        return tiktoken.get_encoding("gpt2").encode
    except:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained("gpt2")
        return lambda s: tok.encode(s, add_special_tokens=False)

def measure_lower_bug(filepath, encode):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    lowered_ratios = []
    original_ratios = []
    
    for line in lines:
        words = len(line.split())  # Use correct split to isolate lowercase effect
        
        tokens_lowered = len(encode(line.lower()))  # Bug: forces lowercase
        tokens_original = len(encode(line))          # Fixed: preserves case
        
        lowered_ratios.append(tokens_lowered / words)
        original_ratios.append(tokens_original / words)
    
    lowered = sum(lowered_ratios) / len(lowered_ratios)
    fixed = sum(original_ratios) / len(original_ratios)
    
    return lowered, fixed

if __name__ == "__main__":
    BASE_DIR = r"d:\Dev\Audit-Assessment\starter_kit"
    ENG = os.path.join(BASE_DIR, "corpus_sample", "eng_sample.txt")
    HIN = os.path.join(BASE_DIR, "corpus_sample", "hin_sample.txt")
    
    encode = get_encoder()
    
    eng_lowered, eng_fixed = measure_lower_bug(ENG, encode)
    hin_lowered, hin_fixed = measure_lower_bug(HIN, encode)
    
    print("LOWERCASE BUG (line.lower() vs line): \n")
    print(f"English - Lowered: {eng_lowered:.3f}  Fixed: {eng_fixed:.3f}  Delta: {eng_fixed-eng_lowered:+.3f}")
    print(f"Hindi   - Lowered: {hin_lowered:.3f}  Fixed: {hin_fixed:.3f}  Delta: {hin_fixed-hin_lowered:+.3f}")
    print(f"\nRatio - Lowered: {hin_lowered/eng_lowered:.2f}x  Fixed: {hin_fixed/eng_fixed:.2f}x  Delta: {(hin_fixed/eng_fixed)-(hin_lowered/eng_lowered):+.2f}x")
