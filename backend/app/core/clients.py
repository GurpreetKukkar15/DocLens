from google import genai
from groq import Groq
from qdrant_client import QdrantClient

from app.config import (
    GEMINI_API_KEY,
    GROQ_API_KEY,
    QDRANT_HOST,
    QDRANT_PORT,
)

# Shared client instances — initialized once at startup
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
