"""Tests for the warranty/entitlement logic (Python port of WarrantyService.cls)."""

from __future__ import annotations

from datetime import date

from sim import warranty


def test_inside_window_is_covered():
    assert warranty.is_under_warranty(date(2025, 1, 15), 12, date(2025, 6, 1)) is True


def test_outside_window_is_not_covered():
    assert warranty.is_under_warranty(date(2024, 1, 15), 12, date(2025, 3, 1)) is False


def test_exact_boundary_is_inclusive():
    order = date(2024, 1, 15)
    expiry = date(2025, 1, 15)
    assert warranty.is_under_warranty(order, 12, expiry) is True
    assert warranty.is_under_warranty(order, 12, date(2025, 1, 16)) is False


def test_missing_inputs_are_not_covered():
    assert warranty.is_under_warranty(None, 12, date(2025, 1, 1)) is False
    assert warranty.is_under_warranty(date(2025, 1, 1), 12, None) is False
    assert warranty.is_under_warranty(date(2025, 1, 1), None, date(2025, 1, 1)) is False


def test_zero_month_warranty_is_not_covered():
    day = date(2025, 1, 15)
    assert warranty.is_under_warranty(day, 0, day) is False
    assert warranty.is_under_warranty(day, -3, day) is False


def test_month_end_clamping():
    # 31 Jan + 1 month has no 31 Feb, so it clamps to the end of February.
    assert warranty.add_months(date(2025, 1, 31), 1) == date(2025, 2, 28)
    assert warranty.add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)  # leap year


def test_accepts_iso_strings_and_datetimes():
    assert warranty.is_under_warranty("2025-01-15", "12", "2025-06-01") is True
    from datetime import datetime

    assert warranty.is_under_warranty(datetime(2025, 1, 15), 12, datetime(2025, 6, 1)) is True


def test_entitlement_message_reflects_verdict():
    covered = warranty.entitlement_message(date(2025, 1, 1), 12, date(2025, 3, 1))
    expired = warranty.entitlement_message(date(2020, 1, 1), 12, date(2025, 3, 1))
    missing = warranty.entitlement_message(None, 12, date(2025, 3, 1))
    assert "still under warranty" in covered
    assert "window has ended" in expired
    assert "could not find" in missing
