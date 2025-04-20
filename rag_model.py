from pathlib import Path
from typing import Dict, List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI,
)
# --- OpenAI alternative (keep commented) ---
# from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from langchain_core.prompts import PromptTemplate

VEC_DIR = Path("data/bbc_faiss")

class RAGModel:
    def __init__(self):
        if not VEC_DIR.exists():
            raise RuntimeError("Vector store not found – run build_vectors.py")

        # Embeddings (Gemini)
        emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        # emb = OpenAIEmbeddings(model="text-embedding-3-small")  # OpenAI alt.

        # Vector store
        self.vs = FAISS.load_local(
            str(VEC_DIR),
            emb,
            allow_dangerous_deserialization=True
        )

        # LLM (Gemini Flash)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2
        )
        # self.llm = ChatOpenAI(model_name="gpt-3.5-turbo")        # OpenAI alt.

        # Prompt & chain (use RunnableSequence | syntax)
        prompt = PromptTemplate.from_template(
            "Use the BBC News excerpts below to answer the user's question "
            "(max 3 sentences).\n\n"
            "{context}\n\nQuestion: {question}\nAnswer:"
        )
        self.chain = prompt | self.llm   # LCEL 寫法

    # -------- public API --------
    def ask(self, query: str, k: int = 4) -> Dict:
        # get vector neighbors + score
        docs_scores: List[Tuple] = self.vs.similarity_search_with_score(query, k=k)

        # generate summary
        answer = self.chain.invoke({
            "context": "\n\n".join([d.page_content for d, _ in docs_scores]),
            "question": query
        })

        # format return
        chunks = []
        for d, score in docs_scores:
            chunks.append({
                "category": d.metadata.get("category"),
                "text"    : d.page_content,
                "score"   : round(float(score), 4)  # ✅ force float
            })

        # --- convert summary to pure string (compatible with different LangChain versions) ---
        if hasattr(answer, "content"):        # AIMessage
            summary = answer.content
        else:                                 # already str
            summary = str(answer)

        return {
            "answer": summary,
            "chunks": chunks
        }
