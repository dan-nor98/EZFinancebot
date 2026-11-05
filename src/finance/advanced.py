from collections.abc import Sequence
from datetime import date
from decimal import Decimal, getcontext

getcontext().prec = 38


def xnpv(rate: Decimal, cashflows: Sequence[tuple[date, Decimal]]) -> Decimal:
    origin = cashflows[0][0]
    return sum(
        (
            amount / (Decimal(1) + rate) ** (Decimal((when - origin).days) / Decimal(365))
            for when, amount in cashflows
        ),
        start=Decimal(0),
    )


def xirr(cashflows: Sequence[tuple[date, Decimal]], guess: Decimal = Decimal("0.1")) -> Decimal:
    """Calculate effective annual cost without binary floating point."""
    if (
        not cashflows
        or not any(v < 0 for _, v in cashflows)
        or not any(v > 0 for _, v in cashflows)
    ):
        raise ValueError("cashflows must contain positive and negative values")
    rate = guess
    origin = cashflows[0][0]
    for _ in range(100):
        value = xnpv(rate, cashflows)
        derivative = sum(
            -(Decimal((when - origin).days) / Decimal(365))
            * amount
            / (Decimal(1) + rate) ** (Decimal((when - origin).days) / Decimal(365) + 1)
            for when, amount in cashflows
        )
        if derivative == 0:
            break
        next_rate = rate - value / derivative
        if abs(next_rate - rate) < Decimal("0.000000000000000001"):
            return next_rate
        rate = next_rate
    return rate


def weighted_average_cost(
    lots: Sequence[tuple[Decimal, Decimal]], sale_quantity: Decimal
) -> tuple[Decimal, Decimal]:
    quantity = sum((q for q, _ in lots), Decimal(0))
    cost = sum((q * p for q, p in lots), Decimal(0))
    if sale_quantity > quantity or quantity == 0:
        raise ValueError("insufficient holding")
    unit_cost = cost / quantity
    return unit_cost * sale_quantity, quantity - sale_quantity
