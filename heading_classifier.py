import numpy as np
import re
import string
from sklearn.cluster import KMeans
from nltk.corpus import stopwords

STOPWORDS = set(stopwords.words("english"))
BULLET_CHARS = {"•", "-", "—", "·", "*"}

EMAIL_REGEX = re.compile(r'\b[\w.-]+@[\w.-]+\.\w{2,7}\b')
LONG_DIGITS_REGEX = re.compile(r'\b\d{6,}\b')

def cluster_font_sizes(spans):
    font_sizes = np.array([span["size"] for span in spans]).reshape(-1, 1)
    if len(font_sizes) == 0:
        return {}, None
    unique_sz = np.unique(font_sizes)
    k = min(3, len(unique_sz))
    if k == 1:
        return {0: "H1"}, None
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = kmeans.fit_predict(font_sizes)
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

def is_noise_text(text):
    """Detect high-noise lines: mostly symbols/numbers, emails, or gibberish."""
    stripped = text.strip()
    if not stripped:
        return True

    # Too many symbols or digits >50%
    symbols_digits = sum(1 for c in stripped if not c.isalnum())
    if symbols_digits / max(len(stripped), 1) > 0.5:
        return True

    # Contains email or long digit string
    if EMAIL_REGEX.search(stripped) or LONG_DIGITS_REGEX.search(stripped):
        return True

    # Too short non-alpha fragment
    if len(stripped) < 4 and not any(c.isalpha() for c in stripped):
        return True

    return False

def is_heading_candidate(span, level, is_title_area=False):
    text = span['text']
    # Basic text filters
    if len(text) < 4:
        return False
    if any(text.lstrip().startswith(b) for b in BULLET_CHARS):
        return False
    if all(c in BULLET_CHARS for c in text):
        return False
    if re.fullmatch(r"\d{1,4}", text):
        return False
    if is_noise_text(text):
        return False

    # Title area special pass (usually top of page 1 large font)
    if is_title_area and level == "H1" and span["size"] >= 16:
        return True

    # Style cues
    bold = (span["flags"] & 2) != 0
    italic = (span["flags"] & 4) != 0
    caps = text.isupper() and len(text) > 4
    leftish = span["bbox"][0] < 100 or (90 < span["bbox"][0] < 220)
    centered = 90 < span["bbox"][0] < 300
    big_gap = span["spacing_above"] > 10

    # Sentence/run-on checks
    too_long = len(text) > 78
    many_words = len(text.split()) > 10
    ratio = stopword_ratio(text)
    runs_on = (
        text.endswith(".") or
        text.endswith("?") or
        text.endswith("!") or
        (many_words and ratio > 0.50) or
        (len(text.split()) >= 4 and ratio > 0.65)
    )
    numbered_long = bool(re.match(r"^[0-9]+(\.[0-9]+)*", text)) and many_words
    bulletlist = text.lstrip().startswith(tuple(BULLET_CHARS)) and not bold
    awkward = text.endswith(",") or text.endswith(";") or ".." in text

    # Scoring heuristics
    score = 0
    if level == "H1":
        score += 3.2
    elif level == "H2":
        score += 1.8
    elif level == "H3":
        score += 1.3

    if span["size"] >= 13.5:
        score += 0.8
    if bold:
        score += 1.3
    if caps:
        score += 0.8
    if big_gap:
        score += 1.0
    if leftish or centered:
        score += 0.4
    if italic:
        score += 0.3
    if len(text) < 53:
        score += 0.3
    if bool(re.match(r"^[0-9]+(\.[0-9]+)*(\s+|[.:])", text)):
        score += 0.3

    # Penalties
    if too_long:
        score -= 2.0
    if awkward:
        score -= 1.3
    if bulletlist:
        score -= 2.2
    if numbered_long:
        score -= 1.7
    if runs_on:
        score -= 1.7

    return score >= 3.3

def batch_assign_headings(spans, size_to_level):
    headings = []
    seen = set()
    max_firstpage_y = min(350, max((s['line_y'] for s in spans if s['page'] == 1), default=350))

    h1_seen_pages = set()  # To allow only one H1 on first page and limit others

    for span in spans:
        level = size_to_level.get(span.get("cluster", 999), None)
        is_title_spot = (span['page'] == 1 and span['line_y'] < max_firstpage_y)
        if not level or level not in {"H1", "H2", "H3"}:
            continue
        if level == "H1":
            # Limit H1 to only first page and once, or if big gap on others
            if span['page'] != 1:
                # Disallow H1 on pages >1 (except very rare special case)
                continue
            if 1 in h1_seen_pages:
                continue
            h1_seen_pages.add(1)

        if is_heading_candidate(span, level, is_title_area=is_title_spot):
            text = span["text"].strip()
            if len(text) < 4:
                continue
            # Skip repeated "Document Title – Page N" style headers after first appearance
            if re.match(r"Document Title\s*[-–]\s*Page \d+", text, re.I):
                if span['page'] != 1:
                    continue

            sig = (text, level, span['page'])
            if sig in seen:
                continue
            seen.add(sig)
            headings.append({
                "level": level,
                "text": text,
                "page": span['page'],
                "y": span["line_y"]
            })
    # Postprocess: merge and dedupe intelligently
    return postprocess_headings(headings)

def postprocess_headings(headings):
    if not headings:
        return []
    cleaned = []
    skip = False
    N = len(headings)
    for i, h in enumerate(headings):
        if skip:
            skip = False
            continue
        if i + 1 < N:
            h2 = headings[i + 1]
            if (
                h["page"] == h2["page"] and
                h["level"] == h2["level"] and
                len(h["text"]) < 30 and not h["text"].endswith((".", "?", "!")) and
                len(h2["text"]) < 30 and not h2["text"].endswith((".", "?", "!")) and
                abs(h["y"] - h2["y"]) < 20
            ):
                merged = h["text"].rstrip() + " " + h2["text"].lstrip()
                cleaned.append({"level": h["level"], "text": merged.strip(), "page": h["page"]})
                skip = True
                continue
        cleaned.append({"level": h["level"], "text": h["text"], "page": h["page"]})

    seen = set()
    final = []
    for h in cleaned:
        sig = (h["text"].lower(), h["level"], h["page"])
        if sig in seen or len(h["text"]) < 4:
            continue
        seen.add(sig)
        final.append({"level": h["level"], "text": h["text"], "page": h["page"]})
    return final
