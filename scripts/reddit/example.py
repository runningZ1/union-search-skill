import json
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, "src")
sys.path.append(src_path)

from yars.yars import YARS
from yars.utils import display_results, download_image

# Initialize the YARS Reddit miner
miner = YARS()
filename = "subreddit_data3.json"


# Function to display search results, subreddit posts, and user data
def display_data(miner, subreddit_name, limit=5):
    search_results = miner.search_reddit("OpenAI", limit=3)
    display_results(search_results, "SEARCH")

    # Scrape post details for a specific permalink
    permalink = "https://www.reddit.com/r/getdisciplined/comments/1frb5ib/what_single_health_test_or_practice_has/".split(
        "reddit.com"
    )[
        1
    ]
    post_details = miner.scrape_post_details(permalink)
    if post_details:
        display_results(post_details, "POST DATA")
    else:
        print("Failed to scrape post details.")

    # Scrape user data
    user_data = miner.scrape_user_data("iamsecb", limit=2)
    display_results(user_data, "USER DATA")

    # Scrape top posts from a subreddit
    subreddit_posts = miner.fetch_subreddit_posts(
        subreddit_name, limit=limit, category="new", time_filter="week"
    )
    display_results(subreddit_posts, "SUBREDDIT Top Posts")

    # Attempt to download images from the first few posts
    for idx, post in enumerate(subreddit_posts[:3]):
        try:
            image_url = post.get("image_url", post.get("thumbnail_url", ""))
            if image_url:
                download_image(image_url)
        except Exception as e:
            print(f"Error downloading image from post {idx}: {e}")


# Function to scrape subreddit post details and comments and save to JSON
def scrape_subreddit_data(subreddit_name, limit=5, filename=filename):
    try:
        subreddit_posts = miner.fetch_subreddit_posts(
            subreddit_name, limit=limit, category="top", time_filter="all"
        )

        # Load existing data from the JSON file, if available
        try:
            with open(filename, "r") as json_file:
                existing_data = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        # Scrape details and comments for each post
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

                # Append new post data to existing data
                existing_data.append(post_data)

                # Save the data incrementally to the JSON file
                save_to_json(existing_data, filename)
            else:
                print(f"Failed to scrape details for post: {post['title']}")

    except Exception as e:
        print(f"Error occurred while scraping subreddit: {e}")


# Function to save post data to a JSON file
def save_to_json(data, filename=filename):
    try:
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving data to JSON file: {e}")


# Main execution
if __name__ == "__main__":
    subreddit_name = "wbjee"

    # Display data for various functionalities
    display_data(miner, subreddit_name, limit=3)

    # Scrape and save subreddit post data to JSON
    scrape_subreddit_data(subreddit_name, limit=3)
