#!/bin/bash
kaggle datasets download snap/amazon-fine-food-reviews
mkdir -p data
unzip -o amazon-fine-food-reviews.zip -d data/
echo "Data download completed, extracted to data directory" 