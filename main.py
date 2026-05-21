#!/usr/bin/env python3
"""
Spell Checker Demo
==================
Demonstrates the 3-stage pipeline:
  [A] Hash-based Dictionary Lookup
  [B] Edit Distance Candidate Generation
  [C] Heap-based Top-K Ranking
"""

import os
from spell_checker import SpellChecker


def print_separator(char='─', width=70):
    print(char * width)


def print_stage(label, data, indent=2):
    prefix = ' ' * indent
    print(f"{prefix}📌 {label}")
    if isinstance(data, dict):
        for k, v in data.items():
            print(f"{prefix}   {k}: {v}")
    else:
        print(f"{prefix}   {data}")
    print()


def demo_single_word(checker, word):
    """Run full pipeline on a single word with detailed output."""
    print_separator('═')
    print(f"  INPUT: \"{word}\"")
    print_separator('═')

    result = checker.check(word, top_k=5, max_distance=2)

    # Stage A
    stage_a = result['stages']['A_lookup']
    print(f"\n  ┌─ STAGE A: Dictionary Lookup ─────────────────────")
    print(f"  │  Word \"{word}\" in dictionary? → {stage_a['found']}")
    print(f"  └────────────────────────────────────────────────────────────────")

    if result['is_correct']:
        print(f"\n  ✅ \"{word}\" is spelled correctly. No correction needed.\n")
        return

    # Stage B
    stage_b = result['stages']['B_candidates']
    print(f"\n  ┌─ STAGE B: Candidate Generation ────────────")
    print(f"  │  Max edit distance: 2")
    print(f"  │  Candidates found: {stage_b['num_candidates']}")
    print(f"  │  Sample candidates:")
    for cand, dist in stage_b['sample'][:7]:
        print(f"  │    • \"{cand}\" (distance={dist})")
    print(f"  └────────────────────────────────────────────────────────────────")

    # Stage C
    if 'C_ranking' in result['stages']:
        stage_c = result['stages']['C_ranking']
        print(f"\n  ┌─ STAGE C: Ranking (Min-Heap Top-K Selection) ──────────────")
        print(f"  │  Ranking by: (1) edit distance ↑, (2) frequency ↓")
        print(f"  │")
        print(f"  │  {'Rank':<6}{'Word':<20}{'Distance':<12}{'Frequency'}")
        print(f"  │  {'────':<6}{'────────────':<20}{'────────':<12}{'─────────'}")
        for i, (word_r, dist, freq) in enumerate(stage_c['ranked_results'], 1):
            print(f"  │  {i:<6}\"{word_r}\"{'':<{17-len(word_r)}}{dist:<12}{freq}")
        print(f"  └────────────────────────────────────────────────────────────────")

    # Final output
    if result['suggestions']:
        best = result['suggestions'][0][0]
        print(f"\n  🎯 OUTPUT: \"{best}\"\n")
    else:
        print(f"\n  ❌ No suggestions found.\n")


def main():
    # Resolve dictionary path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dict_path = os.path.join(script_dir, 'dictionary.txt')

    print("\n" + "=" * 70)
    print("         SPELL CHECKER — 3-Stage Algorithm Pipeline")
    print("=" * 70)
    print(f"\n  Loading dictionary from: {dict_path}")

    checker = SpellChecker(dict_path)
    print(f"  Dictionary size: {checker.dictionary.size()} words")
    print(f"  Pipeline: [Hash Lookup] → [Edit Distance] → [Heap Ranking]")
    print()

    # Test cases demonstrating the pipeline
    test_words = [
        "recieve",      # → receive (common ie/ei confusion)
        "definately",   # → definitely
        "occured",      # → occurred
        "seperate",     # → separate
        "accomodate",   # → accommodate
        "wierd",        # → weird
        "neccessary",   # → necessary
        "reccomend",    # → recommend
        "receive",      # correctly spelled — should pass Stage A
        "teh",          # → the (transposition)
    ]

    for word in test_words:
        demo_single_word(checker, word)

    print_separator('═')
    print("  INTERACTIVE MODE — Type a word to check (or 'quit' to exit)")
    print_separator('═')
    print()

    while True:
        try:
            user_input = input("  Check word → ").strip()
            if user_input.lower() in ('quit', 'exit', 'q'):
                print("\n  Goodbye!\n")
                break
            if user_input:
                demo_single_word(checker, user_input)
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!\n")
            break


if __name__ == '__main__':
    main()
