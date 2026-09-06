import os
import unicodedata
import regex
import numpy as np
import pandas as pd
from transformers import AutoTokenizer
import tiktoken
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def count_graphemes(text):
    return len(regex.findall(r'\X', text))

def ratio_of_totals(df, denom_col):
    return df["tokens"].sum() / df[denom_col].sum()

def bootstrap_ratio_ci(df, denom_col, n_iterations=1000, seed=1337):
    """Correct bootstrap for a ratio-of-sums: resample ROWS, recompute the
    ratio from raw sums each time -- not a bootstrap of precomputed ratios."""
    rng = np.random.default_rng(seed)
    n = len(df)
    stats = []
    tok = df["tokens"].values
    den = df[denom_col].values
    for _ in range(n_iterations):
        idx = rng.integers(0, n, size=n)
        stats.append(tok[idx].sum() / den[idx].sum())
    return np.percentile(stats, 2.5), np.percentile(stats, 97.5)

if __name__ == "__main__":
    # Load corpus from CSV
    CORPUS_PATH = r"d:\Dev\Audit-Assessment\partA\corpus\eval_corpus.csv"
    print(f"Loading corpus from {CORPUS_PATH}...")
    corpus_df = pd.read_csv(CORPUS_PATH)
    
    # Group by language
    LANGUAGES = corpus_df['lang'].unique()
    print(f"Found languages: {', '.join(LANGUAGES)}")

    print("\nLoading tokenizers...")
    gpt2_encode = tiktoken.get_encoding("gpt2").encode
    muril_tok = AutoTokenizer.from_pretrained("google/muril-base-cased")
    indic_tok = AutoTokenizer.from_pretrained("ai4bharat/IndicBERTv2-MLM-only", use_fast=False)

    tokenizers = {
        "gpt2": gpt2_encode,
        "muril": lambda s: muril_tok.encode(s, add_special_tokens=False),
        "ai4bharat": lambda s: indic_tok.encode(s, add_special_tokens=False),
    }

    grid_rows, raw_rows = [], []
    for tok_name, encode_fn in tokenizers.items():
        for lang in LANGUAGES:
            print(f"Processing {lang} with {tok_name}...")
            lang_texts = corpus_df[corpus_df['lang'] == lang]['text'].tolist()
            
            # Process lines directly (already NFC normalized)
            records = []
            for line in lang_texts:
                line = unicodedata.normalize("NFC", str(line).strip())
                tokens = len(encode_fn(line))
                words = len(line.split())
                graphemes = count_graphemes(line)
                byte_len = len(line.encode('utf-8'))
                records.append({
                    "tokens": tokens, "words": words,
                    "graphemes": graphemes, "bytes": byte_len,
                })
            
            df = pd.DataFrame(records)
            
            # Calculate metrics
            results = {}
            for name, col in [("tok_per_word", "words"), ("tok_per_graph", "graphemes"),
                               ("tok_per_byte", "bytes")]:
                mean_of_ratios = (df["tokens"] / df[col]).mean()
                rot = ratio_of_totals(df, col)
                ci_lo, ci_hi = bootstrap_ratio_ci(df, col)
                results[name] = {"mean_of_ratios": mean_of_ratios, "ratio_of_totals": rot,
                                  "ci_low": ci_lo, "ci_high": ci_hi}

            sent_mean = df["tokens"].mean()
            sent_ci = bootstrap_ratio_ci(df.assign(_ones=1), "_ones")
            results["tok_per_sent"] = {"mean_of_ratios": sent_mean, "ratio_of_totals": sent_mean,
                                        "ci_low": sent_ci[0], "ci_high": sent_ci[1]}
            
            df["tokenizer"], df["language"] = tok_name, lang
            raw_rows.append(df)
            for metric, stats in results.items():
                grid_rows.append({"Tokenizer": tok_name, "Language": lang, "Metric": metric, **stats})

    out_dir = r"d:\Dev\Audit-Assessment\partA\results"
    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame(grid_rows).to_csv(os.path.join(out_dir, "fertility_grid.csv"), index=False)
    pd.concat(raw_rows).to_csv(os.path.join(out_dir, "raw_counts.csv"), index=False)
    print(f"\n[OK] Saved to {out_dir}")
    print("  - fertility_grid.csv (aggregates with CIs)")
    print("  - raw_counts.csv (per-sentence, for re-derivation)")