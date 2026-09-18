from datetime import date
from decimal import Decimal

import pytest

from finance.advanced import weighted_average_cost, xirr


def test_weighted_cost_preserves_decimal_precision() -> None:
    cost, remaining = weighted_average_cost(
        [(Decimal("0.1"), Decimal("100")), (Decimal("0.2"), Decimal("200"))], Decimal("0.15")
    )
    assert cost == Decimal("25.0")
    assert remaining == Decimal("0.15")


def test_xirr() -> None:
    rate = xirr([(date(2025, 1, 1), Decimal("-100")), (date(2026, 1, 1), Decimal("110"))])
    assert abs(rate - Decimal("0.1")) < Decimal("0.0000001")


def test_cannot_sell_more_than_holding() -> None:
    with pytest.raises(ValueError):
        weighted_average_cost([(Decimal("1"), Decimal("2"))], Decimal("2"))
