from churn import model


def test_short_tenure_with_calls_is_risky():
    assert model.score({"tenure_months": 2, "support_calls": 5}) == 1.0
    assert model.predict([{"tenure_months": 30, "support_calls": 0}], 0.5) == [0]


def test_accuracy():
    rows = [{"tenure_months": 2, "support_calls": 5, "churned": 1}, {"tenure_months": 30, "support_calls": 0,
                                                                      "churned": 1}]
    assert model.accuracy(rows, 0.5) == 0.5
