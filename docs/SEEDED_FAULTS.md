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
