FROM --platform=linux/amd64 python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m nltk.downloader stopwords

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
