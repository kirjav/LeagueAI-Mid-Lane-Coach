import numpy as np
import pandas as pd

def suggest_target_value(model, feature_name, current_value, target_score=80, value_range=None, step=5):
    """
    Suggest a better value for a single feature to achieve a higher lane score.

    Parameters:
    - model: The trained feature model (regressor).
    - feature_name: str, the name of the feature (must match model input).
    - current_value: float/int, the player's value for that feature.
    - target_score: int/float, desired lane score (default 80).
    - value_range: tuple(min, max) of values to search through. If None, uses (0, 1000).
    - step: how fine-grained the value search should be.

    Returns:
    - best_value (float) if improvement found, else None
    """
    if value_range is None:
        value_range = (0, 1000)

    test_values = np.arange(value_range[0], value_range[1], step)
    df = pd.DataFrame({feature_name: test_values})
    preds = model.predict(df)

    # Find best prediction near target
    best_idx = np.argmin(np.abs(preds - target_score))
    best_value = test_values[best_idx]

    if preds[best_idx] > model.predict(pd.DataFrame([{feature_name: current_value}])[model.feature_names_in_])[0] and not np.isclose(best_value, current_value):
        return best_value
    return None
