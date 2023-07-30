#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup

CACHE_FOLDER = "cache"


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


# Replace this URL with the actual URL you want to fetch
url = "https://austin.bibliocommons.com/v2/search?custom_edit=false&query=formatcode%3A(MUSIC_CD)&searchType=bl&suppress=true&f_CIRC=CIRC&sort=newly_acquired"

json_data = get_json_data(url)

if json_data:
    print("JSON data extracted successfully!")
else:
    print("Unable to fetch JSON data.")
