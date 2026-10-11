"""Small SerpApi adapter; import the optional client lazily for graceful startup."""
import os
from dotenv import load_dotenv

load_dotenv()


class SerpApiService:
    def __init__(self):
        api_key = os.getenv("SERPAPI_API_KEY")
        placeholders = {"your_actual_key_here", "your_serpapi_key_here", "your-serpapi-key", "replace_me"}
        if not api_key or api_key.strip().lower() in placeholders:
            raise RuntimeError("SERPAPI_API_KEY is not configured with a valid key.")
        try:
            import serpapi
        except ImportError as exc:
            raise RuntimeError("The 'serpapi' package is not installed. Run: python -m pip install -r requirements.txt") from exc
        self.client = serpapi.Client(api_key=api_key, timeout=30)

    def search(self, query: str) -> dict:
        results = self.client.search({"engine": "google", "q": query, "output": "json", "num": 5})
        return dict(results)
