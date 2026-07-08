import sys
import os
import time

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from google import genai as google_genai
from google.genai import types as google_genai_types
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini").lower().strip()

class GeminiEmbedder:
    """
    A wrapper class for the Google Gemini embedding API using google-genai SDK.
    """
    def __init__(self, model: str = "gemini-embedding-001"):
        """
        Initializes the embedder with a specific model.

        Args:
            model (str): The Gemini embedding model name.
        """
        self.model = model
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.client = google_genai.Client(api_key=key) if key else None

    def embed(self, text: str) -> list[float]:
        """
        Generates an embedding vector for a single string with transient retry logic.

        Args:
            text (str): The input text to embed.

        Returns:
            list[float]: The resulting embedding vector.
        """
        max_retries = 5
        base_delay = 1.0
        for attempt in range(max_retries):
            try:
                result = self.client.models.embed_content(
                    model=self.model,
                    contents=text,
                    config=google_genai_types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                )
                return result.embeddings[0].values
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt)
                print(f"[Embedder] Network error or timeout ({e}). Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generates embedding vectors for a list of strings in batches.
        
        Args:
            texts (list[str]): List of input strings.

        Returns:
            list[list[float]]: List of embedding vectors.
        """
        if not texts:
            return []
            
        chunk_size = 15
        embeddings = []
        for i in range(0, len(texts), chunk_size):
            chunk = texts[i:i + chunk_size]
            max_retries = 5
            base_delay = 5.0
            for attempt in range(max_retries):
                try:
                    result = self.client.models.embed_content(
                        model=self.model,
                        contents=chunk,
                        config=google_genai_types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
                    )
                    embeddings.extend([emb.values for emb in result.embeddings])
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    # 429 quota exhaustion gets 30s delay
                    delay = 30.0 if "429" in str(e) or "quota" in str(e).lower() else (base_delay * (2 ** attempt))
                    print(f"[Embedder] Rate limit or network error ({e}) in batch. Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)
            if i + chunk_size < len(texts):
                time.sleep(10.0)
        return embeddings


class AICoreEmbedder:
    """
    A wrapper class for SAP AI Core embedding API using generative-ai-hub-sdk.
    """
    def __init__(self, model: str = None):
        self.model = model or os.getenv("GENAI_EMBEDDING_MODEL", "amazon.titan-embed-text-v1")
        if os.getenv("AICORE_OAUTH_URL") and not os.getenv("AICORE_AUTH_URL"):
            os.environ["AICORE_AUTH_URL"] = os.getenv("AICORE_OAUTH_URL")

    def embed(self, text: str) -> list[float]:
        from gen_ai_hub.proxy.native.openai import OpenAI
        max_retries = 5
        base_delay = 1.0
        client = OpenAI()
        for attempt in range(max_retries):
            try:
                result = client.embeddings.create(
                    model=self.model,
                    input=text
                )
                return result.data[0].embedding
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = base_delay * (2 ** attempt)
                print(f"[AICoreEmbedder] Network error ({e}). Retrying in {delay:.2f}s...")
                time.sleep(delay)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))
            time.sleep(0.5)
        return embeddings


def get_embedder():
    if EMBEDDING_PROVIDER == "aicore":
        return AICoreEmbedder()
    return GeminiEmbedder()


def embed_text(text: str) -> list[float]:
    """
    Convenience function for one-off embedding of a single string.
    """
    return get_embedder().embed(text)


if __name__ == "__main__":
    try:
        embedder = get_embedder()
        test_text = "total headcount by department"
        print(f"Generating embedding for: '{test_text}'")
        vector = embedder.embed(test_text)
        print(f"Vector length: {len(vector)}")
        print(f"First 5 values: {list(vector[:5])}")
    except Exception as e:
        print(f"Error during smoke test: {e}")