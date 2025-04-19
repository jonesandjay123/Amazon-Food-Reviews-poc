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
            "Extract JSON fields {category, keyword} from the query if present.\n"
            "Categories: business, entertainment, politics, sport, tech.\n"
            "Please respond only with valid JSON.\n\n"
            f"Query: {query}"
        )
        try:
            res = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )

            raw = res.text.strip()

            # 清除 markdown 格式的 JSON 區塊 ```json\n...\n```
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\n(.*?)\n```$", r"\1", raw, flags=re.DOTALL).strip()

            return json.loads(raw)

        except Exception as e:
            print("⚠️ LLM 回傳錯誤：", e)
            print("↪️ 回傳內容：", getattr(res, 'text', '(no response)'))
            return {}