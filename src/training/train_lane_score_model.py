import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

def main():
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, '..', '..', 'data', 'labeled_data.csv')
    model_path = os.path.join(base_dir, '..', '..', 'models', 'lane_score_model.pkl')

    # Load data
    df = pd.read_csv(input_path)

    # Drop rows without lane_score
    df = df[df['lane_score'].notna()]

    # Define features and target
    features = df.drop(columns=['lane_score', 'summoner', 'match_id', 'champion', 'opp_champion', 'opp_summoner'])
    target = df['lane_score']

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate model
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"✅ Model trained! MSE: {mse:.2f}, R²: {r2:.2f}")

    # Save model
    joblib.dump(model, model_path)
    print(f"🧠 Model saved to: {model_path}")

if __name__ == '__main__':
    main()
