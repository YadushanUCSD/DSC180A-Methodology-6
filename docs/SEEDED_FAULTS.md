# Seeded faults

## 0. Feature test written first: cnt_lag_2

Tests added before the feature existed. Red run:

```
....F....F                                                               [100%]
=================================== FAILURES ===================================
_____________________ test_cnt_lag_2_is_true_two_day_lags ______________________
tests/test_leakage.py:54: in test_cnt_lag_2_is_true_two_day_lags
    for date, lag in feats.set_index("dteday").cnt_lag_2.items():
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../miniforge3/lib/python3.12/site-packages/pandas/core/generic.py:6194: in __getattr__
    return object.__getattribute__(self, name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'DataFrame' object has no attribute 'cnt_lag_2'. Did you mean: 'cnt_lag_1'?
_________________________ test_cnt_lag_2_on_named_date _________________________
../../miniforge3/lib/python3.12/site-packages/pandas/core/indexes/base.py:3641: in get_loc
    return self._engine.get_loc(casted_key)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pandas/_libs/index.pyx:168: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/index.pyx:197: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/hashtable_class_helper.pxi:7668: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
pandas/_libs/hashtable_class_helper.pxi:7676: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
E   KeyError: 'cnt_lag_2'

The above exception was the direct cause of the following exception:
tests/test_leakage.py:91: in test_cnt_lag_2_on_named_date
    assert row["cnt_lag_2"] == 5020
           ^^^^^^^^^^^^^^^^
../../miniforge3/lib/python3.12/site-packages/pandas/core/series.py:959: in __getitem__
    return self._get_value(key)
           ^^^^^^^^^^^^^^^^^^^^
../../miniforge3/lib/python3.12/site-packages/pandas/core/series.py:1046: in _get_value
    loc = self.index.get_loc(label)
          ^^^^^^^^^^^^^^^^^^^^^^^^^
../../miniforge3/lib/python3.12/site-packages/pandas/core/indexes/base.py:3648: in get_loc
    raise KeyError(key) from err
E   KeyError: 'cnt_lag_2'
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_cnt_lag_2_is_true_two_day_lags - Attribute...
FAILED tests/test_leakage.py::test_cnt_lag_2_on_named_date - KeyError: 'cnt_l...
2 failed, 8 passed in 0.51s
```

## make feature_columns in src/features.py also return the forbidden column casual

`git diff src/`:

```diff
diff --git a/src/features.py b/src/features.py
index 02e93ca..c805413 100644
--- a/src/features.py
+++ b/src/features.py
@@ -82,7 +82,7 @@ def build_features(df: pd.DataFrame) -> pd.DataFrame:
 def feature_columns(df: pd.DataFrame) -> list[str]:
     """Numeric columns that are safe to feed the model."""
     numeric = df.select_dtypes(include="number").columns
-    return [c for c in numeric if c not in FORBIDDEN]
+    return [c for c in numeric if c not in FORBIDDEN or c == "casual"]
 
 
 if __name__ == "__main__":
```

Hook stderr (`check_leakage.sh`, as surfaced after the Edit):

```
[${CLAUDE_PROJECT_DIR}/.claude/hooks/check_leakage.sh]: Leakage tests failed after editing /Users/yadi/Downloads/bikeshare-open-starter/src/features.py:
feats =         dteday  instant  season  ...  cnt_lag_2 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      959.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1341.0     920.0  1531.428571

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'casual'}
E       assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_2', 'cnt_lag_7', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:31: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 9 passed in 0.35s
```

`python -m pytest -q --tb=short`:

```
.......F...........                                                      [100%]
=================================== FAILURES ===================================
__________________________ test_no_forbidden_features __________________________
tests/test_leakage.py:31: in test_no_forbidden_features
    assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E   AssertionError: forbidden columns in feature set: {'casual'}
E   assert not ({'atemp', 'casual', 'cnt_lag_1', 'cnt_lag_2', 'cnt_lag_7', 'cnt_roll_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
1 failed, 18 passed in 1.18s
```

**Fix:** agent (Claude Sonnet), fresh session, 3 turns. Prompt: "make test is failing. Find the cause and fix it." Not blind: the seed commit message and this file name the fault, and the failing test prints `{'casual'}`. The count measures fixing a fault the suite has flagged, not unaided diagnosis.
