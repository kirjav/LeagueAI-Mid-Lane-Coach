import os
import csv
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}

def get_timeline(match_id):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Failed: {match_id} — Status code {response.status_code}")
        return None

def main():
    # CSV source
    matches_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'midlane_matches.csv')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'timelines')
    os.makedirs(output_dir, exist_ok=True)

    with open(matches_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            match_id = row['match_id']
            summoner = row['summoner'].replace(" ", "_").replace("#", "-")  # clean file-safe name

            output_filename = f"{summoner}__{match_id}_timeline.json"
            output_path = os.path.join(output_dir, output_filename)

            if os.path.exists(output_path):
                print(f"⏩ Skipping (already downloaded): {output_filename}")
                continue

            print(f"🔎 Fetching: {output_filename}")
            timeline = get_timeline(match_id)
            if timeline:
                with open(output_path, 'w') as f:
                    json.dump(timeline, f, indent=2)
                print(f"✅ Saved: {output_filename}")

            time.sleep(1.5)  # Respect Riot API rate limits

if __name__ == '__main__':
    main()
