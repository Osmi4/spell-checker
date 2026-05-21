# spell-checker
An application that detects misspelled words and suggests the most likely corrections. The system first checks whether a word exists in a dictionary using a hash-based lookup. If the word is not found, it generates candidate corrections using an edit distance algorithm and then ranks the best suggestions using a heap-based top-k selection.
