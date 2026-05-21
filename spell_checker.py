"""
Spell Checker System
====================
A 3-stage pipeline that detects misspelled words and suggests corrections:
  Stage A: Hash-based dictionary lookup (O(1) membership test)
  Stage B: Edit distance candidate generation (Levenshtein distance)
  Stage C: Heap-based top-k ranking (min-heap by edit distance, max-heap by frequency)
"""

import heapq
from collections import Counter


# STAGE A: Dictionary Preprocessing (Hash Set)

class Dictionary:
    """
    Stores valid words in a hash set for O(1) average-case lookup.
    Also maintains word frequency counts for ranking candidates.
    """

    def __init__(self, filepath: str):
        self.words: set[str] = set()
        self.frequency: Counter = Counter()
        self._load(filepath)

    def _load(self, filepath: str):
        """Load words from file into hash set and count frequencies."""
        with open(filepath, 'r') as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    self.words.add(word)
                    self.frequency[word] += 1

    def contains(self, word: str) -> bool:
        """O(1) average-case lookup using hash set."""
        return word.lower() in self.words

    def size(self) -> int:
        return len(self.words)


# STAGE B: Candidate Generation (Edit Distance - Levenshtein)

class CandidateGenerator:
    """
    Generates correction candidates using two strategies:
    1. Generate all strings within edit distance 1 or 2 from the input
    2. Compute Levenshtein distance between input and dictionary words

    Edit operations: insert, delete, replace, transpose
    """

    ALPHABET = 'abcdefghijklmnopqrstuvwxyz'

    def __init__(self, dictionary: Dictionary):
        self.dictionary = dictionary

    @staticmethod
    def levenshtein_distance(s: str, t: str) -> int:
        """
        Compute the Levenshtein (edit) distance between two strings.
        Uses dynamic programming with O(min(m,n)) space optimization.

        Time:  O(m * n)
        Space: O(min(m, n))
        """
        if len(s) < len(t):
            return CandidateGenerator.levenshtein_distance(t, s)

        # s is the longer string
        m, n = len(s), len(t)

        # Only keep two rows at a time
        prev = list(range(n + 1))
        curr = [0] * (n + 1)

        for i in range(1, m + 1):
            curr[0] = i
            for j in range(1, n + 1):
                if s[i - 1] == t[j - 1]:
                    curr[j] = prev[j - 1]  # no operation needed
                else:
                    curr[j] = 1 + min(
                        prev[j],      # deletion
                        curr[j - 1],  # insertion
                        prev[j - 1]   # substitution
                    )
            prev, curr = curr, prev

        return prev[n]

    def _edits_at_distance_1(self, word: str) -> set[str]:
        """
        Generate all strings that are exactly 1 edit operation away.
        Operations: delete, transpose, replace, insert
        """
        word = word.lower()
        splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]

        # Delete one character
        deletes = [L + R[1:] for L, R in splits if R]

        # Transpose two adjacent characters
        transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]

        # Replace one character with every letter
        replaces = [L + c + R[1:] for L, R in splits if R for c in self.ALPHABET]

        # Insert one character at every position
        inserts = [L + c + R for L, R in splits for c in self.ALPHABET]

        return set(deletes + transposes + replaces + inserts)

    def _edits_at_distance_2(self, word: str) -> set[str]:
        """Generate all strings within edit distance 2 (edits of edits)."""
        return {e2 for e1 in self._edits_at_distance_1(word)
                for e2 in self._edits_at_distance_1(e1)}

    def generate_candidates(self, word: str, max_distance: int = 2) -> list[tuple[str, int]]:
        """
        Generate candidate corrections with their edit distances.

        Strategy:
        1. First check edits at distance 1 that exist in dictionary
        2. If not enough, check edits at distance 2
        3. For remaining dictionary words, compute exact edit distance

        Returns: list of (candidate_word, edit_distance) tuples
        """
        word = word.lower()
        candidates = []
        seen = set()

        # Distance-1 candidates (fast generation)
        edits1 = self._edits_at_distance_1(word)
        for candidate in edits1:
            if candidate in self.dictionary.words and candidate not in seen:
                candidates.append((candidate, 1))
                seen.add(candidate)

        # Distance-2 candidates if we need more
        if max_distance >= 2:
            edits2 = self._edits_at_distance_2(word)
            for candidate in edits2:
                if candidate in self.dictionary.words and candidate not in seen:
                    candidates.append((candidate, 2))
                    seen.add(candidate)

        # For short dictionary, also brute-force check nearby words
        if len(candidates) < 5 and self.dictionary.size() <= 1000:
            for dict_word in self.dictionary.words:
                if dict_word not in seen:
                    dist = self.levenshtein_distance(word, dict_word)
                    if dist <= max_distance:
                        candidates.append((dict_word, dist))
                        seen.add(dict_word)

        return candidates


