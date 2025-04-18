import pandas as pd
import sqlite3
import sys
import os

# Create data directory (if it doesn't exist)
os.makedirs("data", exist_ok=True)

# Read CSV file
print("Reading BBC News CSV file...")
df = pd.read_csv("data/bbc-news.csv")

# Connect to SQLite database
print("Creating SQLite database...")
con = sqlite3.connect("data/bbc_news.sqlite")

# Create table (add auto-incrementing id field)
print("Converting data to SQLite table...")
cursor = con.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    title TEXT,
    text TEXT
)
''')
con.commit()

# Store data in table
df.to_sql("news_temp", con, if_exists="replace", index=False)

# Copy data from temporary table to main table (to maintain auto-incrementing id)
cursor.execute('''
INSERT INTO news (category, title, text)
SELECT category, title, text FROM news_temp
''')
con.commit()

# Delete temporary table
cursor.execute("DROP TABLE news_temp")
con.commit()

# Close database connection
con.close()

print("BBC News data successfully converted to SQLite database (data/bbc_news.sqlite)")
print(f"Converted a total of {len(df)} news records") 