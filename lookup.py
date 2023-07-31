#!/usr/bin/env python3
import os
import csv
import time
import requests

# Input and output CSV file paths
INPUT_CSV_FILE = "cd_metadata_output_2023-07-30.csv"
OUTPUT_CSV_FILE = "cd_metadata_with_redacted_results.csv"

# Limit number of rows to process (for testing) - set to None to process all rows
ROW_PROCESS_LIMIT = 1


def lookup_cd_on_redacted(artist, title, api_token, base_url, limit=5):
    url = base_url
    params = {
        "action": "browse",
        "artistname": artist,
        "groupname": title,
        "format": "FLAC",
        "media": "CD",
    }
    headers = {
        "Authorization": api_token,
    }

    try:
        print(f"Querying URL: {url} with params: {params} and headers: {headers}")
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Check if the request was successful

        # Introduce a 2-second delay after each API call to ensure we don't exceed the API rate limit
        time.sleep(2)

        # Parse the API response and extract the number of results
        json_data = response.json()
        num_results = len(json_data["response"]["results"])

        # Limit the number of results to the specified limit
        num_results = min(num_results, limit)
        return num_results
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Redacted for {artist} - {title}:", e)
        return None
    except Exception as e:
        print(f"Error parsing data from Redacted for {artist} - {title}:", e)
        return None


def main():
    api_token = os.getenv("REDACTED_API_TOKEN")
    base_url = os.getenv("REDACTED_API_BASE_URL")

    if not api_token:
        print("REDACTED_API_TOKEN environment variable is not set.")
        return

    if not base_url:
        print("REDACTED_API_BASE_URL environment variable is not set.")
        return

    with open(INPUT_CSV_FILE, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    if ROW_PROCESS_LIMIT:
        rows = rows[:ROW_PROCESS_LIMIT]

    for i, row in enumerate(rows, start=1):
        artist = row["Artist"]
        title = row["Title"]

        # Lookup CD on Redacted and get the number of results
        num_results = lookup_cd_on_redacted(artist, title, api_token, base_url)

        # Add the number of results to the row
        row["Redacted Torrent Results"] = num_results

        print(f"Processed CD {i}/{len(rows)}")

    with open(OUTPUT_CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Redacted torrent results added to the CSV.")


if __name__ == "__main__":
    main()
