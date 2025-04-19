import pandas as pd, sqlite3, os

# CSV Path and Database Path
CSV_PATH = "data/bbc-news.csv"
DB_PATH  = "data/bbc_news.sqlite"

# Check if database already exists
if os.path.exists(DB_PATH):
    print("DB already exists, skipping.")
    exit(0)

# Ensure data folder exists
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

# Check if CSV file exists
if not os.path.exists(CSV_PATH):
    print("Error: CSV file not found at", CSV_PATH)
    print("Please download the dataset manually from:")
    print("https://huggingface.co/datasets/hf-internal/bbc-text/resolve/main/bbc-text.csv")
    print("Then rename it to 'bbc-news.csv' and place it in the 'data/' folder.")
    exit(1)

print("Reading BBC News CSV file…")
df = pd.read_csv(CSV_PATH)

# Check if columns are as expected
assert {"category", "text"}.issubset(df.columns), "CSV columns are not as expected"

# Add title column: take the first sentence of each text (split by ".")
df["title"] = df["text"].str.split(".").str[0].str.strip()

print("Creating SQLite database…")
con = sqlite3.connect(DB_PATH)
df.to_sql("news", con, if_exists="replace", index=False)
con.close()

print("✅ SQLite table [news] created with", len(df), "rows.")
print("📌 Columns: category, title, text")
