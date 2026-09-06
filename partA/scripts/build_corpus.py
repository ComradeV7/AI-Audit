import os
import unicodedata
import pandas as pd
from datasets import load_dataset

# Using the ungated flores_101 mirror
LANGS = ["eng", "hin", "tam", "tel"]

def main():
    os.makedirs("partA/corpus", exist_ok=True)
    data_records = []
    base_len = None
    
    print("Downloading FLORES-101 datasets (devtest split)...")
    
    for lang in LANGS:
        print(f"Downloading {lang}...")
        # gsarti/flores_101 is fully ungated and doesn't require trust_remote_code
        ds = load_dataset("gsarti/flores_101", lang, split="devtest", trust_remote_code=True)
        
        # Apply NFC but keep casing and punctuation
        sentences = [unicodedata.normalize("NFC", s) for s in ds['sentence']]
        
        if base_len is None: 
            base_len = len(sentences)
        
        for i, text in enumerate(sentences):
            data_records.append({"sentence_id": i, "lang": lang, "text": text})
            
    df = pd.DataFrame(data_records)
    df.to_csv("partA/corpus/eval_corpus.csv", index=False)
    
    print(f"Total Sentences per language: {base_len}")
    
    avg_chars = df.groupby("lang")["text"].apply(lambda x: x.str.len().mean()).round(2)
    print("\nAverage character length:")
    for lang, avg in avg_chars.items():
        print(f"  - {lang}: {avg} chars")
        
    print("\nSpot-check (Sentence #42):")
    for _, row in df[df["sentence_id"] == 42].iterrows():
        print(f"  - [{row['lang']}] {row['text']}")

if __name__ == "__main__":
    main()