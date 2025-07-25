import numpy as np
import re
import string
from sklearn.cluster import KMeans
from nltk.corpus import stopwords

STOPWORDS = set(stopwords.words("english"))

def cluster_font_sizes(spans):
    font_sizes = np.array([span["size"] for span in spans]).reshape(-1, 1)
    unique_sz = np.unique(font_sizes)
    k = min(3, len(unique_sz))
    if k < 1:
        return {}, None
    if len(unique_sz) == 1:
        # All text is same size
        return {0: "H1"}, None
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = kmeans.fit_predict(font_sizes)
    # Sort clusters by their centers, descending = H1>H2>H3
    clusters_sorted = np.argsort(kmeans.cluster_centers_.reshape(-1))[::-1]
    size_to_level = {cluster: f"H{i+1}" for i, cluster in enumerate(clusters_sorted)}
    for i, span in enumerate(spans):
        span["cluster"] = labels[i]
    return size_to_level, kmeans

def stopword_ratio(text):
    tokens = [t.lower().strip(string.punctuation) for t in text.split()]
    if not tokens:
        return 0
    sw_hits = sum(1 for t in tokens if t in STOPWORDS)
    return sw_hits / len(tokens)

def is_probable_heading(span):
    text = span["text"]
    # Explicit exclusion: bullets, dashes, lone symbols/numbers
    if text.strip() in ["•", "-", "—", ".", "·", "…", "*"] or len(text.strip()) < 3:
        return False
    if text.strip().startswith(("•", "-", "–", "•")):
        return False
    if re.fullmatch(r"[0-9]+", text.strip()):
        return False
    if len(text) > 70:
        return False
    if text.lower().endswith(".") and len(text.split()) > 5:
        return False

    # NLP stopword ratio
    sw_ratio = stopword_ratio(text)
    if sw_ratio > 0.5 and len(text.split()) > 3:  # Sentence, not a heading
        return False

    # Looks numbered but is long and sentence-like
    if re.match(r"^\d+(\.\d+)*", text) and len(text.split()) > 8:
        return False

    return True

def assign_heading_score(span, size_to_level):
    # Extract features
    score = 0
    font_cluster = span.get("cluster", None)
    level = size_to_level.get(font_cluster) if size_to_level else None
    is_bold = bool(span["flags"] & 2)
    is_italic = bool(span["flags"] & 4)
    is_caps = span["text"].isupper() and len(span["text"]) > 2
    short = len(span["text"]) <= 55
    leftish = span["bbox"][0] < 150  # px value, adjust if needed
    numbering = bool(re.match(r"^[0-9]+(\.[0-9]+)*(\s+|[.:])", span["text"]))

    # Heading Level from cluster (bigger font = higher)
    if level == "H1":
        score += 2.5
    elif level == "H2":
        score += 2.0
    elif level == "H3":
        score += 1.5
    # Style signals
    if is_bold:
        score += 1.0
    if is_caps:
        score += 0.7
    if is_italic:
        score += 0.2
    if short:
        score += 0.5
    if leftish or numbering:
        score += 0.3
    # Spacing above (if there is a significant vertical gap)
    if span.get("spacing_above", 0) > 14:
        score += 0.7
    # Bonus for classic numbering
    if numbering:
        score += 0.4
    
    # Penalize very long (not heading-like)
    if len(span["text"]) > 70:
        score -= 1.0

    return score, level

def merge_split_headings(headings):
    # Merge consecutive headings that are likely split due to PDF layout
    merged = []
    skip_next = False
    for i, h in enumerate(headings):
        if skip_next:
            skip_next = False
            continue
        if i+1 < len(headings):
            # Merge two short consecutive headings if both on same page and close vertically
            if (h['page'] == headings[i+1]['page'] and
                abs(h['page'] - headings[i+1]['page']) <= 1 and
                len(h['text']) < 30 and len(headings[i+1]['text']) < 30):
                combined = h['text'] + " " + headings[i+1]['text']
                merged.append({
                    "level": h["level"],
                    "text": combined.strip(),
                    "page": h["page"]
                })
                skip_next = True
                continue
        merged.append(h)
    return merged

def classify_headings(spans, size_to_level, min_score=3.1):
    headings = []
    seen = set()
    for span in spans:
        # Advanced feature gating
        if not is_probable_heading(span):
            continue
        score, level = assign_heading_score(span, size_to_level)
        if score >= min_score and level in ["H1", "H2", "H3"]:
            sig = (span["text"], level, span["page"])
            if sig in seen:
                continue
            seen.add(sig)
            headings.append({
                "level": level,
                "text": span["text"].strip(),
                "page": span["page"]
            })
    # Merge/join mistakenly fragmented headings
    return merge_split_headings(headings)
