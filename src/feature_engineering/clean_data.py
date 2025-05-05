import os
import sys
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
import joblib

# ✅ Allow direct script execution by adjusting the import path
sys.path.append(os.path.dirname(__file__))
from champion_role_map import champion_role_map

def main():
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, '..', '..', 'data', 'merged_data.csv')
    output_path = os.path.join(base_dir, '..', '..', 'data', 'cleaned_data.csv')
    encoder_path = os.path.join(base_dir, '..', '..', 'models', 'champion_role_encoder.pkl')
    os.makedirs(os.path.join(base_dir, '..', '..', 'models'), exist_ok=True)

    df = pd.read_csv(input_path)

    # Drop rows where opponent participant ID is missing
    df = df[df['opp_participant_id'].notna()]

    # Map champion to role
    df['champion_role'] = df['champion'].map(champion_role_map)
    df = df[df['champion_role'].notna()]

    # One-hot encode champion roles
    encoder = OneHotEncoder(sparse_output=False)
    role_encoded = encoder.fit_transform(df[['champion_role']])
    encoded_df = pd.DataFrame(role_encoded, columns=encoder.get_feature_names_out(['champion_role']))
    df = pd.concat([df.reset_index(drop=True), encoded_df], axis=1)
    df.drop(columns=['champion_role'], inplace=True)

    # Save encoder and cleaned data
    joblib.dump(encoder, encoder_path)
    df.to_csv(output_path, index=False)
    print(f"✅ Cleaned data saved to: {output_path}")
    print(f"✅ Encoder saved to: {encoder_path}")

if __name__ == '__main__':
    main()
