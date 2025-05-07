import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
import json
import time
import pandas as pd
from dotenv import load_dotenv
from sklearn.preprocessing import OneHotEncoder
import joblib

# ✅ Replace with actual path if run independently
from feature_engineering.champion_role_map import champion_role_map

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")
HEADERS = {"X-Riot-Token": API_KEY}
ROUTING = 'americas'

def is_boots(item_id):
    return item_id in {
        1001, 3006, 3009, 3020, 3047, 3111, 3117, 3158
    }
    
def normalize_summoner(s):
    s = s.replace('_', ' ')
    return s.replace('-', '#') if '#' not in s and '-' in s else s

def get_match_data(match_id):
    url = f"https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else None

def get_timeline_data(match_id):
    url = f"https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else None

def extract_participants(info, riot_id):
    game_name, tag_line = riot_id.split("#")
    for p in info['participants']:
        if (p.get('riotIdGameName', '').lower() == game_name.lower() and
            p.get('riotIdTagline', '').lower() == tag_line.lower() and
            p.get('lane') == 'MIDDLE'):
            this_player = p
            break
    else:
        return None, None

    for p in info['participants']:
        if p.get('lane') == 'MIDDLE' and p['teamId'] != this_player['teamId']:
            return this_player, p
    return this_player, None

def extract_features(features, timeline_json, match_id, summoner, participant_id, opp_participant_id=None):
    info = timeline_json['info']
    frames = info['frames']
    events = [e for frame in frames for e in frame['events']]

    if not frames:
        return None

    game_duration = frames[-1]['timestamp'] / 1000
    features['game_length_minutes'] = round(game_duration / 60, 2)

    final_cs = 0
    kills = deaths = assists = 0
    opp_kills = opp_deaths = opp_assists = 0

    for frame in frames:
        pf = frame.get('participantFrames', {}).get(str(participant_id))
        opp_pf = frame.get('participantFrames', {}).get(str(opp_participant_id)) if opp_participant_id else None

        if pf:
            cs = pf.get('minionsKilled', 0) + pf.get('jungleMinionsKilled', 0)
            if frame['timestamp'] >= 600000 and not features['cs_at_10min']:
                features['cs_at_10min'] = cs
            if frame == frames[-1]:
                final_cs = cs

        if opp_pf:
            if frame['timestamp'] >= 600000 and not features['opp_cs_at_10min']:
                features['opp_cs_at_10min'] = opp_pf.get('minionsKilled', 0) + opp_pf.get('jungleMinionsKilled', 0)

    if game_duration > 0:
        features['avg_cs_per_min'] = round(final_cs / (game_duration / 60), 2)

    for event in events:
        t = event['timestamp'] / 1000

        if event['type'] == 'WARD_PLACED' and event.get('creatorId') == participant_id and not features['first_ward_time']:
            features['first_ward_time'] = t

        if event['type'] == 'CHAMPION_KILL':
            if event.get('victimId') == participant_id:
                if not features['first_death_time']:
                    features['first_death_time'] = t
                deaths += 1
            if event.get('killerId') == participant_id:
                if not features['first_kill_or_assist_time']:
                    features['first_kill_or_assist_time'] = t
                if not features['first_teamfight_join_time'] and len(event.get('assistingParticipantIds', [])) >= 2:
                    features['first_teamfight_join_time'] = t
                if t <= 900:
                    features['fight_impact_score'] += 1
                kills += 1
            elif participant_id in event.get('assistingParticipantIds', []):
                if not features['first_kill_or_assist_time']:
                    features['first_kill_or_assist_time'] = t
                if not features['first_teamfight_join_time'] and len(event.get('assistingParticipantIds', [])) >= 2:
                    features['first_teamfight_join_time'] = t
                if t <= 900:
                    features['fight_impact_score'] += 1
                assists += 1

            # Opponent stats
            if event.get('victimId') == opp_participant_id:
                opp_deaths += 1
            if event.get('killerId') == opp_participant_id:
                opp_kills += 1
            elif opp_participant_id in event.get('assistingParticipantIds', []):
                opp_assists += 1

        if event['type'] == 'ITEM_PURCHASED' and event.get('participantId') == participant_id:
            item_id = event.get('itemId')
            if t > 240 and not features['first_item_after_4min_id']:
                features['first_item_after_4min_id'] = item_id
                features['first_item_after_4min_time'] = t
            if is_boots(item_id) and not features['boots_purchase_time']:
                features['boots_purchase_time'] = t

    # Final derived metrics
    features['kda'] = round((kills + assists) / max(1, deaths), 2)
    features['opp_kda'] = round((opp_kills + opp_assists) / max(1, opp_deaths), 2)

    if features['cs_at_10min'] is not None and features['opp_cs_at_10min'] is not None:
        features['cs_diff_at_10'] = features['cs_at_10min'] - features['opp_cs_at_10min']

    # Gold diff at 10 min
    for frame in frames:
        ts = frame['timestamp']
        pf = frame.get('participantFrames', {}).get(str(participant_id))
        opp_pf = frame.get('participantFrames', {}).get(str(opp_participant_id))

        if pf and opp_pf:
            p_gold = pf.get('totalGold', 0)
            opp_gold = opp_pf.get('totalGold', 0)
            diff = p_gold - opp_gold

            if ts >= 300000 and features.get('gold_diff_at_5') is None:
                features['gold_diff_at_5'] = diff
            if ts >= 600000 and features.get('gold_diff_at_10') is None:
                features['gold_diff_at_10'] = diff
            if ts >= 900000 and features.get('gold_diff_at_15') is None:
                features['gold_diff_at_15'] = diff

    if features['gold_diff_at_5'] is not None and features['gold_diff_at_10'] is not None:
        features['gold_diff_trend_5_to_10'] = features['gold_diff_at_10'] - features['gold_diff_at_5']

    if features['gold_diff_at_10'] is not None and features['gold_diff_at_15'] is not None:
        features['gold_diff_trend_10_to_15'] = features['gold_diff_at_15'] - features['gold_diff_at_10']


    # Early roam
    if features['first_teamfight_join_time'] and features['first_teamfight_join_time'] <= 600:
        features['early_roam'] = True

    # Has early lane prio: any two of cs_diff > 10, gold_diff > 300, early roam
    prio_flags = [
        features['cs_diff_at_10'] is not None and features['cs_diff_at_10'] >= 10,
        features['gold_diff_at_10'] is not None and features['gold_diff_at_10'] >= 300,
        features['early_roam']
    ]

    features['has_early_lane_prio'] = prio_flags.count(True) >= 2

    return features

