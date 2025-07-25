import json

def write_outline_json(title, headings, output_path):
    result = {
        "title": title or "Untitled",
        "outline": [
            {"level": h["level"], "text": h["text"], "page": h["page"]}
            for h in headings
        ]
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
