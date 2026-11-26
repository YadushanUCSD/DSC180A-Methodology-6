"""Stage 3: temporal split, fit, evaluate, write metrics.

Two baselines and two models, on purpose.

  baseline_mean         predict the 2011 average for every day
  baseline_persistence  predict yesterday's count (cnt_lag_1)
  ridge                 standardised linear model on the audited features
  hgb                   gradient-boosted trees on the same features

The mean baseline shows what "the distribution moved" costs. Persistence
is the baseline that actually matters: ridge's features are dominated by
lagged demand, so if it cannot beat "yesterday again" it has learned
nothing worth reporting. The booster is there because it fails, and the
reason it fails is the headline result.

Run: python -m src.train

With --target ratio, models are fit on cnt / cnt_roll_7, predictions are
multiplied by cnt_roll_7 and scored against cnt on validation only. The
persistence baseline is not transformed: it already predicts a count.

Run: python -m src.train --target ratio
"""
import argparse
import json

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import (
    METRICS,
    METRICS_RATIO,
    PROCESSED,
    TARGET,
    TRAIN_END,
    VALID_END,
)
from src.features import feature_columns


class PersistenceBaseline(BaseEstimator, RegressorMixin):
    """Predict a single lagged column unchanged. Nothing is fit."""

    def __init__(self, column: str = "cnt_lag_1"):
        self.column = column

    def fit(self, X, y=None):
        if self.column not in X.columns:
            raise ValueError(f"persistence baseline needs column {self.column!r}")
        return self

    def predict(self, X):
        return X[self.column].to_numpy(dtype=float)


MODELS = {
    "baseline_mean": DummyRegressor(strategy="mean"),
    "baseline_persistence": PersistenceBaseline("cnt_lag_1"),
    "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    "hgb": HistGradientBoostingRegressor(random_state=0, max_iter=300),
}


def temporal_split(df: pd.DataFrame):
    """Split by date, never at random. A random split on a time series
    puts tomorrow in train and today in test."""
    train = df[df.dteday <= TRAIN_END]
    valid = df[(df.dteday > TRAIN_END) & (df.dteday <= VALID_END)]
    test = df[df.dteday > VALID_END]
    return train, valid, test


RATIO_BASE = "cnt_roll_7"


def fit_and_score(target: str = "raw") -> dict:
    if target not in ("raw", "ratio"):
        raise ValueError(f"unknown target {target!r}")
    df = pd.read_parquet(PROCESSED)
    cols = feature_columns(df)
    train, valid, test = temporal_split(df)

    results = {
        "n_features": len(cols),
        "features": cols,
        "n_train": len(train),
        "n_valid": len(valid),
        "n_test": len(test),
    }
    splits = [("valid", valid), ("test", test)]
    if target == "ratio":
        results["target"] = f"{TARGET} / {RATIO_BASE}"
        splits = [("valid", valid)]  # test is never scored while experimenting

    for name, model in MODELS.items():
        # Persistence fits nothing and returns a count, so rescaling it
        # would multiply a count by a count.
        scaled = target == "ratio" and not isinstance(model, PersistenceBaseline)
        y = train[TARGET] / train[RATIO_BASE] if scaled else train[TARGET]
        model.fit(train[cols], y)
        results[name] = {}
        for split, part in splits:
            pred = model.predict(part[cols])
            if scaled:
                pred = pred * part[RATIO_BASE].to_numpy()
            results[name][split] = {
                "r2": round(float(r2_score(part[TARGET], pred)), 4),
                "mae": round(float(mean_absolute_error(part[TARGET], pred)), 1),
            }
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fit models and write metrics.")
    parser.add_argument("--target", choices=["raw", "ratio"], default="raw")
    args = parser.parse_args()

    res = fit_and_score(args.target)
    out = METRICS_RATIO if args.target == "ratio" else METRICS
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2))
    if args.target == "ratio":
        print("VALIDATION        R²       MAE")
        for name in MODELS:
            m = res[name]["valid"]
            print(f"{name:<22}{m['r2']:>8.4f}{m['mae']:>9.1f}")
    else:
        print(json.dumps({k: v for k, v in res.items() if k != "features"}, indent=2))
