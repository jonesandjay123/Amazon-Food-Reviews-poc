# gemini_model.py
import os, json, re
from google import genai

# MODEL_NAME = "gemini-2.5-pro-exp-03-25"
MODEL_NAME = "gemini-2.0-flash"

class GeminiModel:
    def __init__(self) -> None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY not set")
        self.client = genai.Client(api_key=key)

    def parse(self, query: str) -> dict:
        prompt = (
            "You are a keyword extractor.  \n"
            "ALWAYS reply with valid JSON: {\"keyword\": <string or null>}  \n"
            "Pick ONE meaningful keyword or noun phrase from the user query.  \n"
            "If nothing obvious, return null.  \n"
            "NO markdown, JSON ONLY.\n\n"
            f"Query: {query}"
        )
        res = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        raw = res.text.strip()
        # remove possible ```json block
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n(.*?)\n```$", r"\1", raw, flags=re.DOTALL).strip()
        return json.loads(raw)