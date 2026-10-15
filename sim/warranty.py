"""Python port of ``WarrantyService.isUnderWarranty``.

The window is inclusive of the exact anniversary boundary so the harness and the Apex class agree
on eligibility (pain P5).
"""

from __future__ import annotations

from datetime import date, datetime


def _as_date(value):
    """Coerce a ``date``/``datetime``/ISO string to a ``date``; return None for missing values."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return datetime.fromisoformat(text.replace("Z", "+00:00")).date()


def add_months(anchor: date, months: int) -> date:
    """Add calendar months to a date, clamping the day to the end of the target month."""
    month_index = anchor.month - 1 + months
    year = anchor.year + month_index // 12
    month = month_index % 12 + 1
    # Clamp to the last valid day of the resulting month.
    if month == 12:
        last_day = 31
    else:
        last_day = (date(year, month + 1, 1) - date(year, month, 1)).days
    day = min(anchor.day, last_day)
    return date(year, month, day)


def is_under_warranty(order_date, warranty_months, request_date) -> bool:
    """Is ``request_date`` within ``warranty_months`` of ``order_date`` (inclusive boundary)?

    Returns False for any missing input or non-positive coverage, matching the Apex behaviour.
    """
    order = _as_date(order_date)
    request = _as_date(request_date)
    if order is None or request is None:
        return False
    if warranty_months is None:
        return False
    try:
        months = int(warranty_months)
    except (TypeError, ValueError):
        return False
    if months <= 0:
        return False
    return request <= add_months(order, months)


def entitlement_message(order_date, warranty_months, request_date) -> str:
    """Agent-friendly verdict text, mirroring ``WarrantyService.entitlementMessage``."""
    order = _as_date(order_date)
    if order is None:
        return "We could not find that order on your account. A specialist will follow up."
    if is_under_warranty(order, warranty_months, request_date):
        expiry = add_months(order, int(warranty_months))
        return (
            f"Good news - this purchase is still under warranty through "
            f"{expiry.isoformat()}. We can start a warranty claim for you."
        )
    return (
        "Your warranty window has ended. We can still help - here is our "
        "out-of-warranty repair option."
    )
