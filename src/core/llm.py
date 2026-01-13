from google import genai
from google.genai import types
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("CoreLLM")

def call_llm(prompt, model='gemini-2.0-flash-exp'):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found.")
        return None

    try:
        # Use v1alpha as in agent.py to support newer models/features
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )

        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        return response.text
    except Exception as e:
        logger.error(f"LLM Call Error: {e}")
        return None
