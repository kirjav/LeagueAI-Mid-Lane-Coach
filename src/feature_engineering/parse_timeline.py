import os
import json
import csv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.riot_helpers import normalize_summoner
from utils.feature_extract_helper import is_boots, calculate_kda


def extract_features(timeline_json, match_id, summoner, participant_id, opp_participant_id=None):
    info = timeline_json['info']
    frames = info['frames']
    events = [e for frame in frames for e in frame['events']]

    features = {
        'summoner': normalize_summoner(summoner),
        'match_id': match_id,
        'champion': None,
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
        'has_early_lane_prio': False
    }

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
    features['kda'] = calculate_kda(kills, assists, deaths)
    features['opp_kda'] = calculate_kda(opp_kills, opp_assists, opp_deaths)

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



def main():
    input_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'timelines')
    match_info_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'midlane_matches.csv')
    output_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'parsed_timeline_features.csv')

    with open(match_info_path, newline='', encoding='utf-8') as f:
        match_info_list = list(csv.DictReader(f))

    results = []

    for match_info in match_info_list:
        summoner = match_info['summoner']
        match_id = match_info['match_id']
        participant_id = int(match_info.get('participant_id', -1))
        opp_participant_id = int(match_info.get('opp_participant_id', -1)) if match_info.get('opp_participant_id') else None

        filename = f"{summoner.replace(' ', '_').replace('#', '-') }__{match_id}_timeline.json"
        filepath = os.path.join(input_dir, filename)
        if not os.path.exists(filepath):
            print(f"❌ Missing timeline file for match: {filename}")
            continue

        with open(filepath, newline='', encoding='utf-8') as f:
            timeline = json.load(f)

        features = extract_features(timeline, match_id, summoner, participant_id, opp_participant_id)
        if features:
            results.append(features)

    fieldnames = results[0].keys() if results else []
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Parsed {len(results)} timelines → saved to {output_file}")

if __name__ == '__main__':
    main()
