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
    this_player = next(
        (p for p in info['participants']
         if p.get('riotIdGameName', '').lower() == game_name.lower()
         and p.get('riotIdTagline', '').lower() == tag_line.lower()
         and p.get('lane') == 'MIDDLE'),
        None
    )
    opponent = next(
        (p for p in info['participants']
         if p.get('lane') == 'MIDDLE' and p.get('teamId') != this_player.get('teamId')),
        None
    ) if this_player else None

    return this_player, opponent
