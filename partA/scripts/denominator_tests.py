from pathlib import Path
import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
grid = pd.read_csv(RESULTS_DIR / "fertility_grid.csv")

piv = grid.pivot_table(index=["Metric","Language"], columns="Tokenizer", values="ratio_of_totals")

piv["gpt2_to_ai4bharat_shrink"] = 1 - (piv["ai4bharat"] / piv["gpt2"])

print(piv.sort_values("gpt2_to_ai4bharat_shrink", ascending=False))

fair = grid[grid.Tokenizer == "ai4bharat"]

eng = fair[fair.Language == "eng"].set_index("Metric")["ratio_of_totals"]

ratio_rows = {}

for lang in ["hin", "tam", "tel"]:

    row = fair[fair.Language == lang].set_index("Metric")["ratio_of_totals"]

    ratio_rows[lang] = (row / eng).round(3)

    print(lang, ratio_rows[lang].to_dict())

ratio_df = pd.DataFrame(ratio_rows)

for metric in ratio_df.index:

    print(f"  {metric}: worst={ratio_df.loc[metric].idxmax()} ({ratio_df.loc[metric].max()})")
