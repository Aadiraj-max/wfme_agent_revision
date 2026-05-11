import sys
import os
import time

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

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

    def embed(self, text: str) -> list[float]:
        """
        Generates an embedding vector for a single string.

        Args:
            text (str): The input text to embed.

        Returns:
            list[float]: The resulting embedding vector.
        """
        result = client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return result.embeddings[0].values

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generates embedding vectors for a list of strings.
        Includes a 0.5s delay between calls to respect rate limits.

        Args:
            texts (list[str]): List of input strings.

        Returns:
            list[list[float]]: List of embedding vectors.
        """
        embeddings = []
        for text in texts:
            embeddings.append(self.embed(text))
            time.sleep(0.5)
        return embeddings


def embed_text(text: str) -> list[float]:
    """
    Convenience function for one-off embedding of a single string.

    Args:
        text (str): The input text to embed.

    Returns:
        list[float]: The resulting embedding vector.
    """
    return GeminiEmbedder().embed(text)


if __name__ == "__main__":
    try:
        embedder = GeminiEmbedder()
        test_text = "total headcount by department"
        print(f"Generating embedding for: '{test_text}'")
        vector = embedder.embed(test_text)
        print(f"Vector length: {len(vector)}")
        print(f"First 5 values: {list(vector[:5])}")
    except Exception as e:
        print(f"Error during smoke test: {e}")