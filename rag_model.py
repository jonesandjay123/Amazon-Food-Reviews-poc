from pathlib import Path
from typing import Dict, List
from langchain_community.vectorstores import FAISS
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI,
)
# --- OpenAI alternative ---        
# from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

VEC_DIR = Path("data/bbc_faiss")

class RAGModel:
    def __init__(self):
        if not VEC_DIR.exists():
            raise RuntimeError("Vector store not found – run build_vectors.py")

        emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        # emb = OpenAIEmbeddings(model="text-embedding-3-small")  # OpenAI alternative

        self.vs = FAISS.load_local(
            str(VEC_DIR),
            emb,
            allow_dangerous_deserialization=True
        )

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest", temperature=0.2
        )
        # self.llm = ChatOpenAI(model_name="gpt-3.5-turbo")        # OpenAI alternative

        self.prompt = PromptTemplate.from_template(
            "Use the BBC News excerpts below to answer the user's question "
            "(max 3 sentences).\n\n"
            "{context}\n\nQuestion: {question}\nAnswer:"
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    def ask(self, query: str, k: int = 4) -> Dict:
        docs = self.vs.similarity_search(query, k=k)
        answer = self.chain.run(
            context="\n\n".join(d.page_content for d in docs),
            question=query,
        )
        return {
            "answer": answer,
            "chunks": [
                {
                    "category": d.metadata["category"],
                    "text": d.page_content[:200] + "…",
                }
                for d in docs
            ],
        }
