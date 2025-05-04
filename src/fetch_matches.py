import requests
import time
import csv
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}
REGION = 'na1'
ROUTING = 'americas'



def get_puuid_by_riot_id(game_name, tag_line):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"Error getting Riot ID {game_name}#{tag_line}: {res.status_code}")
        return None
    return res.json()['puuid']

def get_match_ids(puuid, count=50):
    url = f'https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start=0&count={count}'
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"Error fetching match IDs for PUUID: {res.status_code}")
        return []
    return res.json()

def get_match_info(match_id, riot_id_full):
    url = f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        print(f"Error fetching match {match_id}: {res.status_code}")
        return None

    data = res.json()
    info = data['info']
    participants = info['participants']

    if "#" not in riot_id_full:
        print(f"Invalid Riot ID format passed: {riot_id_full}")
        return None

    game_name, tag_line = riot_id_full.split("#")

    your_player = None
    for p in participants:
        if (
            p.get('riotIdGameName', '').lower() == game_name.lower()
            and p.get('riotIdTagline', '').lower() == tag_line.lower()
        ):
            your_player = p
            break

    if not your_player:
        print(f"Summoner {riot_id_full} not found in match {match_id}")
        return None

    if your_player.get('teamPosition') != 'MIDDLE':
        return None

    your_team_id = your_player['teamId']

    enemy_mid = next(
        (p for p in participants if p['teamPosition'] == 'MIDDLE' and p['teamId'] != your_team_id),
        None
    )

    return {
        'match_id': match_id,
        'champion': your_player['championName'],
        'win': your_player['win'],
        'kills': your_player['kills'],
        'deaths': your_player['deaths'],
        'assists': your_player['assists'],
        'cs': your_player['totalMinionsKilled'] + your_player['neutralMinionsKilled'],
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
    file_path = os.path.join(base_dir, 'summoners.txt')
    with open(file_path) as f:
        summoners = [line.strip() for line in f if line.strip()]

    results = []

    for riot_id in summoners:
        if "#" not in riot_id:
            print(f"Invalid Riot ID format: {riot_id} — should be like 'Faker#KR'")
            continue

        game_name, tag_line = [part.strip() for part in riot_id.split("#")]
        print(f"\nLooking up: {game_name}#{tag_line}")

        puuid = get_puuid_by_riot_id(game_name, tag_line)
        if not puuid:
            continue

        match_ids = get_match_ids(puuid, count=50)
        time.sleep(1)  # Prevent rate limit

        for match_id in match_ids:
            match_info = get_match_info(match_id, f"{game_name}#{tag_line}")
            if match_info:
                results.append({
                    'summoner': f"{game_name}#{tag_line}",
                    **match_info
                })
            time.sleep(1.2)  # Be gentle with Riot API

    # Save to CSV
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'midlane_matches.csv')
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = [
    'summoner', 'match_id', 'champion', 'win',
    'kills', 'deaths', 'assists', 'cs', 'duration', 'timestamp',
    'opp_champion', 'opp_kills', 'opp_deaths', 'opp_cs'
]

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    
if __name__ == '__main__':
    main()




