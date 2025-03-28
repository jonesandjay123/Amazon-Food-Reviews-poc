#!/bin/bash
kaggle datasets download snap/amazon-fine-food-reviews
mkdir -p data
unzip -o amazon-fine-food-reviews.zip -d data/
echo "數據下載完成，已解壓到data目錄" 