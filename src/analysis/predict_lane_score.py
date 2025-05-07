import os
import pandas as pd
import joblib

def main():
    # Adjust this if you're executing from a different directory
    base_dir = os.path.dirname(__file__)
    model_path = os.path.join(base_dir, '..', '..', 'models', 'lane_score_model.pkl')
    encoder_path = os.path.join(base_dir, '..', '..', 'models', 'champion_role_encoder.pkl')
    input_row_path = os.path.join(base_dir, '..', '..', 'data', 'single_match_row.csv')

    # Load trained model and encoder
    model = joblib.load(model_path)
    encoder = joblib.load(encoder_path)

    # Load single match row
    df = pd.read_csv(input_row_path)

    # One-hot encode champion_role
    if 'champion_role' in df.columns:
        encoded = encoder.transform(df[['champion_role']])
        encoded_df = pd.DataFrame(encoded, columns=encoder.get_feature_names_out(['champion_role']))
        df = pd.concat([df.reset_index(drop=True), encoded_df], axis=1)
        df.drop(columns=['champion_role'], inplace=True)

    # Ensure all required features are present
    model_features = model.feature_names_in_
    for col in model_features:
        if col not in df.columns:
            df[col] = 0  # fill missing columns with 0
    df = df[model_features]

    # Predict and print result
    lane_score = model.predict(df)[0]
    print(f"🧠 Predicted Lane Score: {lane_score:.2f} (out of 100)")

if __name__ == '__main__':
    main()
