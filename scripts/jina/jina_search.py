import requests
import json
import os
import sys
from datetime import datetime

class JinaSearch:
    """
    Production-ready wrapper for Jina AI Reader/Search API.
    """
    def __init__(self, api_key=None):
        # Prioritize provided API key, then check environment variable
        self.api_key = api_key or os.getenv("JINA_API_KEY", "")
        self.base_url = "https://s.jina.ai/"

    def search(self, query, save_to_file=False):
        """
        Execute search and return results.
        """
        if not self.api_key:
            raise ValueError("JINA_API_KEY is not set.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Respond-With": "no-content",
            "Accept": "application/json"
        }
        
        params = {"q": query}
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if save_to_file:
                self._save_response(query, data)
                
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"Error during Jina search: {e}", file=sys.stderr)
            return None

    def _save_response(self, query, data):
        """
        Save the search response to the responses folder.
        """
        if not os.path.exists("scripts/jina/responses"):
            os.makedirs("scripts/jina/responses")
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c if c.isalnum() else "_" for c in query)[:50]
        filename = f"scripts/jina/responses/{timestamp}_{safe_query}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Response saved to {filename}")

def main():
    # Simple CLI interface for testing/production use
    if len(sys.argv) < 2:
        print("Usage: python jina_search.py <query>")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    client = JinaSearch()
    results = client.search(query, save_to_file=True)
    
    if results and "data" in results:
        print(f"\nFound {len(results['data'])} results for: {query}\n")
        for i, item in enumerate(results['data']):
            print(f"[{i+1}] {item.get('title')}")
            print(f"    URL: {item.get('url')}")
            print(f"    Desc: {item.get('description')[:100]}...\n")

if __name__ == "__main__":
    main()
