import fitz
import numpy as np

def extract_text_spans(pdf_path):
    doc = fitz.open(pdf_path)
    all_spans = []
    for page_num, page in enumerate(doc, start=1):
        last_y = 0
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                y_min = line["bbox"][1]
                spacing_above = y_min - last_y if last_y else 0
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    all_spans.append({
                        "text": text,
                        "font": span["font"],
                        "size": round(span["size"], 2),
                        "flags": span["flags"],
                        "bbox": span["bbox"],
                        "page": page_num,
                        "spacing_above": spacing_above,
                        "line_y": y_min,
                    })
                last_y = line["bbox"][3]
    return all_spans
