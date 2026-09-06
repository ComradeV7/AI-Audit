import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_whitespace_types(filepath):
    """Check for non-standard whitespace characters"""
    with open(filepath, 'rb') as f:
        raw_bytes = f.read()
    
    counts = {
        'regular': sum(1 for b in raw_bytes if b == 0x20),
        'nbsp': sum(1 for b in raw_bytes if b == 0xA0),
        'tab': sum(1 for b in raw_bytes if b == 0x09)
    }
    return counts

def main():
    BASE_DIR = r"d:\Dev\Audit-Assessment\starter_kit"
    ENG_FILE = os.path.join(BASE_DIR, "corpus_sample", "eng_sample.txt")
    HIN_FILE = os.path.join(BASE_DIR, "corpus_sample", "hin_sample.txt")
    
    print("UNICODE NORMALIZATION TEST")
    
    print("\nWhitespace Character Analysis:")
    
    eng_ws = check_whitespace_types(ENG_FILE)
    hin_ws = check_whitespace_types(HIN_FILE)
    
    print(f"\nEnglish - Regular: {eng_ws['regular']}  NBSP: {eng_ws['nbsp']}  Tab: {eng_ws['tab']}")
    print(f"Hindi   - Regular: {hin_ws['regular']}  NBSP: {hin_ws['nbsp']}  Tab: {hin_ws['tab']}")
    
    print(f"\nNon-standard Whitespace Found:")
    if eng_ws['nbsp'] > 0 or eng_ws['tab'] > 0:
        print(f"English: {eng_ws['nbsp']} NBSP, {eng_ws['tab']} tabs")
    else:
        print(f"English: None (all standard)")
        
    if hin_ws['nbsp'] > 0 or hin_ws['tab'] > 0:
        print(f"Hindi:   {hin_ws['nbsp']} NBSP, {hin_ws['tab']} tabs")
    else:
        print(f"Hindi:   None (all standard)")

if __name__ == "__main__":
    main()
