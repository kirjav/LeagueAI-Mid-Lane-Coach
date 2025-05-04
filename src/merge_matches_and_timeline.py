import os
import csv

def read_csv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))

def write_csv(path, fieldnames, rows):
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    base_dir = os.path.dirname(__file__)
    match_path = os.path.join(base_dir, '..', 'data', 'midlane_matches.csv')
    timeline_path = os.path.join(base_dir, '..', 'data', 'parsed_timeline_features.csv')
    output_path = os.path.join(base_dir, '..', 'data', 'merged_data.csv')

    matches = read_csv(match_path)
    timelines = read_csv(timeline_path)

    # ✅ Index timelines by match_id only
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

        # ✅ Merge match + timeline row
        combined = {**match, **timeline}
        merged_rows.append(combined)

    if merged_rows:
        fieldnames = merged_rows[0].keys()
        write_csv(output_path, fieldnames, merged_rows)
        print(f"✅ Merged {len(merged_rows)} rows → {output_path}")
    else:
        print("❌ No data merged. Check CSV consistency.")

if __name__ == '__main__':
    main()
