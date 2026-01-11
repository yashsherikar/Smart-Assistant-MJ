import os
import pickle
from difflib import get_close_matches

CACHE = ".search_index.pkl"

def build_index(root='.', cache_path=CACHE):
    index = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            key = name.lower()
            index.setdefault(key, []).append(os.path.join(dirpath, name))
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(index, f)
    except Exception:
        pass
    return index

def load_index(cache_path=CACHE):
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return build_index()
    return build_index()

def search_index(query, index=None, max_results=10):
    q = (query or '').lower()
    if index is None:
        index = load_index()
    # exact substring matches first
    results = []
    for name, paths in index.items():
        if q in name:
            results.extend(paths)
            if len(results) >= max_results:
                return results[:max_results]

    # fuzzy fallback using difflib on keys
    keys = list(index.keys())
    close = get_close_matches(q, keys, n=max_results, cutoff=0.6)
    for k in close:
        results.extend(index.get(k, []))
        if len(results) >= max_results:
            break
    return results[:max_results]
