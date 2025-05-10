import numpy as np
import pandas as pd

def suggest_target_value(model, feature_name, current_value, target_score=0.8, value_range=None, step=5):
    """
    Suggest a better value for a single feature to achieve a higher chance of being 'good'.
    Works with classifiers using .predict_proba().
    """
    if value_range is None:
        value_range = (0, 1000)

    test_values = np.arange(value_range[0], value_range[1], step)
    df = pd.DataFrame({feature_name: test_values})

    if hasattr(model, "predict_proba"):
        preds = model.predict_proba(df[model.feature_names_in_])[:, 1]  # probability of class 1
    else:
        preds = model.predict(df[model.feature_names_in_])  # fallback for regressors

    best_idx = np.argmin(np.abs(preds - target_score))
    return float(test_values[best_idx])
