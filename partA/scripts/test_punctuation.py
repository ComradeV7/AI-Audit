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

def measure_punctuation_effect(filepath, encode):
    """Measure fertility with/without punctuation"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    punct_chars = set('.,!?;:\'"()-')
    
    # Count punctuation density
    text = ' '.join(lines)
    punct_count = sum(1 for c in text if c in punct_chars)
    word_count = len(text.split())
    punct_density = punct_count / word_count if word_count > 0 else 0
    
    # Measure fertility with/without punctuation
    total_tokens_with = 0
    total_tokens_without = 0
    total_words = 0
    
    for line in lines:
        tokens_with = len(encode(line.lower()))
        
        line_no_punct = ''.join(c if c not in punct_chars else ' ' for c in line)
        line_no_punct = ' '.join(line_no_punct.split())
        tokens_without = len(encode(line_no_punct.lower()))
        
        words = len(line.split())
        
        total_tokens_with += tokens_with
        total_tokens_without += tokens_without
        total_words += words
    
    with_punct = total_tokens_with / total_words
    without_punct = total_tokens_without / total_words
    
    return punct_density, with_punct, without_punct

def main():
    BASE_DIR = r"d:\Dev\Audit-Assessment\starter_kit"
    ENG_FILE = os.path.join(BASE_DIR, "corpus_sample", "eng_sample.txt")
    HIN_FILE = os.path.join(BASE_DIR, "corpus_sample", "hin_sample.txt")
    
    encode = get_encoder()
    
    print("PUNCTUATION HANDLING TEST:")
    
    eng_density, eng_with, eng_without = measure_punctuation_effect(ENG_FILE, encode)
    hin_density, hin_with, hin_without = measure_punctuation_effect(HIN_FILE, encode)
    
    print(f"\nPunctuation Density:")
    print(f"English: {eng_density:.3f} marks/word")
    print(f"Hindi:   {hin_density:.3f} marks/word")
    print(f"Ratio:   {eng_density/hin_density:.1f}x difference")
    
    print(f"\nFertility Analysis:")
    print(f"English - With: {eng_with:.3f}  Without: {eng_without:.3f}  Delta: {eng_without-eng_with:+.3f}")
    print(f"Hindi   - With: {hin_with:.3f}  Without: {hin_without:.3f}  Delta: {hin_without-hin_with:+.3f}")
    
    print(f"\nPunctuation Contribution:")
    print(f"English adds: {eng_with - eng_without:.3f} tok/word from punctuation")
    print(f"Hindi adds:   {hin_with - hin_without:.3f} tok/word from punctuation")

if __name__ == "__main__":
    main()
