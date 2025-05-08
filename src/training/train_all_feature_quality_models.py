import os
from train_feature_quality_model import train_stat_quality_model
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from feature_engineering.lane_features import FEATURES_TO_TRAIN

def main():
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, '..', '..', 'data', 'labeled_data.csv')
    output_dir = os.path.join(base_dir, '..', '..', 'models', 'feature_quality')
    os.makedirs(output_dir, exist_ok=True)

    features_to_train = FEATURES_TO_TRAIN

    for feature in features_to_train:
        model_path = os.path.join(output_dir, f'{feature}_quality_model.pkl')
        try:
            train_stat_quality_model(
                data_path=data_path,
                feature_name=feature,
                output_model_path=model_path
            )
        except Exception as e:
            print(f"❌ Failed to train model for {feature}: {e}")

if __name__ == '__main__':
    main()
