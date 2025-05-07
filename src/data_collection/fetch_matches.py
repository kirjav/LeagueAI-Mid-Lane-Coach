import os
import csv
import time
import requests
from dotenv import load_dotenv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}
REGION = 'na1'
ROUTING = 'americas'


def get_puuid_by_riot_id(game_name, tag_line):
    url = f"https://{ROUTING}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"❌ Error getting Riot ID {game_name}#{tag_line}: {res.status_code}")
        return None
    return res.json()['puuid']


def get_match_ids(puuid, count=50):
    url = f'https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count={count}'
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"❌ Error fetching match IDs for PUUID: {res.status_code}")
        return []
    return res.json()


def get_match_info(match_id, riot_id_full):
    url = f'https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}'
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        print(f"❌ Error fetching match {match_id}: {res.status_code}")
        return None

    data = res.json()
    info = data['info']
    participants = info['participants']

    if "#" not in riot_id_full:
        print(f"❌ Invalid Riot ID format: {riot_id_full}")
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
                return None  # Skip if not a mid lane game
            this_player = p
            break

    if not this_player:
        print(f"❌ Summoner {riot_id_full} not found in match {match_id}")
        return None

    for p in participants:
        if p['lane'] == 'MIDDLE' and p['teamId'] != this_player['teamId']:
            opponent_mid = p
            break

    opp_riot_id = (
        f"{opponent_mid.get('riotIdGameName')}#{opponent_mid.get('riotIdTagline')}"
        if opponent_mid else None
    )

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
    file_path = os.path.join(base_dir, 'summoners.txt')
    output_path = os.path.join(base_dir, '..', '..', 'data', 'midlane_matches.csv')

    with open(file_path) as f:
        summoners = [line.strip() for line in f if line.strip()]

    results = []

    for riot_id in summoners:
        if "#" not in riot_id:
            print(f"⚠️ Invalid Riot ID format: {riot_id}")
            continue

        game_name, tag_line = riot_id.split("#")
        print(f"\n🔍 Looking up: {game_name}#{tag_line}")

        puuid = get_puuid_by_riot_id(game_name, tag_line)
        if not puuid:
            continue

        match_ids = get_match_ids(puuid, count=50)
        time.sleep(1)

        for match_id in match_ids:
            match_info = get_match_info(match_id, riot_id)
            if match_info:
                results.append({'summoner': riot_id, **match_info})
            time.sleep(1.2)

    fieldnames = [
        'summoner', 'match_id', 'champion', 'participant_id', 'opp_participant_id', 'win',
        'kills', 'deaths', 'assists', 'cs', 'duration',
        'opp_kills', 'opp_deaths', 'opp_assists', 'opp_cs',
        'opp_champion', 'opp_summoner'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Saved {len(results)} matches to {output_path}")


if __name__ == '__main__':
    main()

