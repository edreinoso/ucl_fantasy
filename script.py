import http.client
import boto3
import requests
import json
import csv
import logging
import time
from notion import Notion
from botocore.exceptions import NoCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Skill mapping
skill_map = {
    1: "goal keepers",
    2: "defenders",
    3: "midfielders",
    4: "attackers"
}


def get_uefa_players_data():
    start_time = time.time()
    logging.info("Fetching players data from UEFA.")
    conn = http.client.HTTPSConnection("gaming.uefa.com")
    conn.request("GET", "/en/uclfantasy/services/feeds/players/players_70_en_6.json")
    res = conn.getresponse()
    data = res.read()
    data = json.loads(data.decode("utf-8"))
    
    cleaned_player_data = []

    for player in data['data']['value']['playerList']:
        # Transform the skill number to its description
        skill_description = skill_map.get(data.get('skill', 0), 'unknown')

        cleaned_player_data.append({
            'name': player.get('pDName', ''),
            'rating': player.get('rating', ''),
            'value': player.get('value', ''),
            'total points': player.get('totPts', ''),
            'goals': player.get('gS', ''),
            'assist': player.get('assist', ''),
            'minutes played': player.get('minsPlyd', ''),
            'average points': player.get('avgPlayerPts', ''),
            'isActive': player.get('isActive', ''),
            'team': player.get('cCode', ''),
            'man of match': player.get('mOM', ''),
            'position': skill_description,
            'goals conceded': player.get('gC'),
            'yellow cards': player.get('yC'),
            'red cards': player.get('rC'),
            'penalties earned': player.get('pE'),
            'balls recovered': player.get('bR'),
        })
    
    end_time = time.time()
    logging.info(f"UEFA players data fetched and cleaned in {end_time - start_time:.2f} seconds.")
    
    return cleaned_player_data

def csv_table(player_data):
    # Write to a CSV file
    csv_file_path = 'players3.csv'

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'rating', 'value', 'total points', 'goals', 'assist', 'minutes played', 'average points', 'isActive', 'team', 'man of match', 'position', 'goals conceded', 'yellow cards', 'red cards', 'penalties earned', 'balls recovered']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for player in player_data:
            writer.writerow(player)

    print("CSV file created successfully.")

def write_to_json_file(file_path, data):
    # Write to JSON file with readable Unicode characters
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Existing entries written to {file_path}.")
    except Exception as e:
        logging.error(f"Error writing to file: {e}")

def download_file_from_s3(bucket_name, s3_file_key, local_file_path):
    session = boto3.Session(profile_name='ed')
    s3 = session.client('s3')
    try:
        s3.download_file(bucket_name, s3_file_key, local_file_path)
        logging.info(f"File downloaded from S3 bucket.")
    except NoCredentialsError:
        logging.error("Credentials not available.")
    except Exception as e:
        logging.error(f"Error downloading file from S3: {e}")

if __name__ == "__main__":
    notion = Notion(requests=requests, logging=logging, time=time)

    # Download existing_entries.json from S3
    bucket_name = 'ucl-fantasy-data'
    s3_file_key = 'existing_entries.json'
    local_file_path = 'existing_entries.json'
    download_file_from_s3(bucket_name, s3_file_key, local_file_path)
    
    uefa_players_data  = get_uefa_players_data()
    # existing_entries = get_notion_existing_entries()
    
    # Writing data to a JSON file
    # existing_entries = notion.get_notion_existing_entries()
    # write_to_json_file("existing_entries.json", existing_entries)

    # Reading data from JSON file
    with open(local_file_path, "r") as f:
        existing_entries = json.load(f)

    notion.update_notion_entries(uefa_players_data, existing_entries)
