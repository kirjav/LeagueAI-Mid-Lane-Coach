import os
import json
import csv

# Helper: checks if item is boots
def is_boots(item_id):
    BOOTS_IDS = {
        1001, 3006, 3009, 3020, 3047, 3111, 3117, 3158
    }
    return item_id in BOOTS_IDS

# Main parser function per file
def extract_features(timeline_json, match_id, summoner):
    info = timeline_json['info']
    frames = info['frames']
    events = [e for frame in frames for e in frame['events']]
    participants = info['participants']

    features = {
        'summoner': summoner,
        'match_id': match_id,
        'champion': None,
        'cs_at_10min': None,
        'first_death_time': None,
        'first_kill_or_assist_time': None,
        'first_ward_time': None,
        'first_item_after_4min_id': None,
        'first_item_after_4min_time': None,
        'boots_purchase_time': None,
        'first_teamfight_join_time': None,
        'fight_impact_score': 0
    }

    # Detect participant ID
    # We assume it's always the first one in the list if not mapped (better to map using match metadata later)
    participant_id = participants[0]['participantId']
    features['champion'] = None  # or leave out for now


    # Phase 1: Frame-based (CS at 10 min)
    for frame in frames:
        if frame['timestamp'] >= 600000:
            pframe = frame['participantFrames'].get(str(participant_id))
            if pframe:
                cs = pframe.get('minionsKilled', 0) + pframe.get('jungleMinionsKilled', 0)
                features['cs_at_10min'] = cs
            break

    # Phase 2: Events
    for event in events:
        t = event['timestamp'] / 1000

        # WARD
        if event['type'] == 'WARD_PLACED' and event.get('creatorId') == participant_id and not features['first_ward_time']:
            features['first_ward_time'] = t

        # DEATH
        if event['type'] == 'CHAMPION_KILL':
            if event.get('victimId') == participant_id and not features['first_death_time']:
                features['first_death_time'] = t
            elif (event.get('killerId') == participant_id or
                  participant_id in event.get('assistingParticipantIds', [])):

                if not features['first_kill_or_assist_time']:
                    features['first_kill_or_assist_time'] = t

                # Approximate teamfight if 2+ allies are involved
                if (event.get('assistingParticipantIds') and
                    len(event['assistingParticipantIds']) >= 2):
                    if not features['first_teamfight_join_time']:
                        features['first_teamfight_join_time'] = t

                # Basic impact score: 1 point per kill/assist before 15 min
                if t <= 900:
                    features['fight_impact_score'] += 1

        # ITEMS
        if event['type'] == 'ITEM_PURCHASED' and event.get('participantId') == participant_id:
            item_id = event.get('itemId')

            # First item after 4 min
            if t > 240 and not features['first_item_after_4min_id']:
                features['first_item_after_4min_id'] = item_id
                features['first_item_after_4min_time'] = t

            # Boots
            if is_boots(item_id) and not features['boots_purchase_time']:
                features['boots_purchase_time'] = t

    return features

# Main loop
def main():
    input_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'timelines')
    output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'parsed_timeline_features.csv')

    results = []

    for filename in os.listdir(input_dir):
        if filename.endswith('_timeline.json'):
            # Format: summoner__match_id_timeline.json
            try:
                summoner, match_id = filename.replace('_timeline.json', '').split('__')
            except ValueError:
                print(f"❌ Skipping malformed filename: {filename}")
                continue

            with open(os.path.join(input_dir, filename)) as f:
                timeline = json.load(f)

            features = extract_features(timeline, match_id, summoner)
            results.append(features)

    # Write results to CSV
    fieldnames = list(results[0].keys()) if results else []
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Parsed {len(results)} matches → saved to {output_file}")

if __name__ == '__main__':
    main()
