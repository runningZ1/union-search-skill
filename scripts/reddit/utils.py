import csv
import json
import logging
import os
from urllib.parse import urlparse

import requests
from pygments import formatters, highlight, lexers

logging.basicConfig(
    level=logging.INFO, filename="YARS.log", format="%(asctime)s - %(message)s"
)


def display_results(results, title):
    try:
        print(f"\n{'-'*20} {title} {'-'*20}")

        if isinstance(results, (list, dict)):
            items = results if isinstance(results, list) else [results]
            for item in items:
                if isinstance(item, dict):
                    formatted_json = json.dumps(item, sort_keys=True, indent=4)
                    colorful_json = highlight(
                        formatted_json,
                        lexers.JsonLexer(),
                        formatters.TerminalFormatter(),
                    )
                    print(colorful_json)
                else:
                    print(item)
        else:
            logging.warning(
                "No results to display: expected a list or dictionary, got %s",
                type(results),
            )
            print("No results to display.")

    except Exception as e:
        logging.error("Error displaying results: %s", e)
        print("Error displaying results.")


def download_image(image_url, output_folder="images", session=None):
    os.makedirs(output_folder, exist_ok=True)

    filename = os.path.basename(urlparse(image_url).path)
    filepath = os.path.join(output_folder, filename)

    if session is None:
        session = requests.Session()

    try:
        response = session.get(image_url, stream=True)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        logging.info("Downloaded: %s", filepath)
        return filepath
    except requests.RequestException as e:
        logging.error("Failed to download %s: %s", image_url, e)
        return None
    except Exception as e:
        logging.error("An error occurred while saving the image: %s", e)
        return None


def export_to_json(data, filename="output.json"):
    try:
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully exported to {filename}")
    except Exception as e:
        print(f"Error exporting to JSON: {e}")


def export_to_csv(data, filename="output.csv"):
    if not data:
        print("Error: No data to export")
        return

    try:
        keys = data[0].keys()
        with open(filename, "w", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        print(f"Data successfully exported to {filename}")
    except Exception as e:
        print(f"Error exporting to CSV: {e}")