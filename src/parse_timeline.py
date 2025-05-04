import os
import json
import csv

def normalize_summoner(s):
    return s.replace('-', '#') if '#' not in s and '-' in s else s

def is_boots(item_id):
    return item_id in {
        1001, 3006, 3009, 3020, 3047, 3111, 3117, 3158
    }

def extract_features(timeline_json, match_id, summoner):
    info = timeline_json['info']
    frames = info['frames']
    events = [e for frame in frames for e in frame['events']]
    participants = info['participants']

    participant_id = participants[0]['participantId']  # placeholder (map via PUUID later)

    # Pre-fill feature dictionary
    features = {
        'summoner': normalize_summoner(summoner),
        'match_id': match_id,
        'champion': None,
        'cs_at_10min': None,
        'first_ward_time': None,
        'first_death_time': None,
        'first_kill_or_assist_time': None,
        'first_item_after_4min_id': None,
        'first_item_after_4min_time': None,
        'boots_purchase_time': None,
        'first_teamfight_join_time': None,
        'fight_impact_score': 0,
        'avg_cs_per_min': None,
        'game_length_minutes': None
    }

    # Estimate duration from final frame
    if frames:
        game_duration = frames[-1]['timestamp'] / 1000  # seconds
        features['game_length_minutes'] = round(game_duration / 60, 2)


    final_cs = 0

    for frame in frames:
        if frame['timestamp'] >= 600000 and not features['cs_at_10min']:
            pf = frame['participantFrames'].get(str(participant_id))
            if pf:
                cs = pf.get('minionsKilled', 0) + pf.get('jungleMinionsKilled', 0)
                features['cs_at_10min'] = cs
        # Also collect final frame CS
        if frame == frames[-1]:
            pf = frame['participantFrames'].get(str(participant_id))
            if pf:
                final_cs = pf.get('minionsKilled', 0) + pf.get('jungleMinionsKilled', 0)

    if game_duration > 0:
        features['avg_cs_per_min'] = round(final_cs / (game_duration / 60), 2)

    for event in events:
        t = event['timestamp'] / 1000

        # Ward
        if event['type'] == 'WARD_PLACED' and event.get('creatorId') == participant_id and not features['first_ward_time']:
            features['first_ward_time'] = t

        # Kills & Deaths
        if event['type'] == 'CHAMPION_KILL':
            if event.get('victimId') == participant_id:
                
                if not features['first_death_time']:
                    features['first_death_time'] = t
            if event.get('killerId') == participant_id:
                
                if not features['first_kill_or_assist_time']:
                    features['first_kill_or_assist_time'] = t
                if not features['first_teamfight_join_time'] and len(event.get('assistingParticipantIds', [])) >= 2:
                    features['first_teamfight_join_time'] = t
                if t <= 900:
                    features['fight_impact_score'] += 1
            elif participant_id in event.get('assistingParticipantIds', []):
                if not features['first_kill_or_assist_time']:
                    features['first_kill_or_assist_time'] = t
                if not features['first_teamfight_join_time'] and len(event.get('assistingParticipantIds', [])) >= 2:
                    features['first_teamfight_join_time'] = t
                if t <= 900:
                    features['fight_impact_score'] += 1

        # Items
        if event['type'] == 'ITEM_PURCHASED' and event.get('participantId') == participant_id:
            item_id = event.get('itemId')
            if t > 240 and not features['first_item_after_4min_id']:
                features['first_item_after_4min_id'] = item_id
                features['first_item_after_4min_time'] = t
            if is_boots(item_id) and not features['boots_purchase_time']:
                features['boots_purchase_time'] = t

    return features

def main():
    input_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'timelines')
    output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'parsed_timeline_features.csv')

    results = []

    for filename in os.listdir(input_dir):
        if filename.endswith('_timeline.json'):
            try:
                summoner, match_id = filename.replace('_timeline.json', '').split('__')
            except ValueError:
                print(f"❌ Skipping malformed filename: {filename}")
                continue

            with open(os.path.join(input_dir, filename)) as f:
                timeline = json.load(f)

            features = extract_features(timeline, match_id, summoner)
            results.append(features)

    # Write CSV
    fieldnames = results[0].keys() if results else []
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Parsed {len(results)} timelines → saved to {output_file}")

if __name__ == '__main__':
    main()
