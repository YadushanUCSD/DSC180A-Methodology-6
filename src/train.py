"""Train baseline and ML models, write reports/metrics.json.

Run: python -m src.train
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error

from src.config import METRICS, PROCESSED, TARGET
from src.features import build_features, feature_columns


def temporal_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split by date: train = 2011, valid = H1 2012, test = H2 2012.

    Do not shuffle or stratify — this is time series data.
    """
    train = df[df.dteday <= "2011-12-31"].copy()
    valid = df[(df.dteday > "2011-12-31") & (df.dteday <= "2012-06-30")].copy()
    test = df[df.dteday > "2012-06-30"].copy()
    return train, valid, test


# Pre-create unfitted models as per the interface contract.
# Each value is an object with fit(X, y) and predict(X), where X is a DataFrame.
MODELS = {
    "baseline_mean": None,
    "baseline_persistence": None,
    "ridge": Ridge(),
    "hgb": HistGradientBoostingRegressor(),
}


def _evaluate(pred, true):
    """Compute R² and MAE."""
    return {"r2": float(r2_score(true, pred)), "mae": float(mean_absolute_error(true, pred))}


def main():
    # Load features (assumes make features has run)
    feats = pd.read_parquet(PROCESSED)

    # Temporal split: train = 2011, valid = H1 2012, test = H2 2012
    train, valid, test = temporal_split(feats)

    # Feature matrix
    cols = feature_columns(feats)
    X_train, y_train = train[cols], train[TARGET]
    X_valid, y_valid = valid[cols], valid[TARGET]
    X_test, y_test = test[cols], test[TARGET]

    results = {}

    # --- Baseline mean ---------------------------------------------------------
    mean_pred_valid = np.full(len(y_valid), y_train.mean())
    mean_pred_test = np.full(len(y_test), y_train.mean())

    MODELS["baseline_mean"] = {
        "fit": lambda X, y: None,
        "predict": lambda X: np.full(len(X), y_train.mean()),
    }
    result = _evaluate(mean_pred_valid, y_valid)
    valid_r2, valid_mae = result["r2"], result["mae"]
    result = _evaluate(mean_pred_test, y_test)
    test_r2, test_mae = result["r2"], result["mae"]
    results["baseline_mean"] = {
        "valid": {"r2": valid_r2, "mae": valid_mae},
        "test": {"r2": test_r2, "mae": test_mae},
    }

    # --- Persistence baseline (yesterday's count) -----------------------------
    pers_pred_valid = valid[cols]["cnt_lag_1"]
    pers_pred_test = test[cols]["cnt_lag_1"]

    MODELS["baseline_persistence"] = {
        "fit": lambda X, y: None,
        "predict": lambda X: X[cols]["cnt_lag_1"],
    }
    result = _evaluate(pers_pred_valid, y_valid)
    valid_r2, valid_mae = result["r2"], result["mae"]
    result = _evaluate(pers_pred_test, y_test)
    test_r2, test_mae = result["r2"], result["mae"]
    results["baseline_persistence"] = {
        "valid": {"r2": valid_r2, "mae": valid_mae},
        "test": {"r2": test_r2, "mae": test_mae},
    }

    # --- Ridge -----------------------------------------------------------------
    ridge = MODELS["ridge"]
    ridge.fit(X_train, y_train)
    valid_pred = ridge.predict(X_valid)
    test_pred = ridge.predict(X_test)
    result = _evaluate(valid_pred, y_valid)
    valid_r2, valid_mae = result["r2"], result["mae"]
    result = _evaluate(test_pred, y_test)
    test_r2, test_mae = result["r2"], result["mae"]
    results["ridge"] = {"valid": {"r2": valid_r2, "mae": valid_mae}, "test": {"r2": test_r2, "mae": test_mae}}

    # --- Gradient boosting ------------------------------------------------------
    hgb = MODELS["hgb"]
    hgb.fit(X_train, y_train)
    valid_pred = hgb.predict(X_valid)
    test_pred = hgb.predict(X_test)
    result = _evaluate(valid_pred, y_valid)
    valid_r2, valid_mae = result["r2"], result["mae"]
    result = _evaluate(test_pred, y_test)
    test_r2, test_mae = result["r2"], result["mae"]
    results["hgb"] = {"valid": {"r2": valid_r2, "mae": valid_mae}, "test": {"r2": test_r2, "mae": test_mae}}

    # Write results
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS, "w") as f:
        json.dump(results, f, indent=2)

    print(f"OK trained 4 models on {len(feats)} rows ({len(cols)} features)")
    print("  OK baseline_mean: fit=lambda X,y:... predict=lambda X:...")
    print("  OK baseline_persistence: fit=lambda X,y:... predict=lambda X:...")
    print(f"  OK ridge: R²_valid={results['ridge']['valid']['r2']:.3f}, R²_test={results['ridge']['test']['r2']:.3f}")
    print(f"  OK hgb: R²_valid={results['hgb']['valid']['r2']:.3f}, R²_test={results['hgb']['test']['r2']:.3f}")


if __name__ == "__main__":
    main()
