import os
import json
import base64
from azure.identity import CertificateCredential
from azure.core.credentials import AccessToken
from azure.ai.openai import AzureOpenAI


HTTP_PROXY = "..."
HTTPS_PROXY = "..."
CLIENT_ID = "..."
CERTIFICATE_PATH = "..."
TENANT_ID = "..."
MODEL_NAME = "..."

SCOPE = "..."

AZURE_OPENAI_ENDPOINT = "..."
API_VERSION = "..."

class ChatGPTModel:
    """Class for handling ChatGPT API interactions through Azure OpenAI"""
    
    def __init__(self):
        """Initialize Azure OpenAI client"""
        # set proxy environment variables
        if os.environ.get("no_proxy", "").split(",")[-1] == "openai.azure.com":
            os.environ["no_proxy"] = os.environ["no_proxy"] + ",openai.azure.com"

        os.environ["http_proxy"] = HTTP_PROXY
        os.environ["https_proxy"] = HTTPS_PROXY
        
        # hardcoded authentication information
        self.client_id = CLIENT_ID
        self.certificate_path = CERTIFICATE_PATH
        self.tenant_id = TENANT_ID
        self.model_name = MODEL_NAME
        
        # initialize Azure OpenAI client
        try:
            self.client = self.get_openai_instance()
            print("Azure OpenAI client initialized successfully")
        except Exception as e:
            print(f"Error initializing Azure OpenAI client: {e}")
            raise e
    
    def get_token(self):
        """Get Azure authentication token"""
        scope = SCOPE
        credential = CertificateCredential(
            client_id=self.client_id,
            certificate_path=self.certificate_path,
            tenant_id=self.tenant_id
        )
        cred_info = credential.get_token(scope)
        return cred_info.token
    
    def get_openai_instance(self):
        """Create and return Azure OpenAI client"""
        client = AzureOpenAI(
            credential=self.get_token(),
            api_version=API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        return client
    
    def parse_natural_language_query(self, user_query):
        """
        Use Azure OpenAI (ChatGPT) API to parse a natural language query into structured parameters
        
        Args:
            user_query (str): User's natural language query
            
        Returns:
            dict: Structured query parameters
        """
        try:
            # prepare prompt
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
            
            # prepare conversation history
            conversation_history = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts structured data from natural language queries. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # call Azure OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                temperature=0.1,
                messages=conversation_history
            )
            
            # parse response
            content = response.choices[0].message.content
            print(f"Azure OpenAI raw response: {content}")
            
            structured_query = json.loads(content)
            print(f"Structured query content: {structured_query}")
            return structured_query
            
        except Exception as e:
            print(f"Query processing error: {e}")
            raise e 