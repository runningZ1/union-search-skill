
import json
import os
import time
from datetime import datetime

def format_timestamp(ts):
    """Convert unix timestamp to human-readable string."""
    if not ts:
        return "N/A"
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return str(ts)

def extract_tags(aweme):
    """Extract hashtags from aweme object."""
    tags = []
    # Method 1: From text_extra
    text_extra = aweme.get("text_extra") or []
    for entry in text_extra:
        if isinstance(entry, dict):
            tag = entry.get("hashtag_name") or entry.get("hash_tag_name")
            if tag:
                tags.append(f"#{tag}")
    
    # Method 2: If none in text_extra, try regex on desc (fallback)
    if not tags:
        desc = aweme.get("desc") or ""
        import re
        tags = re.findall(r'#([^\s#]+)', desc)
        tags = [f"#{t}" for t in tags]
        
    return list(set(tags))  # Deduplicate

def parse_aweme(aweme, search_keyword):
    """Extract required fields from a single aweme (video) object."""
    if not aweme:
        return None
    
    stats = aweme.get("statistics") or {}
    author = aweme.get("author") or {}
    
    return {
        "search_keyword": search_keyword,
        "video_info": {
            "aweme_id": aweme.get("aweme_id"),
            "title": (aweme.get("desc") or "").strip(),
            "tags": extract_tags(aweme),
            "publish_time": format_timestamp(aweme.get("create_time")),
        },
        "interaction_data": {
            "like_count": stats.get("digg_count", 0),
            "comment_count": stats.get("comment_count", 0),
            "share_count": stats.get("share_count", 0),
            "forward_count": stats.get("forward_count", 0),
            "play_count": stats.get("play_count", 0),
            "collect_count": stats.get("collect_count", 0)
        },
        "author_info": {
            "author_id": author.get("uid"),
            "author_sec_id": author.get("sec_uid"),
            "nickname": author.get("nickname")
        },
        "media_info": {
            "play_urls": (aweme.get("video") or {}).get("play_addr", {}).get("url_list", []),
            "cover_urls": (aweme.get("video") or {}).get("cover", {}).get("url_list", []),
            "dynamic_cover_urls": (aweme.get("video") or {}).get("dynamic_cover", {}).get("url_list", [])
        }
    }

def filter_douyin_response(input_path, output_path=None):
    """
    Load Douyin search response, filter core information, and optionally save to file.
    Designed for production use with error handling.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in input file: {e}")

    # 1. Extract search keyword
    search_keyword = raw_data.get("params", {}).get("keyword", "N/A")
    
    # 2. Navigate to data items
    # Structure: root -> data -> data (list)
    inner_data = raw_data.get("data")
    if not isinstance(inner_data, dict):
        return []
    
    items = inner_data.get("data")
    if not isinstance(items, list):
        return []

    filtered_results = []
    
    # 3. Process each item (card)
    for item in items:
        if not isinstance(item, dict):
            continue
            
        # Case A: Direct video info
        if "aweme_info" in item:
            processed = parse_aweme(item["aweme_info"], search_keyword)
            if processed:
                filtered_results.append(processed)
        
        # Case B: List of videos (e.g. user card or mixed card)
        if "aweme_list" in item:
            aweme_list = item["aweme_list"]
            if isinstance(aweme_list, list):
                for aweme in aweme_list:
                    processed = parse_aweme(aweme, search_keyword)
                    if processed:
                        filtered_results.append(processed)

    # 4. Save to output if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_results, f, ensure_ascii=False, indent=2)
            
    return filtered_results

if __name__ == "__main__":
    # Example usage for the specific file
    INPUT_FILE = r'c:\Users\zijie\.claude\skills\union-search-skill\scripts\douyin\responses\20260219_121906_douyin_search_v3.json'
    OUTPUT_FILE = r'c:\Users\zijie\.claude\skills\union-search-skill\scripts\douyin\responses\filtered_summary.json'
    
    try:
        results = filter_douyin_response(INPUT_FILE, OUTPUT_FILE)
        print(f"Success! Processed {len(results)} videos.")
        print(f"Filtered results saved to: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error processing file: {e}")
