import subprocess
import os

base_dir = os.path.dirname(__file__)

steps = [
    ("data_collection/fetch_matches.py", "📥 Fetching match data"),
    ("data_collection/fetch_timelines.py", "🧠 Fetching timeline JSONs"),
    ("feature_engineering/parse_timeline.py", "📊 Parsing timeline data"),
    ("data_collection/sync_matches_from_timelines.py", "🔄 Syncing match info from timelines"),
    ("feature_engineering/merge_matches_and_timeline.py", "🔗 Merging match + timeline data"),
    ("feature_engineering/clean_data.py", "🧹 Cleaning merged dataset")
]

print("🚀 Starting League AI Data Pipeline...\n")

for rel_path, description in steps:
    script_path = os.path.join(base_dir, rel_path)

    print(f"{description} ({rel_path})")

    try:
        subprocess.run(["python", script_path], check=True)
    except subprocess.CalledProcessError:
        print(f"❌ {rel_path} failed. Exiting pipeline.")
        break
    except FileNotFoundError:
        print(f"❌ Script not found: {script_path}")
        break
    else:
        print(f"✅ {rel_path} completed\n")

print("\n🏁 Pipeline complete!")
