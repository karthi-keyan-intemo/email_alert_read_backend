from datetime import date

import pytest

from cron.date_range import compute_date_range


def test_uses_explicit_dates_when_both_given():
    assert compute_date_range(
        lookback_days=7,
        from_date=date(2026, 8, 16),
        to_date=date(2026, 8, 27),
    ) == (date(2026, 8, 16), date(2026, 8, 27))


def test_uses_lookback_when_no_dates_given():
    from_date, to_date = compute_date_range(lookback_days=2)
    assert to_date == date.today()
    assert (to_date - from_date).days == 2


def test_falls_back_to_lookback_when_only_to_date_given():
    from_date, to_date = compute_date_range(lookback_days=3, to_date=date(2026, 8, 27))
    assert (from_date, to_date) == (date(2026, 8, 24), date(2026, 8, 27))


def test_keeps_from_date_when_only_from_given():
    from_date, to_date = compute_date_range(lookback_days=3, from_date=date(2026, 8, 16))
    assert from_date == date(2026, 8, 16)
    assert (to_date - from_date).days == 3


def test_no_lookback_when_from_and_to_are_equal():
    assert compute_date_range(
        lookback_days=1,
        from_date=date(2026, 8, 16),
        to_date=date(2026, 8, 16),
    ) == (date(2026, 8, 16), date(2026, 8, 16))


def test_rejects_invalid_range():
    with pytest.raises(ValueError):
        compute_date_range(
            lookback_days=1,
            from_date=date(2026, 8, 27),
            to_date=date(2026, 8, 16),
        )