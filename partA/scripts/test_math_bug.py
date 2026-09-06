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

def measure_math_bug(filepath, encode):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    ratios = []
    total_tokens = 0
    total_words = 0
    
    for line in lines:
        tokens = len(encode(line.lower()))
        words = len(line.split(" "))  # Keep split bug to isolate math
        
        ratios.append(tokens / words)
        total_tokens += tokens
        total_words += words
    
    mean_of_ratios = sum(ratios) / len(ratios)  # Bug: wrong aggregation
    ratio_of_totals = total_tokens / total_words  # Fixed: correct aggregation
    
    return mean_of_ratios, ratio_of_totals

if __name__ == "__main__":
    BASE_DIR = r"d:\Dev\Audit-Assessment\starter_kit"
    ENG = os.path.join(BASE_DIR, "corpus_sample", "eng_sample.txt")
    HIN = os.path.join(BASE_DIR, "corpus_sample", "hin_sample.txt")
    
    encode = get_encoder()
    
    eng_buggy, eng_fixed = measure_math_bug(ENG, encode)
    hin_buggy, hin_fixed = measure_math_bug(HIN, encode)
    
    print("MATH BUG (mean-of-ratios vs ratio-of-totals): \n")
    print(f"English - Buggy: {eng_buggy:.3f}  Fixed: {eng_fixed:.3f}  Delta: {eng_fixed-eng_buggy:+.3f}")
    print(f"Hindi   - Buggy: {hin_buggy:.3f}  Fixed: {hin_fixed:.3f}  Delta: {hin_fixed-hin_buggy:+.3f}")
    print(f"\nRatio - Buggy: {hin_buggy/eng_buggy:.2f}x  Fixed: {hin_fixed/eng_fixed:.2f}x  Delta: {(hin_fixed/eng_fixed)-(hin_buggy/eng_buggy):+.2f}x")