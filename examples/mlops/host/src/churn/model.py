"""The round's best experiment: a two-feature risk score and its threshold."""

from __future__ import annotations


def score(row: dict) -> float:
    tenure, calls = float(row["tenure_months"]), float(row["support_calls"])
    return min(1.0, 0.15 * calls + (0.4 if tenure < 6 else 0.0))


def predict(rows: list, threshold: float) -> list:
    return [1 if score(r) >= threshold else 0 for r in rows]


def accuracy(rows: list, threshold: float) -> float:
    hits = sum(int(p == int(r["churned"])) for p, r in zip(predict(rows, threshold), rows))
    return hits / len(rows)
