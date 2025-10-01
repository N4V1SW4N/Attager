import os
# from google.adk.models.lite_llm import LiteLlm # Removed LiteLlm import as we're using native Gemini
# from google.adk.models.gemini import Gemini # This line is removed
# from google.generativeai import GenerativeModel # GenerativeModel import removed
import logging

logger = logging.getLogger(__name__)

def get_model_with_fallback():
    # 1. Try to load native ADK Gemini model using LiteLlm
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_model_name = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")

    if google_api_key:
        try:
            from google.adk.models.lite_llm import LiteLlm # Import LiteLlm here for Gemini via LiteLlm
            model = LiteLlm(
                model=google_model_name, # LiteLlm expects model name directly
                temperature=0.7, # Default temperature
            )
            logger.info(f"LiteLlm with Gemini model '{google_model_name}' loaded successfully.")
            return model
        except Exception as e:
            logger.warning(f"Failed to load LiteLlm with Gemini model '{google_model_name}': {e}. Falling back to LiteLlm (Ollama).")
    else:
        logger.warning("GOOGLE_API_KEY not found or failed to load Gemini via LiteLlm. Falling back to LiteLlm (Ollama).")

    # 2. Fallback to LiteLlm (Ollama) - Keep LiteLlm import here if Ollama fallback is desired
    from google.adk.models.lite_llm import LiteLlm # Import LiteLlm here for fallback only
    ollama_host = os.getenv("OLLAMA_HOST", "localhost")
    model = LiteLlm(
        model="ollama_chat/gpt-oss:20b",
        api_base=f"http://{ollama_host}:11434",
        temperature=0.7,
    )
    logger.info(f"LiteLlm model 'ollama_chat/gpt-oss:20b' (Ollama) loaded with API base: http://{ollama_host}:11434")
    return model
