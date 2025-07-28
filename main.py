import os
import fitz

from extract_fonts_and_spacings import extract_text_spans
from heading_classifier import cluster_font_sizes, batch_assign_headings
from outline_writer import write_outline_json

INPUT_DIR = "input"
OUTPUT_DIR = "output"

def extract_title(pdf_path):
    doc = fitz.open(pdf_path)
    meta = doc.metadata.get("title")
    if meta and meta.strip():
        return meta.strip()
    page0 = doc[0]
    blocks = page0.get_text("dict")["blocks"]
    title_cands = []
    for b in blocks:
        for line in b.get("lines", []):
            for span in line["spans"]:
                # Try only big enough fonts and left-centered text zones
                if span["size"] >= 16 and (110 < span["bbox"][0] < 300) and len(span["text"].strip()) > 7:
                    title_cands.append((span["text"].strip(), span["size"]))
    if title_cands:
        return sorted(title_cands, key=lambda x: x[1], reverse=True)[0][0]
    return "Untitled"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for filename in os.listdir(INPUT_DIR):
        if not filename.lower().endswith(".pdf"):
            continue
        pdf_path = os.path.join(INPUT_DIR, filename)
        spans = extract_text_spans(pdf_path)
        size_to_level, _ = cluster_font_sizes(spans)
        headings = batch_assign_headings(spans, size_to_level)
        title = extract_title(pdf_path)
        output_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))
        write_outline_json(title, headings, output_path)
        print(f"Processed {filename}. {len(headings)} headings extracted.")

if __name__ == "__main__":
    main()
