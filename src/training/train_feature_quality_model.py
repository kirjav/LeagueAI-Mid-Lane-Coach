import os
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

def train_stat_quality_model(
    data_path,
    feature_name,
    output_model_path,
    label_column='lane_score',
    quality_threshold=60,
    test_size=0.2,
    model_cls=LogisticRegression
):
    """
    Trains a classifier that determines if a given stat is "good" or "bad" for lane performance.

    Parameters:
    - data_path (str): Path to the CSV file with full feature data.
    - feature_name (str): The column name of the stat to train the model on (e.g. 'first_ward_time').
    - output_model_path (str): Where to save the trained model.
    - label_column (str): Column used to determine good vs. bad performance (default: 'lane_score').
    - quality_threshold (int): Threshold on lane_score to classify stat as good (1) or bad (0).
    - test_size (float): Fraction of data to use for testing.
    - model_cls (sklearn model): Classifier class to use (default: LogisticRegression).
    """
    df = pd.read_csv(data_path)

    if feature_name not in df.columns or label_column not in df.columns:
        raise ValueError(f"Missing required column: {feature_name} or {label_column}")

    df = df[[feature_name, label_column]].dropna()
    df['is_good'] = (df[label_column] >= quality_threshold).astype(int)

    X = df[[feature_name]]
    y = df['is_good']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)

    model = model_cls()
    model.fit(X_train, y_train)

    print(f"\n📊 Evaluation for '{feature_name}'")
    print(classification_report(y_test, model.predict(X_test)))

    joblib.dump(model, output_model_path)
    print(f"✅ Model saved to: {output_model_path}")
