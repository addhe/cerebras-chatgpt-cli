# config.py
import os

# Model configuration
MODEL_ID = os.getenv("CEREBRAS_MODEL_ID", "llama-4-scout-17b-16e-instruct")

# System message configuration
SYSTEM_MESSAGE = {
    "role": "system",
    "content": os.getenv("CEREBRAS_SYSTEM_MESSAGE", "You are a helpful assistant.")
}

# API configuration
API_KEY = os.getenv("CEREBRAS_API_KEY")

# Application configuration
CHAR_DELAY = float(os.getenv("CHAR_DELAY", "0.02"))
