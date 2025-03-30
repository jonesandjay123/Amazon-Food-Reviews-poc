import os
import json
import openai

class ChatGPTModel:
    """Class for handling ChatGPT API interactions"""
    
    def __init__(self):
        """Initialize ChatGPT API client"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
        
        # Model configuration
        self.model_name = "gpt-4-turbo"  # can be adjusted based on needs
    
    def parse_natural_language_query(self, user_query):
        """
        Use ChatGPT API to parse a natural language query into structured parameters
        
        Args:
            user_query (str): User's natural language query
            
        Returns:
            dict: Structured query parameters
        """
        # TODO: implement ChatGPT API call logic
        # below is an example structure, needs to be adjusted based on actual OpenAI API
        
        """
        # 示例實現（需要完善）:
        try:
            # 準備 prompt
            prompt = f'''
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
            '''
            
            # 呼叫 OpenAI API
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from natural language queries."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # 解析回應
            content = response.choices[0].message.content
            structured_query = json.loads(content)
            return structured_query
            
        except Exception as e:
            print(f"Query processing error: {e}")
            raise e
        """
        
        # temporary return empty result, waiting to be implemented
        return {"error": "ChatGPT implementation not complete"} 