"""
To Convert BBC News to a vector index (FAISS)
one-time: python scripts/build_vectors.py
"""
import sqlite3, os
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# --- OpenAI alternative ---
# from langchain_openai import OpenAIEmbeddings

DB_PATH  = Path("data/bbc_news.sqlite")
OUT_DIR  = Path("data/bbc_faiss")

if OUT_DIR.exists():
    print("Vector store already exists – skip."); exit(0)

print("Loading articles …")
con  = sqlite3.connect(DB_PATH)
rows = con.execute("SELECT rowid, category, text FROM news").fetchall()
con.close()

docs = []
splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
for rid, cat, txt in rows:
    for chunk in splitter.split_text(txt):
        docs.append({"id": rid, "category": cat, "content": chunk})

print("Embedding with Gemini …")
emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
# --- OpenAI alternative ---
# emb = OpenAIEmbeddings(model="text-embedding-3-small")

vec = FAISS.from_texts(
        texts=[d["content"] for d in docs],
        embedding=emb,
        metadatas=[{"id": d["id"], "category": d["category"]} for d in docs]
      )
vec.save_local(str(OUT_DIR))
print("✅  Saved vector store to", OUT_DIR)
