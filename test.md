"""
Convert BBC News CSV → FAISS vector index

執行一次即可：
    python scripts/build_vectors.py
"""

import os, json, gzip
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv; load_dotenv()

from azure.identity import CertificateCredential
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ---------- Azure OpenAI 共用 ---------- #

def _get_azure_token() -> str:
    scope = "https://cognitiveservices.azure.com/.default"
    credential = CertificateCredential(
        tenant_id=os.getenv("TENANT_ID"),
        client_id=os.getenv("CLIENT_ID"),
        certificate_path=os.getenv("CERTIFICATE_PATH", "Terra.pem"),
    )
    return credential.get_token(scope).token

AZURE_KW = dict(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_version="2024-02-15-preview",
    azure_ad_token=_get_azure_token(),
)

EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING", "text-embedding-3-small")

# ---------- 讀取 BBC CSV ---------- #

DATA_DIR  = Path("data")
VEC_DIR   = DATA_DIR / "bbc_faiss"
CSV_FILE  = DATA_DIR / "bbc_news.csv"
CSV_GZ    = DATA_DIR / "bbc_news.csv.gz"     # 若你存成壓縮檔

print("🔄  Loading raw articles …")

if CSV_FILE.exists():
    df = pd.read_csv(CSV_FILE)
elif CSV_GZ.exists():
    with gzip.open(CSV_GZ, "rt", encoding="utf-8") as f:
        df = pd.read_csv(f)
else:
    raise FileNotFoundError("Neither bbc_news.csv nor bbc_news.csv.gz found in /data")

docs = df["text"].fillna("").tolist()

# ---------- 切 Chunk ---------- #

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    length_function=len,
)
chunks = splitter.create_documents(docs)

# ---------- 產生向量 ---------- #

print("🧠  Encoding with Azure OpenAI embeddings …")
emb = AzureOpenAIEmbeddings(
    azure_deployment=EMBED_DEPLOYMENT,
    **AZURE_KW,
)

db = FAISS.from_documents(documents=chunks, embedding=emb)

# ---------- 儲存 ---------- #

print("💾  Saving FAISS index …")
VEC_DIR.mkdir(parents=True, exist_ok=True)
db.save_local(str(VEC_DIR))

print("✅  Done!  Index stored at", VEC_DIR)
