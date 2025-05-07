import os
import csv
import json
import time
from dotenv import load_dotenv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.riot_helpers import get_timeline_data

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}

def main():
    # CSV source
    matches_path = os.path.join(os.path.dirname(__file__), '..','..', 'data', 'midlane_matches.csv')
    output_dir = os.path.join(os.path.dirname(__file__), '..','..', 'data', 'timelines')
    os.makedirs(output_dir, exist_ok=True)

    with open(matches_path, newline='', encoding='utf-8') as csvfile:
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
            timeline = get_timeline_data(match_id)
            if timeline:
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    json.dump(timeline, f, indent=2)
                print(f"✅ Saved: {output_filename}")

            time.sleep(1.5)  # Respect Riot API rate limits

if __name__ == '__main__':
    main()