# STAGE C: Ranking (Heap-based Top-K Selection)

class CandidateRanker:
    """
    Ranks candidates using a min-heap to efficiently select the top-k results.
    Ranking criteria (priority order):
    1. Smallest edit distance (primary)
    2. Highest word frequency (secondary)

    Uses a heap of size k for O(n log k) selection from n candidates.
    """

    def __init__(self, dictionary: Dictionary):
        self.dictionary = dictionary

    def rank_candidates(self, candidates: list[tuple[str, int]], k: int = 5) -> list[tuple[str, int, int]]:
        """
        Select top-k candidates using a heap.

        Each candidate is scored as: (edit_distance, -frequency, word)
        Lower score = better candidate.

        We use Python's heapq (min-heap) with nsmallest for top-k selection.

        Args:
            candidates: list of (word, edit_distance)
            k: number of top results to return

        Returns:
            list of (word, edit_distance, frequency) sorted best-first

        Time:  O(n log k) where n = number of candidates
        Space: O(k)
        """
        if not candidates:
            return []

        # Build heap entries: (edit_distance, -frequency, word)
        # Negative frequency so that higher frequency sorts first (min-heap)
        heap_entries = []
        for word, distance in candidates:
            freq = self.dictionary.frequency.get(word, 1)
            heap_entries.append((distance, -freq, word))

        # Use heapq.nsmallest for efficient top-k selection
        # This is O(n log k) which is better than full sort O(n log n) when k << n
        top_k = heapq.nsmallest(k, heap_entries)

        # Format results: (word, edit_distance, frequency)
        results = [(word, dist, -neg_freq) for dist, neg_freq, word in top_k]
        return results


# =============================================================================
# PIPELINE: Spell Checker (chains A -> B -> C)
# =============================================================================

class SpellChecker:
    """
    Complete spell-checking pipeline:
      Input word -> [A] Hash Lookup -> [B] Edit Distance -> [C] Heap Ranking -> Output
    """

    def __init__(self, dictionary_path: str):
        self.dictionary = Dictionary(dictionary_path)
        self.generator = CandidateGenerator(self.dictionary)
        self.ranker = CandidateRanker(self.dictionary)

    def check(self, word: str, top_k: int = 5, max_distance: int = 2) -> dict:
        """
        Run the full spell-check pipeline.

        Returns a dict with:
          - word: the input word
          - is_correct: whether the word is in the dictionary
          - suggestions: top-k ranked suggestions (if misspelled)
          - stages: data flow through each pipeline stage
        """
        word = word.lower().strip()
        result = {
            'word': word,
            'is_correct': False,
            'suggestions': [],
            'stages': {}
        }

        # Stage A
        result['stages']['A_lookup'] = {
            'description': 'Hash set membership test O(1)',
            'found': self.dictionary.contains(word)
        }

        if self.dictionary.contains(word):
            result['is_correct'] = True
            return result

        # Stage B
        candidates = self.generator.generate_candidates(word, max_distance)
        result['stages']['B_candidates'] = {
            'description': f'Edit distance candidates (max_dist={max_distance})',
            'num_candidates': len(candidates),
            'sample': candidates[:10]  # show first 10 for visibility
        }

        if not candidates:
            return result

        # Stage C
        ranked = self.ranker.rank_candidates(candidates, k=top_k)
        result['stages']['C_ranking'] = {
            'description': f'Heap-based top-{top_k} selection',
            'ranked_results': ranked
        }

        result['suggestions'] = ranked
        return result

    def suggest(self, word: str, top_k: int = 1) -> str | None:
        """Simple interface: return the best suggestion or None."""
        result = self.check(word, top_k=top_k)
        if result['is_correct']:
            return word
        if result['suggestions']:
            return result['suggestions'][0][0]
        return None
