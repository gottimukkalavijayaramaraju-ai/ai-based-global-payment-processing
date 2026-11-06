"""AI fraud-risk model.
Trains a RandomForest on synthetic data at startup (replace with real
historical transactions in production) and returns a 0-1 risk score.
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Demo country risk levels (0 low .. 1 high)
COUNTRY_RISK = {"US": 0.1, "GB": 0.1, "IN": 0.2, "DE": 0.1, "JP": 0.1,
                "AU": 0.1, "CA": 0.1, "SG": 0.1, "AE": 0.3, "BR": 0.4}

FEATURES = ["amount_usd", "hour", "country_risk", "cross_border",
            "txn_last_hour", "new_device"]


def _synthetic_data(n=6000, seed=42):
    rng = np.random.default_rng(seed)
    amount = rng.lognormal(4.0, 1.2, n)
    hour = rng.integers(0, 24, n)
    risk = rng.choice(list(COUNTRY_RISK.values()), n)
    cross = rng.integers(0, 2, n)
    velocity = rng.poisson(1.0, n)
    new_dev = rng.integers(0, 2, n)
    X = np.column_stack([amount, hour, risk, cross, velocity, new_dev])

    # Hidden fraud rule + noise used only to create training labels
    score = (0.0006 * amount + 0.8 * risk + 0.5 * cross + 0.4 * new_dev
             + 0.35 * np.clip(velocity - 2, 0, None)
             + 0.4 * ((hour < 5)).astype(float)
             + rng.normal(0, 0.25, n))
    y = (score > 1.3).astype(int)
    return X, y


class FraudModel:
    def __init__(self):
        X, y = _synthetic_data()
        self.clf = RandomForestClassifier(n_estimators=100, max_depth=8,
                                          random_state=42).fit(X, y)

    def score(self, amount_usd, hour, country, cross_border,
              txn_last_hour, new_device) -> float:
        row = [[amount_usd, hour, COUNTRY_RISK.get(country, 0.5),
                int(cross_border), txn_last_hour, int(new_device)]]
        return float(self.clf.predict_proba(row)[0][1])
