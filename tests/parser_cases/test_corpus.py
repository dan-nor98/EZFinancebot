import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from finance.parser import parse

CASES = json.loads((Path(__file__).parent / "corpus.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=[case["input"] for case in CASES])
def test_permanent_parser_corpus(case: dict[str, object]) -> None:
    result = parse(str(case["input"]), now=datetime(2026, 9, 18, tzinfo=UTC))
    assert result.type is not None and result.type.value == case["type"]
    assert result.amount_irr == case["amountIrr"]
    assert result.category == case["category"]


def test_relative_date_uses_user_timezone() -> None:
    result = parse("دیروز 450k taxi", now=datetime(2026, 9, 18, 22, tzinfo=UTC))
    assert result.occurred_at.date().isoformat() == "2026-09-18"


def test_jalali_date() -> None:
    result = parse("350k taxi 1405/06/27")
    assert result.occurred_at.date().isoformat() == "2026-09-18"


def test_explicit_rial_is_not_multiplied() -> None:
    assert parse("350k rial taxi").amount_irr == 350_000
