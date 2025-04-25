# scripts/build_vectors.py
"""
把 BBC News JSON 做向量化並建立 FAISS 索引
第一次或文本更新後請先跑：
    python scripts/build_vectors.py
"""

import json, os
from pathlib import Path

from azure.identity import CertificateCredential
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ---------- Azure OpenAI 共用 ---------- #

def _get_azure_token() -> str:
    scope = "https://cognitiveservices.azure.com/.default"
    cred = CertificateCredential(
        tenant_id=os.getenv("TENANT_ID"),
        client_id=os.getenv("CLIENT_ID"),
        certificate_path=os.getenv("CERTIFICATE_PATH", "Terra.pem"),
    )
    return cred.get_token(scope).token

AZURE_KW = dict(
    openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_version="2024-02-15-preview",
    openai_api_key=_get_azure_token(),
    openai_api_type="azure",
)
EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING", "text-embedding-3-small")

# ---------- 讀取 BBC 原始 JSON ---------- #

DATA_DIR  = Path("data")
VEC_DIR   = DATA_DIR / "bbc_faiss"
RAW_FILE  = DATA_DIR / "bbc_news.json"

print("🔄  Loading raw articles …")
data = json.loads(RAW_FILE.read_text(encoding="utf-8"))
docs = [d["text"] for d in data]

# ---------- 切 Chunk ---------- #

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    length_function=len,
)
chunks = splitter.create_documents(docs)

# ---------- 產生向量 ---------- #

print("🧠  Encoding with Azure OpenAI embeddings …")
emb = AzureOpenAIEmbeddings(azure_deployment=EMBED_DEPLOYMENT, **AZURE_KW)

db = FAISS.from_documents(documents=chunks, embedding=emb)

print("💾  Saving FAISS index …")
VEC_DIR.mkdir(parents=True, exist_ok=True)
db.save_local(str(VEC_DIR))

print("✅  Done!  Index stored at", VEC_DIR)








# rag_model.py
from pathlib import Path
from typing import List, Tuple, Dict
import os

from azure.identity import CertificateCredential
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate

VEC_DIR = Path("data/bbc_faiss")          # ← 跟 build_vectors.py 存同處
MODEL_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-2024-05-13")

# ---------- Azure OpenAI 共用 ---------- #

def _get_azure_token() -> str:
    scope = "https://cognitiveservices.azure.com/.default"
    cred  = CertificateCredential(
        tenant_id=os.getenv("TENANT_ID"),
        client_id=os.getenv("CLIENT_ID"),
        certificate_path=os.getenv("CERTIFICATE_PATH", "Terra.pem"),
    )
    return cred.get_token(scope).token

AZURE_KW = dict(
    openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_version="2024-02-15-preview",
    openai_api_key=_get_azure_token(),      # 直接把 JWT token 當作 key
    openai_api_type="azure",
)

# ---------- RAG Model ---------- #

class RAGModel:
    """
    先以 similarity search 取 K 篇 BBC 文章，再用 Chat 完成回答
    """

    def __init__(self, k: int = 4):
        if not VEC_DIR.exists():
            raise RuntimeError("Vector store not found – 先執行 scripts/build_vectors.py")

        # Embedding & Vector Store
        emb = AzureOpenAIEmbeddings(azure_deployment=MODEL_DEPLOYMENT, **AZURE_KW)
        self.vs = FAISS.load_local(str(VEC_DIR), emb, allow_dangerous_deserialization=True)

        # LLM
        self.llm = AzureChatOpenAI(
            azure_deployment=MODEL_DEPLOYMENT,
            temperature=0.2,
            **AZURE_KW,
        )

        # Chain
        prompt = PromptTemplate.from_template(
            "Use the BBC News excerpts below to answer the user's question "
            "(max 3 sentences).\n\n"
            "{context}\n\nQuestion: {question}\nAnswer:"
        )
        self.chain = prompt | self.llm
        self.k = k

    # ---------- public API ---------- #
    def ask(self, query: str) -> Dict[str, str]:
        """return {'answer': str, 'context': str, 'matches': List[(doc, score)]}"""
        docs_scores: List[Tuple[str, float]] = self.vs.similarity_search_with_score(query, k=self.k)
        context = "\n\n".join([doc.page_content for doc, _ in docs_scores])

        answer = self.chain.invoke({"context": context, "question": query})
        return {"answer": answer, "context": context, "matches": docs_scores}








# chatgpt_model.py
"""
Baseline：只用 Chat 完成回答，無向量檢索
"""

import os
from azure.identity import CertificateCredential
from langchain_openai import AzureChatOpenAI

# ---------- Azure OpenAI 共用 ---------- #

def _get_azure_token() -> str:
    scope = "https://cognitiveservices.azure.com/.default"
    cred  = CertificateCredential(
        tenant_id=os.getenv("TENANT_ID"),
        client_id=os.getenv("CLIENT_ID"),
        certificate_path=os.getenv("CERTIFICATE_PATH", "Terra.pem"),
    )
    return cred.get_token(scope).token

AZURE_KW = dict(
    openai_api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
    openai_api_version="2024-02-15-preview",
    openai_api_key=_get_azure_token(),
    openai_api_type="azure",
)
MODEL_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-2024-05-13")

# ---------- 單純 Chat ---------- #

class ChatGPTModel:
    def __init__(self, temperature: float = 0.2):
        self.llm = AzureChatOpenAI(
            azure_deployment=MODEL_DEPLOYMENT,
            temperature=temperature,
            **AZURE_KW,
        )

    def ask(self, query: str) -> str:
        return self.llm.invoke(query)








# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://lmopenai.jpmchase.net/v15086-eus2-exp-use2/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-2024-05-13
AZURE_OPENAI_EMBEDDING=text-embedding-3-small

TENANT_ID=79C73825-CD5C-4D36-...
CLIENT_ID=AE39708-2E38-49CD-...
CERTIFICATE_PATH=Terra.pem      # ← 放在 repo 根
