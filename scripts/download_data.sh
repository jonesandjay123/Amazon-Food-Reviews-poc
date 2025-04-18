#!/usr/bin/env bash
set -e

mkdir -p data

URL_PRIMARY="https://raw.githubusercontent.com/selva86/datasets/master/bbc-text.csv"
URL_FALLBACK="https://cdn.jsdelivr.net/gh/selva86/datasets@master/bbc-text.csv"

echo ">>> Downloading BBC News dataset…"
curl -fL "$URL_PRIMARY" -o data/bbc-news.csv \
  || { echo "[warn] primary URL failed, trying fallback…"; \
       curl -fL "$URL_FALLBACK" -o data/bbc-news.csv; }

echo ">>> Converting to SQLite…"
python scripts/csv_to_sqlite.py
echo ">>> DONE!"