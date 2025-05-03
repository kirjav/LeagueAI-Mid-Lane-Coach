import os
import csv
import requests
import openpyxl

# Your Riot API key and headers
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}

def get_match_info(match_id):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"Failed to get match {match_id}: {res.status_code}")
        return None
    info = res.json()['info']
    return {
        'match_id': match_id,
        'game_duration': info.get('gameDuration'),
        'start_time': info.get('gameStartTimestamp'),
        'queue_id': info.get('queueId'),
        'platform': info.get('platformId')
    }

def main():
    replays_dir = os.path.join(os.path.dirname(__file__), '..', 'replays')
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'replay_match_info.xlsx')

    # Set up Excel sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['match_id', 'game_duration', 'start_time', 'queue_id', 'platform'])

    # Process each .rofl file
    for filename in os.listdir(replays_dir):
        if filename.endswith('.rofl'):
            match_id = filename.replace('.rofl', '').replace('-', '_')
            match_info = get_match_info(match_id)
            if match_info:
                ws.append([
                    match_info['match_id'],
                    match_info['game_duration'],
                    match_info['start_time'],
                    match_info['queue_id'],
                    match_info['platform']
                ])

    # Save Excel file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)
    print(f"\n✅ Saved replay match info to {output_path}")

if __name__ == '__main__':
    main()
