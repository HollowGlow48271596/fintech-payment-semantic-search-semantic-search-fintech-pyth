from fintech_search import risk_decision


def test_high_risk_match_requires_review_notification():
    results = [{"metadata": {"risk_level": "high"}}, {"metadata": {"risk_level": "low"}}]
    assert risk_decision(results) == {"notification": "review_required", "requires_review": True}
