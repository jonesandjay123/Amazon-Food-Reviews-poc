# gemini_model.py 
import os
import json
import google.generativeai as genai

MODEL_NAME = "gemini-2.5-pro-exp-03-25"       # Or "gemini-2.0-flash"

class GeminiModel:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(MODEL_NAME)

    def parse(self, query: str) -> dict:
        """Parse the natural language query into {category, keyword}"""
        prompt = (
            "Extract these JSON fields from the query if present:\n"
            "category (business|entertainment|politics|sport|tech), "
            "keyword (string)\n\n"
            f"Query: {query}"
        )
        res = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json"),
        )
        try:
            return json.loads(res.text)
        except json.JSONDecodeError:
            # If the LLM returns a random string, return {} to fall back
            return {}