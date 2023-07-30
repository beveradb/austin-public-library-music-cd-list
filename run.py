#!/usr/bin/env python3
import os
import csv
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


CACHE_FOLDER = "cache"
MAX_PAGES_TO_FETCH = 10  # Set the maximum number of pages to fetch in a single run


def get_json_data(url):
    try:
        # Create the cache folder if it doesn't exist
        if not os.path.exists(CACHE_FOLDER):
            os.makedirs(CACHE_FOLDER)

        # Check if the cached file exists for the given URL
        cached_file_path = os.path.join(CACHE_FOLDER, url.replace("/", "_") + ".json")
        if os.path.exists(cached_file_path):
            with open(cached_file_path, "r") as cached_file:
                json_data = cached_file.read()
            print("JSON data loaded from cache.")
        else:
            response = requests.get(url)
            response.raise_for_status()  # Check if the request was successful
            soup = BeautifulSoup(response.content, "html.parser")
            script_tags = soup.find_all(
                "script", {"type": "application/json", "data-iso-key": "_0"}
            )
            if script_tags:
                json_data = script_tags[0].string.strip()
                # Cache the JSON data to a file
                with open(cached_file_path, "w") as cached_file:
                    cached_file.write(json_data)
                print("JSON data fetched and cached.")
            else:
                print("JSON data not found in the HTML.")
                return None
    except requests.exceptions.RequestException as e:
        print("Error fetching HTML:", e)
        return None
    except Exception as e:
        print("Error parsing HTML:", e)
        return None

    return json_data


def write_metadata_to_csv(cd_metadata_list):
    fields = [
        "ID",
        "Artist",
        "Title",
        "UPC Barcode",
        "Date",
        "Language",
    ]  # Add more fields as needed
    csv_file_path = "cd_metadata.csv"
    with open(csv_file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        for cd_metadata in cd_metadata_list:
            # Extract the UPC barcode from the jacket URL
            jacket_url = cd_metadata.get("Jacket", {}).get("medium", "")
            upc = ""
            if jacket_url:
                upc = parse_qs(urlparse(jacket_url).query).get("upc", [""])[0]

            # Write the CD metadata to the CSV row
            writer.writerow(
                {
                    "ID": cd_metadata.get("ID", ""),
                    "Artist": cd_metadata.get("Artist", ""),
                    "Title": cd_metadata.get("Title", ""),
                    "UPC Barcode": upc,
                    "Date": cd_metadata.get("Date", ""),
                    "Language": cd_metadata.get("Language", ""),
                }
            )


def parse_json_and_extract_metadata(json_data):
    cd_metadata_list = []

    try:
        # Step 1: Parse the JSON data
        data = json.loads(json_data)

        # Step 2: Access the relevant section
        bibs_data = data.get("entities", {}).get("bibs", {})

        # Step 3: Iterate through each CD
        for cd_id, cd_info in bibs_data.items():
            try:
                # Step 4: Extract artist and title
                brief_info = cd_info.get("briefInfo", {})

                # Default to Unknown Artist if the 'authors' list is empty
                artist = "Unknown Artist"
                artists = brief_info.get("authors")
                if len(artists) > 0:
                    artist = artists[0]

                title = brief_info.get("title", "")

                # Step 5: Extract additional metadata fields
                metadata_id = cd_info.get("id", "")
                publication_date = brief_info.get("publicationDate", "")
                primary_language = brief_info.get("primaryLanguage", "")

                # Step 6: Store metadata in a list of dictionaries
                cd_metadata = {
                    "ID": metadata_id,
                    "Artist": artist,
                    "Title": title,
                    "UPC Barcode": "",
                    "Date": publication_date,
                    "Language": primary_language,
                    "Jacket": brief_info.get("jacket", {}),
                }
                cd_metadata_list.append(cd_metadata)
            except Exception as e:
                print(f"Error processing CD with ID '{cd_id}':", e)

    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
    except Exception as e:
        print("An error occurred while processing CD data:", e)

    return cd_metadata_list


def fetch_all_cd_metadata():
    base_url = "https://austin.bibliocommons.com/v2/search"
    query_params = {
        "custom_edit": "false",
        "query": "formatcode:(MUSIC_CD)",
        "searchType": "bl",
        "suppress": "true",
        "f_CIRC": "CIRC",
        "sort": "newly_acquired",
    }

    all_cd_metadata = []

    for page in range(1, MAX_PAGES_TO_FETCH + 1):
        query_params["page"] = page
        url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"

        json_data = get_json_data(url)

        if json_data:
            cd_metadata_list = parse_json_and_extract_metadata(json_data)

            all_cd_metadata.extend(cd_metadata_list)
        else:
            print("Failed to fetch JSON search results.")

    if all_cd_metadata:
        write_metadata_to_csv(all_cd_metadata)
        print("All CD metadata fetched and CSV file written.")
    else:
        print("Unable to fetch CD metadata.")


fetch_all_cd_metadata()
