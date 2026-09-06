import os
import sys
import unicodedata

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

def count_graphemes(text):
    """Count visual graphemes using Unicode grapheme cluster boundaries"""
    try:
        import regex
        return len(regex.findall(r'\X', text))
    except ImportError:
        # Fallback: count base characters (ignore combining marks)
        count = 0
        for char in text:
            if unicodedata.category(char)[0] != 'M':
                count += 1
        return count

def measure_grapheme_distortion(filepath, encode):
    """Measure tok/char using codepoints vs graphemes"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    total_tokens = 0
    total_codepoints = 0
    total_graphemes = 0
    
    for line in lines:
        tokens = len(encode(line.lower()))
        codepoints = len(line)
        graphemes = count_graphemes(line)
        
        total_tokens += tokens
        total_codepoints += codepoints
        total_graphemes += graphemes
    
    tok_per_codepoint = total_tokens / total_codepoints
    tok_per_grapheme = total_tokens / total_graphemes
    inflation_ratio = total_codepoints / total_graphemes
    
    return tok_per_codepoint, tok_per_grapheme, inflation_ratio

def main():
    BASE_DIR = r"d:\Dev\Audit-Assessment\starter_kit"
    ENG_FILE = os.path.join(BASE_DIR, "corpus_sample", "eng_sample.txt")
    HIN_FILE = os.path.join(BASE_DIR, "corpus_sample", "hin_sample.txt")
    
    encode = get_encoder()
    
    print("GRAPHEME CLUSTER TEST (tok/char metric)")
    
    # Example demonstration
    examples = [("किताबें", "Hindi"), ("Hello", "English")]
    print("\nExample: Codepoints vs Graphemes")
    for text, lang in examples:
        cp = len(text)
        gr = count_graphemes(text)
        print(f"'{text}' ({lang}): {cp} codepoints, {gr} graphemes")

    print("Corpus Analysis:")
    
    eng_cp, eng_gr, eng_ratio = measure_grapheme_distortion(ENG_FILE, encode)
    hin_cp, hin_gr, hin_ratio = measure_grapheme_distortion(HIN_FILE, encode)
    
    print(f"\nEnglish - tok/codepoint: {eng_cp:.3f}  tok/grapheme: {eng_gr:.3f}  Inflation: {eng_ratio:.2f}x")
    print(f"Hindi   - tok/codepoint: {hin_cp:.3f}  tok/grapheme: {hin_gr:.3f}  Inflation: {hin_ratio:.2f}x")
    
    print(f"\nDistortion Analysis:")
    print(f"English distortion: {eng_cp - eng_gr:+.3f} (codepoint-based is {'inflated' if eng_cp > eng_gr else 'deflated'})")
    print(f"Hindi distortion:   {hin_cp - hin_gr:+.3f} (codepoint-based is {'inflated' if hin_cp > hin_gr else 'deflated'})")

if __name__ == "__main__":
    main()
