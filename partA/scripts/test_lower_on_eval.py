import csv
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

def load_corpus(csv_path):
    """Load eval corpus grouped by language"""
    corpus = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lang = row['lang']
            text = row['text']
            if lang not in corpus:
                corpus[lang] = []
            corpus[lang].append(text)
    return corpus

def measure_lowercase_effect(texts, encode, method='mean_of_ratios'):
    """
    Measure fertility with and without lowercasing
    
    Isolation: Change ONLY case handling
    - Uses correct split() to isolate lowercase effect
    - Can use either mean-of-ratios (intern) or ratio-of-totals (correct)
    """
    
    if method == 'mean_of_ratios':
        # Intern's method
        lowered_ratios = []
        original_ratios = []
        
        for text in texts:
            words = len(text.split())
            tokens_lowered = len(encode(text.lower()))
            tokens_original = len(encode(text))
            
            lowered_ratios.append(tokens_lowered / words)
            original_ratios.append(tokens_original / words)
        
        lowered = sum(lowered_ratios) / len(lowered_ratios)
        original = sum(original_ratios) / len(original_ratios)
        
    else:  # ratio_of_totals
        # Correct method
        total_tokens_lowered = 0
        total_tokens_original = 0
        total_words = 0
        
        for text in texts:
            words = len(text.split())
            tokens_lowered = len(encode(text.lower()))
            tokens_original = len(encode(text))
            
            total_tokens_lowered += tokens_lowered
            total_tokens_original += tokens_original
            total_words += words
        
        lowered = total_tokens_lowered / total_words
        original = total_tokens_original / total_words
    
    return lowered, original

def main():
    CORPUS_PATH = r"d:\Dev\Audit-Assessment\partA\corpus\eval_corpus.csv"
    
    if not os.path.exists(CORPUS_PATH):
        print(f"ERROR: Corpus not found at {CORPUS_PATH}")
        return
    
    print("Loading evaluation corpus...")
    try:
        corpus = load_corpus(CORPUS_PATH)
    except Exception as e:
        print(f"ERROR loading corpus: {e}")
        return
    
    print(f"Loaded: {', '.join(f'{lang}={len(texts)}' for lang, texts in corpus.items())}\n")
    
    print("Initializing tokenizer...")
    try:
        encode = get_encoder()
    except Exception as e:
        print(f"ERROR: Could not load tokenizer: {e}")
        return
    
    print("Tokenizer ready. Processing...\n")
    
    # Test both aggregation methods
    for method_name, method in [("Intern's Method (mean-of-ratios)", 'mean_of_ratios'),
                                 ("Correct Method (ratio-of-totals)", 'ratio_of_totals')]:
        
        print(f"LOWERCASE BUG - {method_name}:")
        
        results = {}
        for lang in ['eng', 'hin', 'tam', 'tel']:
            if lang in corpus:
                lowered, original = measure_lowercase_effect(corpus[lang], encode, method)
                results[lang] = (lowered, original)
                delta = original - lowered
                print(f"{lang:3s} - Lowered: {lowered:.3f}  Original: {original:.3f}  Delta: {delta:+.3f}")
        
        # Compare ratios
        if 'eng' in results and 'hin' in results:
            ratio_lowered = results['hin'][0] / results['eng'][0]
            ratio_original = results['hin'][1] / results['eng'][1]
            ratio_delta = ratio_original - ratio_lowered
            
            print(f"\nHindi/English Ratio:")
            print(f"  Lowered:  {ratio_lowered:.2f}x")
            print(f"  Original: {ratio_original:.2f}x")
            print(f"  Delta:    {ratio_delta:+.2f}x")
        
        print()

if __name__ == "__main__":
    main()
