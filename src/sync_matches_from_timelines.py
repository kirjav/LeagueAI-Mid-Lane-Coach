import os
import csv
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}
MATCH_URL = "https://americas.api.riotgames.com/lol/match/v5/matches/{}"

def load_existing_matches(path):
    with open(path, newline='') as f:
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

def get_match_info(match_id, riot_id_full, max_retries=3):
    url = MATCH_URL.format(match_id)

    for attempt in range(max_retries):
        res = requests.get(url, headers=HEADERS)

        if res.status_code == 200:
            break
        elif res.status_code == 429:
            retry_after = int(res.headers.get("Retry-After", "10"))
            print(f"⏳ Rate limited. Retrying in {retry_after} seconds...")
            time.sleep(retry_after)
        else:
            print(f"⚠️ Failed to fetch match {match_id}: {res.status_code}")
            return None
    else:
        print(f"❌ Failed after {max_retries} retries for match {match_id}")
        return None

    data = res.json()
    info = data['info']
    participants = info['participants']

    if "#" not in riot_id_full:
        return None

    game_name, tag_line = riot_id_full.split("#")

    your_player = next(
        (p for p in participants
         if p.get('riotIdGameName', '').lower() == game_name.lower()
         and p.get('riotIdTagline', '').lower() == tag_line.lower()), None)

    if not your_player or your_player.get('teamPosition') != 'MIDDLE':
        return None

    team_id = your_player['teamId']
    enemy_mid = next(
        (p for p in participants if p['teamPosition'] == 'MIDDLE' and p['teamId'] != team_id),
        None
    )

    return {
        'summoner': riot_id_full,
        'match_id': match_id,
        'champion': your_player['championName'],
        'win': your_player['win'],
        'kills': your_player['kills'],
        'deaths': your_player['deaths'],
        'assists': your_player['assists'],
        'cs': your_player['totalMinionsKilled'] + your_player['neutralMinionsKilled'],
        'duration': info['gameDuration'],
        'timestamp': info['gameStartTimestamp'],
        'opp_champion': enemy_mid['championName'] if enemy_mid else None,
        'opp_kills': enemy_mid['kills'] if enemy_mid else None,
        'opp_deaths': enemy_mid['deaths'] if enemy_mid else None,
        'opp_cs': (
            enemy_mid['totalMinionsKilled'] + enemy_mid['neutralMinionsKilled']
            if enemy_mid else None
        )
    }

def main():
    base_dir = os.path.dirname(__file__)
    match_path = os.path.join(base_dir, '..', 'data', 'midlane_matches.csv')
    timeline_dir = os.path.join(base_dir, '..', 'data', 'timelines')

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
            print(f"Existing match info found {match_id} for {summoner}. Moving onto next match")
            continue

        print(f"🔍 Syncing new match {match_id} for {summoner}")
        match_info = get_match_info(match_id, summoner)
        if match_info:
            new_rows.append(match_info)
            time.sleep(1.5)

    # Final deduplication and write
    combined = matches + new_rows
    deduped = {(r['summoner'], r['match_id']): r for r in combined}
    deduped_rows = list(deduped.values())

    if deduped_rows:
        with open(match_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=deduped_rows[0].keys())
            writer.writeheader()
            writer.writerows(deduped_rows)
        print(f"✅ Synced and deduplicated {len(deduped_rows)} matches total")
    else:
        print("✅ No new data added — all timeline matches already covered.")

if __name__ == '__main__':
    main()
