from google import genai
from google.genai import types
import os
import logging
import time
import random
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("CoreLLM")

# Global Circuit Breaker State
_FAILURE_COUNT = 0
_FALLBACK_ACTIVE = False
_FALLBACK_UNTIL = 0
_COOLDOWN_SECONDS = 600  # 10 minutes

def call_llm(prompt, model='gemini-3-flash-preview', fallback_model='gemini-2.5-flash'):
    global _FAILURE_COUNT, _FALLBACK_ACTIVE, _FALLBACK_UNTIL

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

    # Check Circuit Breaker Status
    if _FALLBACK_ACTIVE:
        if time.time() < _FALLBACK_UNTIL:
            logger.warning(f"Global Fallback Mode ACTIVE. Skipping {model}, using {fallback_model} immediately. (Resets in {int(_FALLBACK_UNTIL - time.time())}s)")
            model = fallback_model  # Force primary model to be the fallback
        else:
            logger.info("Global Fallback Mode Cooldown Expired. Attempting to revert to Primary Model.")
            _FALLBACK_ACTIVE = False
            _FAILURE_COUNT = 0

    max_retries = 5
    base_delay = 5  # Start with 5 seconds

    for attempt in range(max_retries):
        # Determine current model for this attempt
        current_model = model

        # Logic for local fallback on last attempt (if global fallback isn't already forcing it)
        # If we are already in global fallback, 'model' is already 'fallback_model', so this logic is redundant but harmless.
        if attempt == max_retries - 1 and fallback_model and current_model != fallback_model:
            logger.warning(f"Max retries nearing limit. Switching to FALLBACK model: {fallback_model} for final attempt.")
            current_model = fallback_model

        try:
            response = client.models.generate_content(
                model=current_model,
                contents=prompt
            )

            # If we succeed on the PRIMARY model, we can verify if we should reset counters?
            # Actually, we reset counters only when cooldown expires or maybe on success?
            # The requirement says "switch... for a while". So cooldown logic is safer.
            # But if we accidentally get a success on primary, maybe we shouldn't reset immediately to avoid flapping.
            # However, if we are NOT in fallback mode, and we succeed, we should probably reset failure count
            # to avoid accumulated failures over long periods triggering the breaker.
            if not _FALLBACK_ACTIVE and current_model != fallback_model:
                 _FAILURE_COUNT = 0

            return response.text

        except Exception as e:
            error_str = str(e)
            is_rate_limit = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "Quota exceeded" in error_str

            if is_rate_limit:
                # Handle Rate Limit Logic
                if not _FALLBACK_ACTIVE and current_model != fallback_model:
                    _FAILURE_COUNT += 1
                    logger.warning(f"Rate Limit Hit on Primary. Global Failure Count: {_FAILURE_COUNT}/4")

                    if _FAILURE_COUNT >= 4:
                        _FALLBACK_ACTIVE = True
                        _FALLBACK_UNTIL = time.time() + _COOLDOWN_SECONDS
                        logger.error(f"Global Rate Limit Threshold Reached ({_FAILURE_COUNT}). ACTIVATING GLOBAL FALLBACK MODE for {_COOLDOWN_SECONDS}s.")

                # Standard Retry Logic
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
