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

def measure_split_bug(filepath, encode):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    buggy_ratios = []
    correct_ratios = []
    
    for line in lines:
        tokens = len(encode(line.lower()))
        buggy_words = len(line.split(" "))    # Bug: creates empty strings
        correct_words = len(line.split())      # Fixed
        
        buggy_ratios.append(tokens / buggy_words)
        correct_ratios.append(tokens / correct_words)
    
    buggy = sum(buggy_ratios) / len(buggy_ratios)
    fixed = sum(correct_ratios) / len(correct_ratios)
    
    return buggy, fixed

if __name__ == "__main__":
    BASE_DIR = r"d:\Dev\Audit-Assessment\starter_kit"
    ENG = os.path.join(BASE_DIR, "corpus_sample", "eng_sample.txt")
    HIN = os.path.join(BASE_DIR, "corpus_sample", "hin_sample.txt")
    
    encode = get_encoder()
    
    eng_buggy, eng_fixed = measure_split_bug(ENG, encode)
    hin_buggy, hin_fixed = measure_split_bug(HIN, encode)
    
    print("SPLIT BUG (split(' ') vs split()): \n")
    print(f"English - Buggy: {eng_buggy:.3f}  Fixed: {eng_fixed:.3f}  Delta: {eng_fixed-eng_buggy:+.3f}")
    print(f"Hindi   - Buggy: {hin_buggy:.3f}  Fixed: {hin_fixed:.3f}  Delta: {hin_fixed-hin_buggy:+.3f}")
    print(f"\nRatio - Buggy: {hin_buggy/eng_buggy:.2f}x  Fixed: {hin_fixed/eng_fixed:.2f}x  Delta: {(hin_fixed/eng_fixed)-(hin_buggy/eng_buggy):+.2f}x")
