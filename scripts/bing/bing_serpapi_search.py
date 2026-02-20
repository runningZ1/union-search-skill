#!/usr/bin/env python3
"""
Bing Search Module (SerpAPI Version)

Uses SerpAPI to perform Bing searches as a backup/alternative method.
Updated with full features from https://serpapi.com/bing-search-api
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
script_dir = os.path.dirname(os.path.abspath(__file__))
skill_root = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(skill_root, '.env'))

try:
    from serpapi import GoogleSearch
except ImportError:
    print("Error: 'google-search-results' package is required. Install it with: pip install google-search-results", file=sys.stderr)
    sys.exit(1)

class BingSerpApiSearch:
    """Bing Search Client using SerpAPI"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the client

        Args:
            api_key: SerpAPI API Key
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            # Fallback to hardcoded key only if env var is missing (usage in previous context)
            self.api_key = "bc9927d2db1c2cde1ff9efe14a7b295855ef99912fb90fb8544df3a871e43372" 
        
        if not self.api_key:
             raise ValueError("SerpAPI API Key is required. Set SERPAPI_API_KEY env var or pass it to constructor.")

    def search(
        self,
        query: str,
        page: int = 1,
        lang: str = "en",
        country: str = "us",
        location: Optional[str] = None,
        market: Optional[str] = None,
        safe_search: str = "Moderate",
        device: str = "desktop",
        no_cache: bool = False,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Execute search with advanced parameter support

        Args:
            query: Search keywords
            page: Page number
            lang: Language code (default: en)
            country: Country code (default: us). Used for 'cc' parameter.
            location: Specific location (e.g., "New York, NY"). Overrides 'cc' behaviors if specific.
            market: Market code (e.g., "en-US"). Mutually exclusive with 'cc'.
            safe_search: Filtering for adult content (Off, Moderate, Strict)
            device: Device type (desktop, tablet, mobile)
            no_cache: Force fresh results
            max_results: Max results to return

        Returns:
            List of search results
        """
        
        # Calculate offset. 
        # 'first' parameter: 1-based index of the first result.
        first = (page - 1) * 10 + 1

        params = {
            "engine": "bing",
            "q": query,
            "first": first,
            "count": max_results,
            "api_key": self.api_key,
            "safeSearch": safe_search,
            "device": device,
            "no_cache": str(no_cache).lower()
        }

        # Handling Location/Market/Country logic
        # 'mkt' and 'cc' are mutually exclusive.
        if market:
            params["mkt"] = market
        else:
            # If no market specified, check if we should use 'cc'
            # Note: 'location' parameter acts independently but often implies a region.
            if location:
                params["location"] = location
            
            # Use 'cc' if no market is defined. 
            # If both location and cc are present, SerpAPI allows them, but location > cc for origin.
            params["cc"] = country.upper()

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Check for API-level errors
            if "error" in results:
                raise Exception(results["error"])
            
            # Check metadata status
            metadata = results.get("search_metadata", {})
            if metadata.get("status") == "Error":
                raise Exception(f"SerpAPI Error: {metadata.get('id', 'Unknown ID')}")

            organic_results = results.get("organic_results", [])
            
            formatted_results = []
            for item in organic_results:
                formatted_results.append({
                    'title': item.get('title', ''),
                    'href': item.get('link', ''),
                    'body': item.get('snippet', ''),
                    'displayed_link': item.get('displayed_link', '')
                })

            return formatted_results[:max_results]

        except Exception as e:
            raise Exception(f"Bing SerpAPI Search failed: {str(e)}")

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format search results"""
        output = []
        output.append(f"🔍 Bing (SerpAPI) Search: {query}")
        output.append(f"📊 Found {len(results)} results")
        output.append("")

        for i, item in enumerate(results, 1):
            output.append(f"[{i}] {item.get('title', '')}")
            output.append(f"    🔗 {item.get('href', '')}")
            if item.get('body'):
                output.append(f"    📝 {item.get('body', '')}")
            output.append("")

        return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description="Bing Search (via SerpAPI)")
    parser.add_argument("query", help="Search keywords")
    parser.add_argument("-p", "--page", type=int, default=1, help="Page number (default: 1)")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("-l", "--lang", default="en", help="Language code (default: en)")
    parser.add_argument("-c", "--country", default="us", help="Country code (default: us)")
    parser.add_argument("--location", help="Specific location (e.g. 'New York, NY')")
    parser.add_argument("--market", help="Market code (e.g. 'en-US'). Mutually exclusive with country.")
    parser.add_argument("--safe", choices=['Off', 'Moderate', 'Strict'], default='Moderate', help="Safe search level")
    parser.add_argument("--device", choices=['desktop', 'tablet', 'mobile'], default='desktop', help="Device type")
    parser.add_argument("--no-cache", action="store_true", help="Force fresh results (no cache)")
    
    parser.add_argument("--api-key", help="SerpAPI API Key")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")

    args = parser.parse_args()

    try:
        client = BingSerpApiSearch(api_key=args.api_key)
        results = client.search(
            query=args.query,
            page=args.page,
            lang=args.lang,
            country=args.country,
            location=args.location,
            market=args.market,
            safe_search=args.safe,
            device=args.device,
            no_cache=args.no_cache,
            max_results=args.max_results
        )

        if args.json:
            output_data = {
                'query': args.query,
                'page': args.page,
                'lang': args.lang,
                'country': args.country,
                'total_results': len(results),
                'results': results
            }
            if args.pretty:
                print(json.dumps(output_data, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(output_data, ensure_ascii=False))
        else:
            print(client.format_results(results, args.query))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
