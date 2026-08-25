import numpy as np
from rep_audit.prototypes.rr_direct import fit_rr_direct, assign_frozen_prototypes


def test_rr_direct_is_deterministic_and_executable():
    rng = np.random.default_rng(7)
    X = rng.normal(size=(80, 12))
    X[:40, 0] += 2.5; X[:40, 1] -= 2.5
    X[40:, 0] -= 2.5; X[40:, 1] += 2.5
    f = tuple(f"g{i}" for i in range(X.shape[1]))
    a = fit_rr_direct(X, f, k=2, feature_budget=12, max_pairs=66, max_rules=10)
    b = fit_rr_direct(X, f, k=2, feature_budget=12, max_pairs=66, max_rules=10)
    assert a.to_dict() == b.to_dict()
    pred, score, margin = assign_frozen_prototypes(X, f, a.prototypes, min_score=0.0, min_margin=0.0)
    assert set(pred) == {0, 1}
    assert np.isfinite(score).all() and np.isfinite(margin).all()


def test_rr_direct_handles_all_nan_feature_and_missing_target_values():
    rng = np.random.default_rng(19)
    X = rng.normal(size=(60, 8))
    X[:, 7] = np.nan
    X[:30, 0] += 2.0; X[:30, 1] -= 2.0
    X[30:, 0] -= 2.0; X[30:, 1] += 2.0
    f = tuple(f"g{i}" for i in range(X.shape[1]))
    model = fit_rr_direct(X, f, k=2, feature_budget=8, max_pairs=28, max_rules=8)
    assert "g7" not in model.selected_feature_ids
    Xt = X.copy()
    Xt[0, 0] = np.nan
    Xt[1, 1] = np.nan
    pred, score, margin = assign_frozen_prototypes(
        Xt, f, model.prototypes, min_score=0.0, min_margin=0.0
    )
    assert pred.shape == (60,)
    assert score.shape == (60,)
    assert margin.shape == (60,)
