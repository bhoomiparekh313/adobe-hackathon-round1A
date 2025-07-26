import os
import fitz

from extract_fonts_and_spacings import extract_text_spans
from heading_classifier import cluster_font_sizes, classify_headings
from outline_writer import write_outline_json

INPUT_DIR = "input"
OUTPUT_DIR = "output"

def extract_title(pdf_path):
    doc = fitz.open(pdf_path)
    meta = doc.metadata.get("title")
    if meta and meta.strip():
        return meta.strip()
    first_page = doc[0]
    blocks = first_page.get_text("dict")["blocks"]
    candidates = []
    for b in blocks:
        for line in b.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if len(text) >= 8 and 150 < span["bbox"][0] < 300:
                    candidates.append((text, span["size"]))
    if candidates:
        return max(candidates, key=lambda x: x[1])[0]
    return "Untitled"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for filename in os.listdir(INPUT_DIR):
        if not filename.lower().endswith(".pdf"):
            continue
        pdf_path = os.path.join(INPUT_DIR, filename)
        spans = extract_text_spans(pdf_path)
        size_to_level, _ = cluster_font_sizes(spans)
        headings = classify_headings(spans, size_to_level)
        title = extract_title(pdf_path)
        output_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))
        write_outline_json(title, headings, output_path)
        print(f"Processed {filename}. {len(headings)} headings extracted.")

if __name__ == "__main__":
    main()
