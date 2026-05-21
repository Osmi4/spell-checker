# Spell Checker — 3-Stage Algorithm Pipeline

A system that detects misspelled words and suggests the most likely corrections by chaining together three distinct algorithms. The system demonstrates how data is transformed from one stage to the next.

## Problem Statement

Given a misspelled word, suggest the most likely correct word.

```
Input:  "recieve"
Output: "receive"
```

## Pipeline Architecture

```
┌──────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│  STAGE A     │     │  STAGE B            │     │  STAGE C         │
│  Hash-based  │────▶│  Edit Distance      │────▶│  Heap-based      │
│  Dictionary  │     │  Candidate          │     │  Top-K Ranking   │
│  Lookup      │     │  Generation         │     │                  │
│  O(1)        │     │  O(m×n) per pair    │     │  O(n log k)      │
└──────────────┘     └─────────────────────┘     └──────────────────┘
     │                        │                          │
     ▼                        ▼                          ▼
 "Is the word          "What words are              "Which candidates
  in the dictionary?"   similar to it?"              are the best?"
```

## Algorithm Details

### Stage A: Dictionary Preprocessing (Hash Set)

- **Data Structure:** Python `set` (hash table)
- **Time Complexity:** O(1) average lookup
- **Purpose:** Quickly determine if a word is correctly spelled
- **Justification:** Hash sets provide constant-time membership testing, making this the fastest possible first-pass filter. If the word exists, we skip all further computation.

### Stage B: Candidate Generation (Levenshtein Edit Distance)

- **Algorithm:** Dynamic Programming (space-optimized to O(min(m,n)))
- **Time Complexity:** O(m × n) per word pair
- **Strategy:**
  1. Generate all strings within edit distance 1 (deletions, transpositions, replacements, insertions)
  2. Generate edit distance 2 candidates (edits of edits)
  3. Filter: only keep candidates that exist in the dictionary
- **Justification:** Edit distance captures the most common types of spelling errors (typos, phonetic confusion, letter doubling). Generating candidates at distance 1 first ensures we find close matches quickly.

### Stage C: Ranking (Min-Heap Top-K Selection)

- **Data Structure:** Binary min-heap (`heapq.nsmallest`)
- **Time Complexity:** O(n log k) where n = candidates, k = results
- **Ranking Criteria:**
  1. **Primary:** Smallest edit distance (closer = better)
  2. **Secondary:** Highest word frequency (more common = more likely)
- **Justification:** A heap-based top-k selection is more efficient than sorting all candidates when we only need the best few results (O(n log k) vs O(n log n)).

## Data Flow Example

```
Input: "recieve"

Stage A: Hash lookup → NOT FOUND (proceed to Stage B)

Stage B: Generate candidates:
  Distance 1: "receive" (transpose i↔e)
  Distance 2: "believe" (substitute+insert)

Stage C: Heap ranking:
  Rank 1: "receive"  (dist=1, freq=2) ← BEST
  Rank 2: "believe"  (dist=2, freq=1)

Output: "receive"
```

## Project Structure

```
spell-checker/
├── spell_checker.py   # Core implementation (all 3 stages)
├── main.py            # Demo with detailed pipeline visualization
├── dictionary.txt     # Word list (554 common + frequently misspelled words)
└── README.md          # This file
```

## Usage

```bash
python3 main.py
```

The demo runs 10 test words through the pipeline with full stage-by-stage output, then enters interactive mode where you can type any word to check.

### Programmatic Usage

```python
from spell_checker import SpellChecker

checker = SpellChecker('dictionary.txt')

# Simple: get best suggestion
print(checker.suggest("recieve"))  # → "receive"

# Detailed: see full pipeline data
result = checker.check("wierd", top_k=5)
print(result['suggestions'])
# [('weird', 1, 2), ('bird', 2, 1), ('field', 2, 1), ...]
```

## Architectural Justification

| Decision | Alternatives Considered | Why This Choice |
|----------|------------------------|-----------------|
| Hash set for dictionary | Trie, sorted array + binary search | O(1) vs O(L) vs O(log n); hash set is simplest for membership testing |
| Levenshtein DP | BK-trees, phonetic matching (Soundex) | Levenshtein handles all error types; DP is well-understood and optimal |
| Heap for top-k | Full sort, quickselect | O(n log k) is optimal for streaming/large candidate sets |
| Generate-then-filter | Compute distance to all dictionary words | Generating edits + filtering is faster for large dictionaries |

## Complexity Summary

| Stage | Time | Space |
|-------|------|-------|
| A: Dictionary Lookup | O(1) average | O(W) for W words |
| B: Edit Distance | O(26^d × L) generation + O(m×n) verification | O(min(m,n)) per DP call |
| C: Top-K Ranking | O(n log k) | O(k) |
