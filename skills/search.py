import os
from difflib import get_close_matches
try:
    from skills.search_index import search_index, load_index
    _INDEX = load_index()
except Exception:
    _INDEX = None


def search_files(root, query, max_results=10):
    """Search for filenames under `root` matching `query`.

    Uses cached index when available for faster results.
    """
    q = (query or "").strip()
    if not q:
        return []
    if _INDEX is not None:
        return search_index(q, index=_INDEX, max_results=max_results)

    # fallback to walking filesystem
    matches = []
    ql = q.lower()
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            lname = name.lower()
            if ql in lname or ql.replace(' ', '') in lname:
                matches.append(os.path.join(dirpath, name))
            else:
                close = get_close_matches(ql, [lname], n=1, cutoff=0.8)
                if close:
                    matches.append(os.path.join(dirpath, name))
        if len(matches) >= max_results:
            break
    return matches[:max_results]
