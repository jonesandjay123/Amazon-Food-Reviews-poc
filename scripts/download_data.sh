#!/bin/bash

# 建立資料目錄（如果不存在）
mkdir -p data

# 下載 BBC News 資料集
echo "正在下載 BBC News 資料集..."
curl -L -o data/bbc-news.csv https://storage.googleapis.com/ztm_tf_course/bbc-text.csv

# 檢查下載是否成功
if [ $? -ne 0 ]; then
    echo "下載失敗，請檢查連線並重試"
    exit 1
fi

# 轉換為 SQLite 資料庫
echo "正在轉換為 SQLite 資料庫..."
python scripts/csv_to_sqlite.py

echo "資料準備完成！" 