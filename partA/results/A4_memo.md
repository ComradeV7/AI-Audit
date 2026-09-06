# Recomendation Memo

**Context:** 
Using ai4bharat tokenizer with tok/sentence as the denominator, Hindi costs **1.17× English** (31.3 vs 26.8 tokens/sentence). Tamil and Telugu cost 1.05-1.06× English.

The corrected range across all Indic languages tested is **~1.05-1.2× English**, not the 6× claimed in the original report.

---

## 1. Tokenizer Fertility

**Findings (FLORES-200, 1012 parallel sentences, ai4bharat/IndicBERTv2, tok/sentence):**

- Hindi: **1.17× English** (31.3 vs 26.8 tokens/sentence)
- Tamil: **1.05× English** (28.1 vs 26.8 tokens/sentence)  
- Telugu: **1.06× English** (28.4 vs 26.8 tokens/sentence)

**Corrected range: ~1.05-1.2× English**, not the original 5.89-6×.

**Root cause:** Swapping GPT-2 for an Indic-aware tokenizer (ai4bharat/IndicBERTv2) shrinks token counts by 84-93% for Hindi/Tamil/Telugu, while English changes by only ~0.1% (marginally worse under ai4bharat, as expected since GPT-2 is English-native). The original gap was GPT-2 never having seen Devanagari/Tamil/Telugu script during training, not a property of the languages themselves.

**Routing metric:** Use **tok/sentence** (ratio-of-totals). FLORES sentences are parallel, meaning-equivalent translations, so tok/sentence directly answers "how many tokens does it cost to serve one unit of user intent in this language." This is what GPU cost actually tracks—users send requests with intent, not arbitrary word counts or byte counts. (This isn't perfectly clean either—FLORES translators vary in literalness across languages—but that noise is unrelated to script or tokenizer effects, unlike the other three denominators, whose flaws are entangled with the very thing being measured.)

Why the other denominators fail:
- **tok/word** assumes word boundaries are comparable units of meaning across languages. They aren't—Tamil and Telugu are agglutinative, packing more meaning per word than English.
- **tok/grapheme** assumes visual character complexity maps to cost. It doesn't—GPU cost tracks tokens processed, not how characters look.
- **tok/byte** flips direction entirely depending on tokenizer quality. Under GPT-2, Hindi was 2.9× worse than English; under ai4bharat, English became 2.2× worse than Hindi. A metric that reverses itself isn't measuring anything stable about the language—it's riding on UTF-8's arbitrary 3-bytes-per-Devanagari-character allocation.

---

## 2. Recommendation

**Swap the production tokenizer** to an Indic-aware model (ai4bharat/IndicBERTv2 or google/muril-base-cased).

**Do not provision a 6× cost multiplier** for Indic traffic. The real overhead, once the tokenizer is fixed, is ~1.05-1.2×.

---

## 3. Biggest Caveat

FLORES is formal, professionally-translated Wikipedia/news register. It says nothing about casual chat, slang, or code-switched text (Hinglish/Tanglish), which is probably the dominant traffic pattern in production. This analysis establishes the correct baseline—production validation still required.

---

## 4. Metric to Monitor

**Track `median_tokens_per_request_by_language` in production**, with drift alerts. This analysis exists because nobody was watching that number when the original report shipped.
