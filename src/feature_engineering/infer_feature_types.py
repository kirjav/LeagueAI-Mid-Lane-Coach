import pandas as pd
import os
import json
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from feature_engineering.lane_features import FEATURES_TO_TRAIN

def main():
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, '..', '..', 'data', 'cleaned_data.csv')
    output_path = os.path.join(base_dir, '..', '..', 'models', 'feature_types.json')

    df = pd.read_csv(input_path)

    feature_types = {}
    for feature in FEATURES_TO_TRAIN:
        if pd.api.types.is_numeric_dtype(df[feature]):
            feature_types[feature] = 'numeric'
        elif pd.api.types.is_bool_dtype(df[feature]):
            feature_types[feature] = 'boolean'
        else:
            feature_types[feature] = 'other'

    with open(output_path, 'w') as f:
        json.dump(feature_types, f, indent=2)

    print(f"✅ Saved feature types to {output_path}")

if __name__ == '__main__':
    main()
