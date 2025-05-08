import os
import pandas as pd
import joblib
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analysis.generate_single_match_row import main as generate_match_row
from analysis.predict_lane_score import main as predict_lane_score
from analysis.analyze_lane_score import main as analyze_lane_score

def full_analysis_pipeline(game_id: str, server: str, summoner: str):
    print("📥 Step 1: Generating single match row...")
    generate_match_row(game_id, server, summoner)
    predict_lane_score()
    print("\n📊 Step 2: Running prediction and analysis...")
    analyze_lane_score()

if __name__ == "__main__":
    # Example input
    full_analysis_pipeline("5282357783", "NA1", "Wallaby#Rito")
