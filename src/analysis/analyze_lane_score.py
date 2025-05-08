import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt
import json
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from feature_engineering.lane_features import FEATURES_TO_TRAIN
from utils.feature_feedback import suggest_target_value

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

        prediction = model.predict(formatted_input)[0]
        ftype = feature_types.get(feature, "numeric")
        category = categorize_feature(feature)

        if prediction >= 0.5:
            if ftype != "boolean":
                categorized_feedback[category].append(
                    f"✅ `{feature}` was strong ({value}). Keep it up!"
                )
            continue

        if ftype == "boolean":
            if not value:
                categorized_feedback[category].append(
                    f"❗ Consider taking action related to `{feature}` earlier or more often."
                )
        else:
            suggested = suggest_target_value(model, feature, value)
            if suggested:
                categorized_feedback[category].append(
                    f"❗ Improve `{feature}` — try aiming for **{suggested:.1f}** (you had {value})."
                )
            else:
                categorized_feedback[category].append(
                    f"❗ Consider optimizing `{feature}` — your value ({value}) underperformed."
                )

    return categorized_feedback


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

    print("\n📋 Feedback on specific features:")
    feedback_by_category = give_feature_feedback(df.iloc[0], feature_models, feature_types)

    print("\n📋 Detailed Feedback by Category:")
    for category, items in feedback_by_category.items():
        if items:
            print(f"\n{category}:")
            for line in items:
                print(f"- {line}")


if __name__ == "__main__":
    main()