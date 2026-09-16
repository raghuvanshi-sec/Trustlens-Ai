import os

import serpapi
from dotenv import load_dotenv


load_dotenv()


class SerpApiService:
    def __init__(self):
        api_key = os.getenv("SERPAPI_API_KEY")

        if not api_key:
            raise RuntimeError("SERPAPI_API_KEY is not configured.")

        self.client = serpapi.Client(
            api_key=api_key,
            timeout=30
        )

    def search(self, query: str) -> dict:
        results = self.client.search({
            "engine": "google",
            "q": query,
            "output": "json",
            "num": 5
        })

        return dict(results)