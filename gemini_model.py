import os
import json
from google import genai
from google.genai import types

class GeminiModel:
    """Class for handling Gemini API interactions"""
    
    def __init__(self):
        """Initialize Gemini API client"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        # Create Google GenAI API client
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-pro-exp-03-25"
    
    def parse_natural_language_query(self, user_query):
        """
        Use Gemini API to parse a natural language query into structured parameters
        
        Args:
            user_query (str): User's natural language query
            
        Returns:
            dict: Structured query parameters
        """
        # Prepare prompt for Gemini
        prompt = f"""
        Based on the following natural language query, extract key search information for Amazon food reviews.
        Please return the following fields in JSON format (if relevant information exists):
        - keyword: Keywords in the review
        - min_score: Minimum rating (1-5)
        - max_score: Maximum rating (1-5)
        - product: Specific product name or ID
        - user: Specific user name or ID
        - sentiment: Sentiment orientation (positive, negative, neutral)

        For example: If the query is "Find 5-star chocolate reviews", you should return: {{"keyword": "chocolate", "min_score": 5, "max_score": 5}}

        Query: {user_query}
        """
        
        try:
            print(f"Processing query: {user_query}")
            
            # Call Gemini API
            gemini_response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            
            print(f"Gemini API raw response: {gemini_response.text}")
            
            # Parse Gemini response
            try:
                structured_query = json.loads(gemini_response.text)
                print(f"Structured query content: {structured_query}")
                return structured_query
            except json.JSONDecodeError as json_err:
                print(f"JSON parsing error: {json_err}. Original response: {gemini_response.text}")
                raise ValueError(f"Cannot parse model response as JSON: {str(json_err)}")
                
        except Exception as e:
            print(f"Query processing error: {e}")
            raise e 