"""Guard rails on the ingest contract and the trained model's behaviour."""
import pandas as pd
import pytest
from sklearn.metrics import r2_score

from src.config import LAG_WARMUP, TARGET
from src.features import (
    WEATHER_ORDER,
    build_features,
    encode_weather,
    feature_columns,
    reindex_to_calendar,
)
from src.ingest import load_raw
from src.train import MODELS, temporal_split


@pytest.fixture(scope="module")
def raw():
    return load_raw().sort_values("dteday").reset_index(drop=True)


@pytest.fixture(scope="module")
def feats(raw):
    return build_features(raw)


def test_calendar_is_complete_before_lagging(raw):
    """The reindexed frame must have no gaps, or the lags are wrong."""
    grid = reindex_to_calendar(raw)
    assert set(grid.dteday.diff().dropna().dt.days.unique()) == {1}


def test_only_expected_rows_are_dropped(raw, feats):
    """Rows may only vanish for the lag warm-up or downstream of a genuinely
    absent day -- never because an encoder produced a silent NaN.

    Accounting: the first LAG_WARMUP days have no complete history. Each
    absent calendar day m costs the LAG_WARMUP rows after it (cnt_lag_1 is
    NaN on m+1, cnt_roll_7 is NaN on m+1..m+7, cnt_lag_7 on m+7; their
    union is 7 rows). Day m itself was never in `raw`, so it is not a loss.
    The bound is exact for the current feature set; add a longer lag and
    LAG_WARMUP in src/config.py must grow with it.
    """
    full = pd.date_range(raw.dteday.min(), raw.dteday.max(), freq="D")
    missing_days = len(full) - len(raw)
    allowed_loss = LAG_WARMUP + LAG_WARMUP * missing_days
    lost = len(raw) - len(feats)
    assert lost <= allowed_loss, f"lost {lost} rows; expected at most {allowed_loss}"


def test_encode_weather_rejects_unmapped_label():
    """An unseen label must raise, not become a NaN that dropna() deletes."""
    labels = pd.Series([*WEATHER_ORDER, "UNSEEN"])
    with pytest.raises(ValueError, match="UNSEEN"):
        encode_weather(labels)


def test_beats_the_mean_baseline(feats):
    """A model that cannot beat predicting the training mean is not a result."""
    cols = feature_columns(feats)
    train, _, test = temporal_split(feats)
    ridge = MODELS["ridge"]
    ridge.fit(train[cols], train[TARGET])
    assert r2_score(test[TARGET], ridge.predict(test[cols])) > 0.4


def test_persistence_baseline_is_reported():
    """The baseline that matters for a lag-driven model is 'yesterday again'.
    It must be in the comparison, whatever its score."""
    assert "baseline_persistence" in MODELS


def _unclassified(columns, feature_cols):
    from src.config import ENCODED_COLS, FORBIDDEN
    known = FORBIDDEN | ENCODED_COLS | set(feature_cols) | {"dteday"}
    return sorted(set(columns) - known)


def test_every_raw_column_is_classified(feats):
    """A new column in the raw CSV must not enter silently: it has to be
    forbidden, encoded, or a feature, by an explicit edit to src/config.py."""
    from src.config import RAW
    from src.features import feature_columns
    raw_cols = pd.read_csv(RAW, nrows=0).columns
    missing = _unclassified(raw_cols, feature_columns(feats))
    assert not missing, f"unclassified raw columns: {missing}; classify each in src/config.py"


def test_unclassified_check_flags_a_new_column(feats):
    from src.features import feature_columns
    assert _unclassified(["dteday", "new_sensor"], feature_columns(feats)) == ["new_sensor"]
