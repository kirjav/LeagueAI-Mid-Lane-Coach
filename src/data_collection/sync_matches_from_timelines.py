import os
import csv
import time
import requests
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.riot_helpers import normalize_summoner

from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}
MATCH_URL = "https://americas.api.riotgames.com/lol/match/v5/matches/{}"

def safe_request(url, headers=None, retries=3, timeout=10):
    for attempt in range(retries):
        try:
            res = requests.get(url, headers=headers, timeout=timeout)
            res.raise_for_status()
            return res
        except requests.exceptions.Timeout:
            print(f"⏳ Timeout on {url} (attempt {attempt + 1}/{retries})")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            break  # Don't retry on permanent failures like 403/404
        time.sleep(2)
    return None

def load_existing_matches(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def extract_keys_from_filename(filename):
    try:
        base = filename.replace('_timeline.json', '')
        summoner, match_id = base.split('__')
        return summoner, match_id
    except:
        return None, None

def match_exists(summoner, match_id, rows):
    return (summoner, match_id) in {(r['summoner'], r['match_id']) for r in rows}

from requests.exceptions import ChunkedEncodingError

def get_match_info(match_id, riot_id_full, max_retries=3):
    url = f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'

    res = safe_request(url, headers=HEADERS)
    if not res:
        return None

    data = res.json()
    info = data['info']
    participants = info['participants']

    if "#" not in riot_id_full:
        print(f"Invalid Riot ID format passed: {riot_id_full}")
        return None

    game_name, tag_line = riot_id_full.split("#")
    this_player = None
    opponent_mid = None

    for p in participants:
        if (
            p.get('riotIdGameName', '').lower() == game_name.lower() and
            p.get('riotIdTagline', '').lower() == tag_line.lower()
        ):
            if p['lane'] != 'MIDDLE':
                return None
            this_player = p
            break

    if not this_player:
        print(f"Summoner {riot_id_full} not found in match {match_id}")
        return None

    for p in participants:
        if p['lane'] == 'MIDDLE' and p['teamId'] != this_player['teamId']:
            opponent_mid = p
            break

    opp_riot_id = f"{opponent_mid.get('riotIdGameName')}#{opponent_mid.get('riotIdTagline')}" if opponent_mid else None

    return {
        'match_id': match_id,
        'champion': this_player['championName'],
        'participant_id': this_player['participantId'],
        'opp_participant_id': opponent_mid['participantId'] if opponent_mid else None,
        'win': this_player['win'],
        'kills': this_player['kills'],
        'deaths': this_player['deaths'],
        'assists': this_player['assists'],
        'cs': this_player['totalMinionsKilled'] + this_player['neutralMinionsKilled'],
        'duration': info['gameDuration'],
        'opp_kills': opponent_mid['kills'] if opponent_mid else 0,
        'opp_deaths': opponent_mid['deaths'] if opponent_mid else 1,
        'opp_assists': opponent_mid['assists'] if opponent_mid else 0,
        'opp_cs': opponent_mid['totalMinionsKilled'] + opponent_mid['neutralMinionsKilled'] if opponent_mid else 0,
        'opp_champion': opponent_mid['championName'] if opponent_mid else '',
        'opp_summoner': opp_riot_id
    }



def main():
    base_dir = os.path.dirname(__file__)
    match_path = os.path.join(base_dir, '..','..', 'data', 'midlane_matches.csv')
    timeline_dir = os.path.join(base_dir, '..','..', 'data', 'timelines')

    matches = load_existing_matches(match_path)
    new_rows = []

    for fname in os.listdir(timeline_dir):
        if not fname.endswith('_timeline.json'):
            continue

        summoner, match_id = extract_keys_from_filename(fname)
        if not summoner or not match_id:
            continue

        # Check in both existing matches and newly added this run
        if match_exists(summoner, match_id, matches + new_rows):
            print(f"🟡 Existing match info found {match_id} for {summoner}. Skipping.")
            continue

        print(f"🔍 Syncing new match {match_id} for {summoner}")
        match_info = get_match_info(match_id, normalize_summoner(summoner))
        if match_info:
            match_info['summoner'] = summoner  # ✅ Ensure summoner is saved in the row
            new_rows.append(match_info)
            time.sleep(1.5)

    # Final deduplication and write
    combined = matches + new_rows
    deduped = {r['match_id']: r for r in combined}
    deduped_rows = list(deduped.values())

    if deduped_rows:
        fieldnames = [
    'summoner', 'match_id', 'champion', 'participant_id', 'opp_participant_id', 'win',
    'kills', 'deaths', 'assists', 'cs', 'duration',
    'opp_kills', 'opp_deaths', 'opp_assists', 'opp_cs', 'opp_champion', 'opp_summoner'
]


        with open(match_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(deduped_rows)

        print(f"✅ Synced and deduplicated {len(deduped_rows)} matches total")
    else:
        print("✅ No new data added — all timeline matches already covered.")

if __name__ == '__main__':
    main()
