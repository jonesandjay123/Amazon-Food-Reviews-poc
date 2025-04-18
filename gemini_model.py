# gemini_model.py  （最小可跑版本）
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

    def parse_natural_language_query(self, user_query: str) -> dict:
        prompt = (
            "Extract the following JSON fields from the query if present:\n"
            "keyword, category (business/entertainment/politics/sport/tech)\n\n"
            f"Query: {user_query}"
        )

        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            ),
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini did not return valid JSON: {e}\n{response.text}")
