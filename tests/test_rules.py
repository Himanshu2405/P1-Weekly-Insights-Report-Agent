from weekly_report import rules


def test_change_pct_and_pp():
    assert rules.change(110, 100, "pct") == 10.0
    assert rules.change(15.2, 14.6, "pp") == 0.6
    assert rules.change(5, 0, "pct") is None
    assert rules.change(5, None, "pct") is None


def test_assessment_respects_polarity():
    # cancellation rate going up is bad, orders going up is good
    assert rules.assessment(0.6, higher_is_good=False) == "bad"
    assert rules.assessment(0.6, higher_is_good=True) == "good"
    assert rules.assessment(-2.0, higher_is_good=False) == "good"
    assert rules.assessment(0.0, higher_is_good=True) == "flat"


def test_notable_thresholds():
    prev = [100, 101, 99, 100, 102, 98, 100, 101]
    assert rules.is_notable(112, 12.0, "pct", prev)[0]        # >= 10% WoW
    assert not rules.is_notable(101, 1.0, "pct", prev)[0]     # small and inside range
    assert rules.is_notable(105, 3.0, "pct", prev)[0]         # small but outside 8-week range
    assert rules.is_notable(15.2, 1.0, "pp", [14.0] * 8)[0]   # >= 1 pp for rates


def test_anomaly_ratio():
    prev = [100] * 8
    assert rules.anomaly_ratio(250, prev) == 2.5
    assert rules.anomaly_ratio(40, prev) == 0.4
    assert rules.anomaly_ratio(180, prev) is None


def test_bad_streak_counts_only_consecutive_bad_moves():
    assert rules.bad_streak([14.3, 14.4, 14.6, 15.2], higher_is_good=False) == 3
    assert rules.bad_streak([14.8, 14.3, 14.4, 14.6], higher_is_good=False) == 2
    assert rules.bad_streak([15.0, 14.0], higher_is_good=False) == 0
    assert rules.bad_streak([100, 90, 80], higher_is_good=True) == 2
