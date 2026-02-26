# Jina AI Search Module

This module provides a production-ready interface for the Jina AI Search (Reader) API.

## Features
- Clean class-based API wrapper.
- Automatic result saving to the `responses/` directory.
- Error handling and status logging.
- Support for API keys via environment variables.

## Usage

### As a Library
```python
from jina_search import JinaSearch

client = JinaSearch(api_key="your_key_here")
results = client.search("Python programming", save_to_file=True)

for item in results.get('data', []):
    print(item['title'], item['url'])
```

### From CLI
```bash
python scripts/jina/jina_search.py "Your search query"
```

## Configuration
Set the `JINA_API_KEY` environment variable to use your own API key.
