import pandas as pd
import joblib
import os
import shap
import matplotlib.pyplot as plt
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from feature_engineering.lane_features import FEATURES_TO_TRAIN



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

def explain_lane_score_with_shap(model, df):
    explainer = shap.Explainer(model.predict, df)
    shap_values = explainer(df)
    shap.summary_plot(shap_values, df, show=False)
    plt.savefig('analysis/shap_summary_plot.png')
    shap.plots.bar(shap_values, show=False)
    plt.savefig('analysis/shap_bar_plot.png')
    print("✅ SHAP visualizations saved.")

def evaluate_feature_quality(df, feature, model_dir):
    value = df[feature].iloc[0]
    if pd.isna(value):
        return None

    model_path = os.path.join(model_dir, f"{feature}_quality_model.pkl")
    if not os.path.exists(model_path):
        return None

    model = joblib.load(model_path)
    pred = model.predict([[value]])[0]  # Predict returns array
    return "✅ Good" if pred == 1 else "⚠️ Needs improvement"

def main():
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, '..', '..', 'models', 'lane_score_model.pkl')
    feature_model_dir = os.path.join(base_dir, '..', '..', 'models', 'feature_quality')
    data_path = os.path.join(base_dir, '..', '..', 'data', 'single_match_row.csv')

    df = pd.read_csv(data_path)

    model, expected_features = load_model_and_features(model_path)
    formatted_df = format_input_to_match_model(df, expected_features)

    explain_lane_score_with_shap(model, formatted_df)

    prediction = model.predict(formatted_df)[0]
    print(f"🎯 Predicted lane score: {prediction:.2f}")

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

    # Evaluate key features using helper models
    features_to_evaluate = FEATURES_TO_TRAIN

    print("\n📋 Feature Feedback:")
    for feature in features_to_evaluate:
        status = evaluate_feature_quality(df, feature, feature_model_dir)
        if status:
            print(f"- {feature}: {status}")

if __name__ == "__main__":
    main()
