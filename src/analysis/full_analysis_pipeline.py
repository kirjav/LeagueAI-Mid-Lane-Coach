import os
import pandas as pd
import joblib
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analysis.generate_single_match_row import main as generate_match_row
from analysis.predict_lane_score import main as predict_lane_score
from analysis.analyze_lane_score import analyze_features_and_feedback as analyze_features_and_feedback

def full_analysis_pipeline(game_id: str, server: str, summoner: str):
    print("📥 Step 1: Generating single match row...")
    generate_match_row(game_id, server, summoner)

    print("\n📊 Step 2: Predicting lane score...")
    predict_lane_score()

    prediction, feedback = analyze_features_and_feedback()

    return {
        "lane_score": prediction,
        "feedback": feedback
    }

#if __name__ == "__main__":
    # Example input and output
    # result = full_analysis_pipeline("5282972169", "NA1", "Wallaby#Rito")
    # print(result)