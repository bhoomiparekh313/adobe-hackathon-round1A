import fitz

def extract_text_spans(pdf_path):
    doc = fitz.open(pdf_path)
    spans = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        last_y = 0
        for b in blocks:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                y_min = line["bbox"][1]
                spacing_above = y_min - last_y if last_y else 0
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    span_dict = {
                        "text": text,
                        "font": span["font"],
                        "size": round(span["size"], 2),
                        "flags": span["flags"],
                        "color": span["color"],
                        "bbox": span["bbox"],
                        "page": page_num,
                        "spacing_above": spacing_above,
                        "line_y": y_min,
                        "block_no": b.get("number", 0)
                    }
                    spans.append(span_dict)
                last_y = line["bbox"][3]
    return spans
