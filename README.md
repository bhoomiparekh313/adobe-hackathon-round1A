## Prerequisite (One-time Only, No Internet Needed at Runtime)
1. After installing NLTK and downloading 'stopwords' on your local machine:
   python -m pip install nltk
   python -m nltk.downloader stopwords
2. Copy the locally downloaded 'corpora/stopwords' folder into the project at 'nltk_data/corpora/stopwords/'.
3. Now build and run normally—No internet is needed for build or execution. All NLTK NLP resources are fully offline.
# Adobe Hackathon - Outline Extractor

## Offline Setup (One-time before Docker build)
1. Install NLTK and download stopwords:
    python -m pip install nltk
    python -m nltk.downloader stopwords
2. Copy your 'corpora/stopwords' folder (see note) into 'nltk_data/corpora/stopwords/' in this repo.
3. Build offline-ready image:
    docker build --platform linux/amd64 -t outline-extractor .
4. Run (fully offline):
    docker run --rm -v %cd%\input:/app/input -v %cd%\output:/app/output --network none outline-extractor

## Approach
- Multi-feature heading detection: font clustering, bold, caps, gaps, numbering, stopwords.
- No runtime/network calls. All resources pre-baked.
- Runs comfortably in <10s on a 50-page PDF.
