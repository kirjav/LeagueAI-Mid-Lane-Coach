import subprocess
import os

base_dir = os.path.dirname(__file__)
script_dir = os.path.join(base_dir, 'src')

steps = [
    ("fetch_matches.py", "📥 Fetching match data"),
    ("fetch_timelines.py", "🧠 Fetching timeline JSONs"),
    ("parse_timeline.py", "📊 Parsing timeline data"),
    ("sync_matches_from_timelines.py", "🔄 Syncing match info from timelines"),
    ("merge_matches_and_timeline.py", "🔗 Merging match + timeline data")
]

print("🚀 Starting League AI Data Pipeline...\n")

for script, description in steps:
    print(f"{description} ({script})")
    script_path = os.path.join(script_dir, script)

    try:
        subprocess.run(["python", script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ {script} failed. Exiting pipeline.")
        break
    except FileNotFoundError:
        print(f"❌ Script not found: {script_path}")
        break
    else:
        print(f"✅ {script} completed\n")

print("\n🏁 Pipeline complete!")
