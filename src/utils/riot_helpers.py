import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}
ROUTING = 'americas'

def get_match_data(match_id):
    url = f"https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else None

def get_timeline_data(match_id):
    url = f"https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else None

def normalize_summoner(s):
    s = s.replace('_', ' ')
    return s.replace('-', '#') if '#' not in s and '-' in s else s

def extract_participants(info, riot_id):
    game_name, tag_line = riot_id.split("#")

    # Step 1: Try to find the summoner
    this_player = next(
        (p for p in info['participants']
         if p.get('riotIdGameName', '').lower() == game_name.lower()
         and p.get('riotIdTagline', '').lower() == tag_line.lower()),
        None
    )

    opponent = None

    if this_player:
        player_team = this_player.get('teamId')
        player_lane = this_player.get('lane', None)

        # Step 2: Try to find an opponent with same lane
        if player_lane and player_lane != "NONE":
            opponent = next(
                (p for p in info['participants']
                 if p.get('teamId') != player_team
                 and p.get('lane') == player_lane),
                None
            )

        # Step 3: Fallback — pick any enemy player if lane match fails
        if not opponent:
            opponent = next(
                (p for p in info['participants']
                 if p.get('teamId') != player_team),
                None
            )

    return this_player, opponent