def main(match_number, server, summoner):
    
    match_id = f"{server.upper()}_{match_number}"
    #summoner = normalize_summoner(summoner)
    match_data = get_match_data(match_id)
    timeline_data = get_timeline_data(match_id)

    if not match_data or not timeline_data:
        print("❌ Failed to fetch data from Riot API.")
        return

    info = match_data['info']
    timeline = timeline_data['info']
    this_player, opponent = extract_participants(info, summoner)
    if not this_player:
        print("❌ Summoner not found in match.")
        return

    base_fields = {
        'summoner': summoner,
        'match_id': match_id,
        'champion': this_player['championName'],
        'participant_id': this_player['participantId'],
        'opp_participant_id': opponent['participantId'] if opponent else None,
        'win': this_player['win'],
        'kills': this_player['kills'],
        'deaths': this_player['deaths'],
        'assists': this_player['assists'],
        'cs': this_player['totalMinionsKilled'] + this_player['neutralMinionsKilled'],
        'duration': info['gameDuration'],
        'opp_kills': opponent['kills'] if opponent else 0,
        'opp_deaths': opponent['deaths'] if opponent else 1,
        'opp_assists': opponent['assists'] if opponent else 0,
        'opp_cs': opponent['totalMinionsKilled'] + opponent['neutralMinionsKilled'] if opponent else 0,
        'opp_champion': opponent['championName'] if opponent else '',
        'opp_summoner': f"{opponent['riotIdGameName']}#{opponent['riotIdTagline']}" if opponent else '',
        'cs_at_10min': None,
        'opp_cs_at_10min': None,
        'first_ward_time': None,
        'first_death_time': None,
        'first_kill_or_assist_time': None,
        'first_item_after_4min_id': None,
        'first_item_after_4min_time': None,
        'boots_purchase_time': None,
        'first_teamfight_join_time': None,
        'fight_impact_score': 0,
        'avg_cs_per_min': None,
        'game_length_minutes': None,
        'kda': None,
        'opp_kda': None,
        'cs_diff_at_10': None,
        'gold_diff_at_5': None,
        'gold_diff_at_10': None,
        'gold_diff_at_15': None,
        'gold_diff_trend_5_to_10': None,
        'gold_diff_trend_10_to_15': None,
        'early_roam': False,
        'has_early_lane_prio': False,
    }
    # (features, timeline_json, match_id, summoner, participant_id, opp_participant_id=None):
    features = extract_features(base_fields, timeline_data, match_id, summoner, this_player['participantId'], opponent['participantId'])

    # Combine and encode
    full_row = features
    df = pd.DataFrame([full_row])
    df['champion_role'] = df['champion'].map(champion_role_map)

    encoder = joblib.load(os.path.join("models", "champion_role_encoder.pkl"))
    role_encoded = encoder.transform(df[['champion_role']])
    encoded_df = pd.DataFrame(role_encoded, columns=encoder.get_feature_names_out(['champion_role']))

    final_df = pd.concat([df.drop(columns=['champion_role']).reset_index(drop=True), encoded_df], axis=1)
    
    output_path = os.path.join(os.path.dirname(__file__), '..','..', 'data', 'single_match_row.csv')
    final_df.to_csv(output_path, index=False)
    print(f"✅ Saved single match row to {output_path}")

if __name__ == '__main__':
    main("5282353", "NA1", "Wallaby#Rito")
