import numpy as np
import re
import string
from sklearn.cluster import KMeans
from nltk.corpus import stopwords

# Precompute for speed (vectorized lookups)
STOPWORDS = set(stopwords.words("english"))

def cluster_font_sizes(spans):
    font_sizes = np.array([span["size"] for span in spans]).reshape(-1, 1)
    unique_sz = np.unique(font_sizes)
    k = min(3, len(unique_sz))
    if k < 1:
        return {}, None
    if len(unique_sz) == 1:
        return {0: "H1"}, None
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = kmeans.fit_predict(font_sizes)
    clusters_sorted = np.argsort(kmeans.cluster_centers_.reshape(-1))[::-1]
    size_to_level = {cluster: f"H{i+1}" for i, cluster in enumerate(clusters_sorted)}
    for i, span in enumerate(spans):
        span["cluster"] = labels[i]
    return size_to_level, kmeans

def batch_stopword_ratio(text_list):
    ratios = []
    for text in text_list:
        tokens = [t.lower().strip(string.punctuation) for t in text.split()]
        if not tokens:
            ratios.append(0.0)
            continue
        sw_hits = sum(1 for t in tokens if t in STOPWORDS)
        ratios.append(sw_hits / len(tokens))
    return np.array(ratios)

def classify_headings(spans, size_to_level, min_score=3.0):
    # Precompute all features in bulk for speed
    texts = [span["text"] for span in spans]
    lengths = np.array([len(t) for t in texts])
    sw_ratios = batch_stopword_ratio(texts)
    is_bold = np.array([(s["flags"] & 2) > 0 for s in spans])
    is_italic = np.array([(s["flags"] & 4) > 0 for s in spans])
    is_caps = np.array([t.isupper() and len(t) > 2 for t in texts])
    short_line = lengths <= 55
    leftish = np.array([s["bbox"][0] < 150 for s in spans])
    big_gap = np.array([s.get("spacing_above", 0) > 14 for s in spans])
    too_long = lengths > 70
    numbered = np.array([bool(re.match(r"^[0-9]+(\.[0-9]+)*(\s+|[.:])", t)) for t in texts])
    endsdot = np.array([t.lower().endswith(".") and len(t.split()) > 5 for t in texts])

    # font levels
    levels = np.array([size_to_level.get(s.get("cluster", 0), None) for s in spans])
    score = (
        2.5*(levels=="H1") + 2.0*(levels=="H2") + 1.5*(levels=="H3") +
        1.0*is_bold + 0.7*is_caps + 0.2*is_italic + 0.5*short_line +
        0.3*(leftish | numbered) + 0.7*big_gap + 0.4*numbered - 1.0*too_long
    )
    # 1. Strict exclusion for trash/bullets
    garbage = np.array(
        [t.strip() in ["•", "-", "—", ".", "·", "…", "*"] or
         t.strip().startswith(("•", "-", "–")) or
         (re.fullmatch(r"[0-9]+", t.strip()) is not None)
         for t in texts])
    too_sentence = (sw_ratios > 0.5) & (np.array([len(t.split()) for t in texts]) > 3)
    endsdot = (endsdot)
    too_longish = too_long
    long_numbered = np.array([
        bool(re.match(r"^\d+(\.\d+)*", t)) and len(t.split()) > 8 for t in texts
    ])
    # Mask for acceptable headings
    keep = (
        (score >= min_score) &
        (levels != None) &
        (~garbage) &
        (~too_sentence) &
        (~endsdot) &
        (~long_numbered) &
        (~too_longish)
    )

    seen = set()
    out = []
    for idx, s in enumerate(spans):
        if not keep[idx]:
            continue
        lv = levels[idx]
        sig = (texts[idx], lv, s['page'])
        if sig in seen: continue
        seen.add(sig)
        out.append({"level": lv, "text": texts[idx].strip(), "page": s['page']})

    # Merge consecutive short headings
    out = merge_split_headings(out)
    return out

def merge_split_headings(headings):
    merged = []
    skip_next = False
    for i, h in enumerate(headings):
        if skip_next:
            skip_next = False
            continue
        if i+1 < len(headings):
            if (h['page'] == headings[i+1]['page'] and len(h['text']) < 30 and len(headings[i+1]['text']) < 30):
                combined = h['text'] + " " + headings[i+1]['text']
                merged.append({"level": h["level"], "text": combined.strip(), "page": h["page"]})
                skip_next = True
                continue
        merged.append(h)
    return merged
