import numpy as np
import math

def ngram_from_text(text, n):
    normalised_text = text.lower()
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer")
    if n > len(text):
        return []

    ngrams = []
    for i in range(len(normalised_text) - n + 1):
        ngram = normalised_text[i:(i+n)]
        ngrams.append(ngram)
    return ngrams

def ngram_frequencies(text, n):
    ngram_list = ngram_from_text(text,n)
    ngram_dict = {}
    for ngram in ngram_list:
        if ngram in ngram_dict:
            ngram_dict[ngram] += 1
        else:
            ngram_dict[ngram] = 1
    return ngram_dict

def cosine_similarity(counts_a, counts_b):
    all_keys = set(counts_a) | set(counts_b)
    dot = 0
    norm_a = 0
    norm_b = 0
    
    for g in all_keys:
        if g in counts_a:
            a = counts_a[g]
        else:
            a = 0

        if g in counts_b:
            b = counts_b[g]
        else:
            b = 0
        dot += a * b
        norm_a += a**2
        norm_b += b**2

    if norm_a == 0 or norm_b == 0:
            # an angle between something and a zero vector doesnt make sense
            # also, in this formula you would divide by 0, so cos is undefined (which is correct since zero vector doesnt have a direction)
            # returning 0.0 prevents the code from crashing, it is not a real angle
            return 0.0
    
    return dot / (math.sqrt(norm_a*norm_b))

