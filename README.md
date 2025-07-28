Adobe Hackathon — PDF Outline Extractor (Round 1A)
Overview
This solution is an advanced, fully offline PDF outline extractor built specifically for the Adobe Hackathon Round 1A. It is designed to reliably parse and analyze PDF files, extract the document title, and automatically generate a concise, hierarchical outline (headings with H1/H2/H3 levels) in a standardized JSON format. The system leverages robust font and layout analysis, NLP-based heuristics, and strict noise filtering to ensure high accuracy across a wide variety of document styles and structures.

Key Features:

Accurate heading extraction (H1/H2/H3) using font clustering, boldness/caps, left/center alignment, vertical spacing, and semantic filtering.

Works fully offline — no network access required at any stage (build or run).

Highly optimized for speed: consistently completes in under 10 seconds for a 50-page PDF.

Modular, production-grade code for easy testing and maintenance.

How It Works
PDF Parsing:
The system parses each page of every PDF using the PyMuPDF library, extracting all text spans along with their typography (font, size, style), position, and spacing features.

Heading Candidate Detection:
Font sizes are clustered using KMeans to infer heading levels (H1, H2, H3). Candidate headings are identified by strong font/style cues and page/layout context (e.g. large, bold, spaced-above, left/centered).

Semantic & Noise Filtering:
Advanced rules filter out:

Lines with excessive symbols, bullets, or numeric noise.

Pure email addresses or long digit strings.

Fragments, body text, or fake headings common in noisy/complex PDFs.

Sentence-like lines with high stopword ratios or punctuation endings.

Outline Structuring:
True headings are organized into a clean hierarchy. Merging and deduplication ensure only genuine multi-line headings are joined, with artificial repeats or artifacts removed.

Output:
For each input PDF, the extractor produces a JSON file containing:

"title" — the document's main title (from metadata or top of the first page)

"outline" — a list of headings, each with "level", "text", and "page"

Offline Setup – One Time Only
To comply with hackathon requirements (no internet at build or runtime), all data dependencies must be included in the repository before building the Docker image.

1. Install NLTK and Download Stopwords (Locally, One Time)
Open your terminal and run:


python -m pip install nltk
python -m nltk.downloader stopwords
This installs NLTK if not already available and downloads the official NLTK English stopwords file.

2. Copy the NLTK Stopwords to Your Project
Find the downloaded folder (commonly at:
C:\Users\<your-username>\AppData\Roaming\nltk_data\corpora\stopwords on Windows).

Copy it into your project directory as follows:

Final project structure:


adobe-hackathon-round1A/
  ├── nltk_data/
  │    └── corpora/
  │        └── stopwords/
You can create the folders and copy with:


mkdir nltk_data
mkdir nltk_data\corpora
xcopy /E /I "%APPDATA%\nltk_data\corpora\stopwords" "nltk_data\corpora\stopwords"
Build & Run Instructions
All dependencies and data are now local: no internet connection required from here forward.

1. Build the Docker Image (Offline)
Open a terminal in your project root and run:


docker build --platform linux/amd64 -t outline-extractor .
This compiles your code, installs requirements, and bakes in the NLTK stopwords so the container is fully offline-enabled.

2. Prepare Your Inputs
Place all PDFs you want to process in the input/ folder of your project.

Create an empty output/ folder (if needed) to receive extracted JSONs.

3. Run the Extractor (Offline Runtime)
From your project directory, execute:


docker run --rm -v %cd%\input:/app/input -v %cd%\output:/app/output --network none outline-extractor
The extractor will process every PDF in input/ and produce one JSON outline per file in output/.

If no PDFs are found, the program exits quietly.

No network access is ever required during execution.

Example Output Format
For a sample input PDF, the corresponding output (in output/sample-file.json) will be:


{
  "title": "This is a test PDF file",
  "outline": [
    { "level": "H1", "text": "Section 1: Introduction", "page": 1 },
    { "level": "H2", "text": "Background and Motivation", "page": 1 },
    { "level": "H2", "text": "Results Overview", "page": 3 },
    { "level": "H3", "text": "Technical Details", "page": 4 }
  ]
}
Approach: Summary
Multi-feature heading detection: Combination of font size clustering, bold/caps detection, left/center alignment, spacing, numbering patterns, and NLP stopword analysis.

Noise-aware heuristics: Rules and regexes skip artificial headings, symbols, emails, synthetic artifacts, long digit strings, and run-on lines.

Offline-first: All resources are pre-baked. No NLTK downloads or internet dependency at build or runtime.

Fast: Sub-10s extraction for 50-page PDFs and robust handling of large or noisy files.

Output: JSON, with only meaningful, deduplicated headings assigned to H1, H2, or H3.

I have already attached some sample pdfs in the input section, if not needed then please delete.