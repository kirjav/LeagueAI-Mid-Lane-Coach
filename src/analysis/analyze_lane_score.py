import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt
import json
import sys
import streamlit as st
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from feature_engineering.lane_features import FEATURES_TO_TRAIN
from utils.feature_feedback import suggest_target_value

   
def clampBoolean(n): 
    if n < 0: 
        return 0
    elif n > 1: 
        return 1
    else: 
        return n 
    
def is_value_reasonable_for_model(model, feature, value, suggested, full_row=None):
    try:
        test_df = pd.DataFrame([full_row])  # use full row
        test_df = format_input_to_match_model(test_df, model.feature_names_in_)

        test_df_value = test_df.copy()
        test_df_value[feature] = value
        pred_value = model.predict(test_df_value)[0]

        test_df_suggested = test_df.copy()
        test_df_suggested[feature] = suggested
        pred_ideal = model.predict(test_df_suggested)[0]

        st.sidebar.write(f"[DEBUG] {feature} → value={value}, suggested={suggested}, pred_value={pred_value:.2f}, pred_ideal={pred_ideal:.2f}")

        if pred_ideal >= 0.5 and pred_value < 0.5:
            return False
        return True
    except Exception as e:
        st.sidebar.write(f"[ERROR] {feature}: {e}")
        return None
    
def categorize_feature(feature):
    if feature in ['first_ward_time', 'first_item_after_4min_time', 'boots_purchase_time']:
        return "📍 Early Game"
    elif feature in ['cs_diff_at_10', 'gold_diff_at_5', 'gold_diff_trend_5_to_10', 'avg_cs_per_min', 'fight_impact_score']:
        return "🔄 Laning Phase"
    elif feature in ['gold_diff_at_10', 'gold_diff_at_15', 'gold_diff_trend_10_to_15', 'first_teamfight_join_time']:
        return "📈 Mid Game"
    else:
        return "🎯 Strategy"

def load_model_and_features(model_path):
    model = joblib.load(model_path)
    expected_features = model.feature_names_in_
    return model, expected_features

def format_input_to_match_model(df, expected_features):
    for col in expected_features:
        if col not in df.columns:
            df[col] = 0
    df = df[expected_features]
    return df

def load_feature_types():
    path = os.path.join("models", "feature_types.json")
    with open(path, 'r') as f:
        return json.load(f)

def load_feature_models():
    models = {}
    for feature in FEATURES_TO_TRAIN:
        path = os.path.join("models", "feature_quality", f"{feature}_quality_model.pkl")
        if os.path.exists(path):
            models[feature] = joblib.load(path)
    return models

def give_feature_feedback(row, feature_models, feature_types):
    categorized_feedback = {
        "📍 Early Game": [],
        "🔄 Laning Phase": [],
        "📈 Mid Game": [],
        "🎯 Strategy": []
    }

    for feature, model in feature_models.items():
        value = row[feature]
        if pd.isnull(value):
            continue

        formatted_input = pd.DataFrame([{feature: value}])
        formatted_input = format_input_to_match_model(formatted_input, model.feature_names_in_)

        probability = model.predict_proba(formatted_input)[0][1]  # Probability of class 1 (good)

        ftype = feature_types.get(feature, "numeric")
        category = categorize_feature(feature)
        suggested = suggest_target_value(model, feature, value)
        if probability >= 0.7:  # use a more confident threshold
            if ftype != "boolean":
                diff = abs(value - suggested)
                if suggested != 0 and (diff / abs(suggested)) <= 0.1:
                    categorized_feedback[category].append(
                        f"✅ `{feature}` was strong ({value:.1f}). Keep it up! Ideal value: `{suggested:.1f}`"
                    )
                else:
                    categorized_feedback[category].append(
                        f"⚠️ `{feature}` helped overall, but `{value:.1f}` could be closer to ideal `{suggested:.1f}`."
                    )
            continue


        if ftype == "boolean":
            suggested = clampBoolean(suggested)
            if bool(value) != bool(suggested):
                categorized_feedback[category].append(
                    f"❗ Consider taking action related to `{feature}` earlier or more often. Your value: `{bool(value)}`. Intended: `{bool(suggested)}`"
                )
            else:
                categorized_feedback[category].append(
                f"✅ `{feature}` was correctly handled (`{bool(value)}`). Keep doing that!"
            )
                
        else:
            if suggested is not None:
                try:
                    diff = abs(value - suggested)
                    if suggested != 0 and (diff / abs(suggested)) <= 0.1:
                        categorized_feedback[category].append(
                            f"✅ `{feature}` was close to ideal — you had {value:.1f}, target is {suggested:.1f}. Nice!"
                        )
                    else:
                        categorized_feedback[category].append(
                            f"❗ Improve `{feature}` — try aiming for **{suggested:.1f}** (you had {value:.1f})."
                        )
                except Exception as e:
                    categorized_feedback[category].append(
                        f"❗ Consider optimizing `{feature}` — your value ({value}) underperformed."
                    )
            else:
                categorized_feedback[category].append(
                    f"❗ Consider optimizing `{feature}` — your value ({value}) underperformed."
                )
    return categorized_feedback

def analyze_features_and_feedback():
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, '..','..', 'models', 'lane_score_model.pkl')
    data_path = os.path.join(base_dir, '..','..', 'data', 'single_match_row.csv')

    df = pd.read_csv(data_path)
    model, expected_features = load_model_and_features(model_path)
    formatted_df = format_input_to_match_model(df.copy(), expected_features)
    prediction = model.predict(formatted_df)[0]
    #print(f"\n🎯 Predicted lane score: {prediction:.2f}")

    feature_models = load_feature_models()
    feature_types = load_feature_types()

    feedback_by_category = give_feature_feedback(df.iloc[0], feature_models, feature_types)

    return prediction, feedback_by_category


def main():
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, '..','..', 'models', 'lane_score_model.pkl')
    data_path = os.path.join(base_dir, '..','..', 'data', 'single_match_row.csv')

    df = pd.read_csv(data_path)
    model, expected_features = load_model_and_features(model_path)
    formatted_df = format_input_to_match_model(df.copy(), expected_features)
    prediction = model.predict(formatted_df)[0]
    print(f"\n🎯 Predicted lane score: {prediction:.2f}")

    if prediction >= 80:
        print("🟢 You dominated lane! Strong gold control and pressure.")
    elif prediction >= 60:
        print("🟢 Solid lane. Minor improvements could turn this into domination.")
    elif prediction >= 40:
        print("🟡 Lane was close. Look into key turning points or mistakes.")
    elif prediction >= 20:
        print("🔴 You lost lane. Identify where you gave up gold advantage.")
    else:
        print("🔴 Severe lane loss. Likely early deaths or missed CS lead to a snowball.")

    feature_models = load_feature_models()
    feature_types = load_feature_types()

    feedback_by_category = give_feature_feedback(df.iloc[0], feature_models, feature_types)

    print("\n📋 Detailed Feedback by Category:")
    for category, items in feedback_by_category.items():
        if items:
            print(f"\n{category}:")
            for line in items:
                print(f"- {line}")


if __name__ == "__main__":
    main()