import os
import csv

def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def write_csv(path, fieldnames, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def calculate_kda(kills, assists, deaths):
    return round((int(kills) + int(assists)) / max(1, int(deaths)), 2)

def main():
    base_dir = os.path.dirname(__file__)
    match_path = os.path.join(base_dir, '..', 'data', 'midlane_matches.csv')
    timeline_path = os.path.join(base_dir, '..', 'data', 'parsed_timeline_features.csv')
    output_path = os.path.join(base_dir, '..', 'data', 'merged_data.csv')

    matches = read_csv(match_path)
    timelines = read_csv(timeline_path)

    timeline_index = {
        row['match_id']: row for row in timelines
    }

    merged_rows = []

    for match in matches:
        match_id = match['match_id']
        timeline = timeline_index.get(match_id)

        if not timeline:
            print(f"⚠️ Timeline data not found for match {match_id}")
            continue

        combined = {**match, **timeline}
        merged_rows.append(combined)

    if merged_rows:
        # 🧹 Remove any row with missing or invalid participant ID
            # 🧹 Remove rows where opponent's participant ID is missing or invalid
        merged_rows = [
        row for row in merged_rows
        if row.get('opp_participant_id') not in [None, '', '-1']]

        fieldnames = merged_rows[0].keys()
        write_csv(output_path, fieldnames, merged_rows)
        print(f"✅ Merged {len(merged_rows)} rows → {output_path}")
    else:
        print("❌ No data merged. Check CSV consistency.")


if __name__ == '__main__':
    main()
