#!/bin/bash

# Create data directory (if it doesn't exist)
mkdir -p data

# Download BBC News dataset
echo "Downloading BBC News dataset..."
curl -L -o data/bbc-news.csv https://storage.googleapis.com/ztm_tf_course/bbc-text.csv

# Check if download was successful
if [ $? -ne 0 ]; then
    echo "Download failed, please check your connection and try again"
    exit 1
fi

# Convert to SQLite database
echo "Converting to SQLite database..."
python scripts/csv_to_sqlite.py

echo "Data preparation complete!" 