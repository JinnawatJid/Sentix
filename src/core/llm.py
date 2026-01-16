from google import genai
from google.genai import types
import os
import logging
import time
import random
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("CoreLLM")

def call_llm(prompt, model='gemini-3-flash-preview', fallback_model='gemini-2.5-flash'):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not found.")
        return None

    client = None
    try:
        # Use v1alpha as in agent.py to support newer models/features
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
    except Exception as e:
        logger.error(f"Failed to initialize Gemini Client: {e}")
        return None

    max_retries = 5
    base_delay = 5 # Start with 5 seconds (error message said ~8s)

    for attempt in range(max_retries):
        # Default to primary model
        current_model = model

        # On the last attempt (index 4 = 5th try), switch to fallback if available
        if attempt == max_retries - 1 and fallback_model:
            logger.warning(f"Max retries nearing limit. Switching to FALLBACK model: {fallback_model} for final attempt.")
            current_model = fallback_model

        try:
            response = client.models.generate_content(
                model=current_model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            # Check for 429 or "RESOURCE_EXHAUSTED" or "Quota exceeded"
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "Quota exceeded" in error_str:
                if attempt < max_retries - 1:
                    # Exponential Backoff with Jitter
                    delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                    logger.warning(f"LLM Rate Limit Hit (429) on {current_model}. Retrying in {delay:.2f}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"LLM Rate Limit Exceeded after {max_retries} attempts. Final attempt with {current_model} failed. Error: {e}")
                    return None
            else:
                # Non-retriable error
                logger.error(f"LLM Call Error on {current_model}: {e}")
                return None

    return None
