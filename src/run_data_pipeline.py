import subprocess
import os

scripts = [
    'fetch_matches.py',
    'fetch_timelines.py',
    'sync_matches_from_timelines.py',
    'parse_timeline.py',
    'merge_matches_and_timeline.py'
]

def main():
    print("🚀 Starting League AI Data Pipeline...\n")

    src_dir = os.path.join(os.path.dirname(__file__), 'src')

    for script in scripts:
        script_path = os.path.join(src_dir, script)
        print(f"🔧 Running {script}...")
        result = subprocess.run(['python', script_path])
        if result.returncode != 0:
            print(f"❌ {script} failed. Exiting pipeline.")
            return

    print("\n✅ All steps completed successfully!")

if __name__ == '__main__':
    main()
