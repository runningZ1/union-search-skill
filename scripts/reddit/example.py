import json
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, "src")
sys.path.append(src_path)

from yars.utils import display_results, download_image
from yars.yars import YARS

miner = YARS()
DEFAULT_FILENAME = "subreddit_data3.json"


def display_data(miner, subreddit_name, limit=5):
    search_results = miner.search_reddit("OpenAI", limit=3)
    display_results(search_results, "SEARCH")

    permalink = "/r/getdisciplined/comments/1frb5ib/what_single_health_test_or_practice_has/"
    post_details = miner.scrape_post_details(permalink)
    if post_details:
        display_results(post_details, "POST DATA")
    else:
        print("Failed to scrape post details.")

    user_data = miner.scrape_user_data("iamsecb", limit=2)
    display_results(user_data, "USER DATA")

    subreddit_posts = miner.fetch_subreddit_posts(
        subreddit_name, limit=limit, category="new", time_filter="week"
    )
    display_results(subreddit_posts, "SUBREDDIT Top Posts")

    for idx, post in enumerate(subreddit_posts[:3]):
        try:
            image_url = post.get("image_url", post.get("thumbnail_url", ""))
            if image_url:
                download_image(image_url)
        except Exception as e:
            print(f"Error downloading image from post {idx}: {e}")


def load_existing_data(filename):
    try:
        with open(filename, "r") as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_to_json(data, filename):
    try:
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data to JSON file: {e}")


def scrape_subreddit_data(subreddit_name, limit=5, filename=DEFAULT_FILENAME):
    try:
        subreddit_posts = miner.fetch_subreddit_posts(
            subreddit_name, limit=limit, category="top", time_filter="all"
        )

        existing_data = load_existing_data(filename)

        for i, post in enumerate(subreddit_posts, 1):
            permalink = post["permalink"]
            post_details = miner.scrape_post_details(permalink)
            print(f"Processing post {i}")

            if post_details:
                post_data = {
                    "title": post.get("title", ""),
                    "author": post.get("author", ""),
                    "created_utc": post.get("created_utc", ""),
                    "num_comments": post.get("num_comments", 0),
                    "score": post.get("score", 0),
                    "permalink": post.get("permalink", ""),
                    "image_url": post.get("image_url", ""),
                    "thumbnail_url": post.get("thumbnail_url", ""),
                    "body": post_details.get("body", ""),
                    "comments": post_details.get("comments", []),
                }

                existing_data.append(post_data)
                save_to_json(existing_data, filename)
            else:
                print(f"Failed to scrape details for post: {post['title']}")

    except Exception as e:
        print(f"Error occurred while scraping subreddit: {e}")


if __name__ == "__main__":
    subreddit_name = "wbjee"

    display_data(miner, subreddit_name, limit=3)
    scrape_subreddit_data(subreddit_name, limit=3)
