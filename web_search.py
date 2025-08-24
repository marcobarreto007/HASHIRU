import time
from typing import Dict, List, Any
from duckduckgo_search import DDGS

class WebSearchEvolution:
    """
    Web search with learning capabilities using DuckDuckGo.
    Includes a simple time-based cache.
    """

    def __init__(self, cache_hours: int = 2):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_duration_seconds = cache_hours * 3600
        self.ddgs = DDGS()

    def _is_cache_valid(self, query: str) -> bool:
        """Checks if a cached result for a query is still valid."""
        if query not in self.cache:
            return False

        cache_entry = self.cache[query]
        return (time.time() - cache_entry['timestamp']) < self.cache_duration_seconds

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Performs a web search using DuckDuckGo, with caching.

        :param query: The search query.
        :param max_results: The maximum number of results to return.
        :return: A list of search result dictionaries.
        """
        if self._is_cache_valid(query):
            print(f"Returning cached result for '{query}'")
            return self.cache[query]['results']

        print(f"Performing new web search for '{query}'")
        try:
            results = self.ddgs.text(query, max_results=max_results)

            # Ensure results is not None and is iterable
            if results:
                formatted_results = [
                    {'title': r.get('title', ''), 'href': r.get('href', ''), 'body': r.get('body', '')}
                    for r in results
                ]
            else:
                formatted_results = []

            self.cache[query] = {
                'timestamp': time.time(),
                'results': formatted_results
            }
            return formatted_results
        except Exception as e:
            print(f"An error occurred during web search: {e}")
            return []
