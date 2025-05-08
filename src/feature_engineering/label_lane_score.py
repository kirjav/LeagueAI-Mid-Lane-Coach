import os
import pandas as pd

def calculate_lane_score(trend_5_to_10, trend_10_to_15):
    """
    Score is based on gold advantage growth or decline in early lane phase.
    0 = disastrous trend (heavy gold loss), 100 = dominant trend (heavy gold gain).
    """
    if pd.isna(trend_5_to_10) or pd.isna(trend_10_to_15):
        return None

    total_trend = trend_5_to_10 + trend_10_to_15
    score = max(-1500, min(total_trend, 1500))  # clip extreme trends
    scaled = round(((score + 1500) / 3000) * 100, 2)

    return scaled

def main():
    base_dir = os.path.dirname(__file__)
    input_path = os.path.join(base_dir, '..','..', 'data', 'cleaned_data.csv')
    output_path = os.path.join(base_dir, '..','..', 'data', 'labeled_data.csv')

    df = pd.read_csv(input_path)

    if not {'gold_diff_trend_5_to_10', 'gold_diff_trend_10_to_15'}.issubset(df.columns):
        print("❌ Required trend columns not found in cleaned_data.csv")
        return

    df['lane_score'] = df.apply(
        lambda row: calculate_lane_score(
            row['gold_diff_trend_5_to_10'],
            row['gold_diff_trend_10_to_15']
        ),
        axis=1
    )

    df = df[df['lane_score'].notna()]
    df.to_csv(output_path, index=False)
    print(f"✅ Labeled data with lane_score saved to {output_path}")

if __name__ == '__main__':
    main()
