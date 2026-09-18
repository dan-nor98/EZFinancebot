import re
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

import jdatetime

from finance.models import TransactionType

DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
CHARS = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه"})
SCALE = {
    "k": Decimal(1000),
    "thousand": Decimal(1000),
    "هزار": Decimal(1000),
    "m": Decimal(1000000),
    "million": Decimal(1000000),
    "میلیون": Decimal(1000000),
    "b": Decimal(1000000000),
    "billion": Decimal(1000000000),
    "میلیارد": Decimal(1000000000),
}
CATEGORY_ALIASES = {
    "TRANSPORTATION": {"taxi", "snapp", "اسنپ", "تاکسی", "تپسی"},
    "FOOD": {"food", "coffee", "قهوه", "غذا", "رستوران"},
    "CLOTHING": {"clothes", "clothing", "لباس", "پوشاک"},
    "SALARY": {"salary", "حقوق"},
    "REFUND": {"refund", "بازپرداخت"},
}
INTENT_WORDS = [
    (TransactionType.BNPL_PAYMENT, {"قسط اعتباری", "bnpl payment"}),
    (TransactionType.BNPL_PURCHASE, {"خرید اقساطی", "bnpl"}),
    (TransactionType.LOAN_PAYMENT, {"قسط وام", "loan payment"}),
    (TransactionType.LOAN_DISBURSEMENT, {"وام گرفتم", "loan received"}),
    (TransactionType.DEBT_GIVEN, {"قرض دادم", "lent"}),
    (TransactionType.DEBT_RECEIVED, {"قرض گرفتم", "borrowed"}),
    (TransactionType.DEBT_PAYMENT, {"بدهی دادم", "debt payment"}),
    (TransactionType.ASSET_BUY, {"خریدم", "buy", "bought"}),
    (TransactionType.ASSET_SELL, {"فروختم", "sell", "sold"}),
    (TransactionType.GOAL_CONTRIBUTION, {"پس انداز", "پس‌انداز", "goal"}),
    (TransactionType.TRANSFER, {"انتقال", "transfer", " to "}),
    (TransactionType.REFUND, {"refund", "بازپرداخت"}),
    (TransactionType.INCOME, {"salary", "حقوق", "درآمد", "income", "پاداش"}),
]
AMOUNT_RE = re.compile(
    r"(?<![\w.])(?P<number>\d+(?:[.,]\d+)?)\s*(?P<scale>k|m|b|thousand|million|billion|هزار|میلیون|میلیارد)?\b",
    re.I,
)
DATE_RE = re.compile(r"\b(?P<year>\d{4})[-/](?P<month>\d{1,2})[-/](?P<day>\d{1,2})\b")


@dataclass(frozen=True)
class ParseResult:
    type: TransactionType | None
    amount_irr: int | None
    currency: str
    category: str | None
    occurred_at: datetime
    description: str | None
    note: str | None
    tags: list[str] = field(default_factory=list)
    account: str | None = None
    payment_method: str | None = None
    confidence: Decimal = Decimal("1")
    missing_fields: list[str] = field(default_factory=list)


def normalize(text: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKC", text).translate(DIGITS).translate(CHARS).strip().split()
    )


def extract_amount(text: str) -> tuple[int | None, str, tuple[int, int] | None]:
    match = AMOUNT_RE.search(text)
    if not match:
        return None, "TOMAN", None
    try:
        number = Decimal(match.group("number").replace(",", ""))
    except InvalidOperation:
        return None, "TOMAN", None
    scale = SCALE.get((match.group("scale") or "").lower(), Decimal(1))
    currency = "RIAL" if re.search(r"ریال|\brial\b|\birr\b", text, re.I) else "TOMAN"
    amount = number * scale * (Decimal(1) if currency == "RIAL" else Decimal(10))
    if amount != amount.to_integral_value():
        return None, currency, match.span()
    return int(amount), currency, match.span()


def extract_date(
    text: str, now: datetime, timezone: str
) -> tuple[datetime, tuple[int, int] | None]:
    local_now = now.astimezone(ZoneInfo(timezone))
    if "پریروز" in text:
        return local_now - timedelta(days=2), (text.index("پریروز"), text.index("پریروز") + 6)
    if "دیروز" in text or re.search(r"\byesterday\b", text, re.I):
        token = "دیروز" if "دیروز" in text else "yesterday"
        return local_now - timedelta(days=1), (
            text.lower().index(token),
            text.lower().index(token) + len(token),
        )
    match = DATE_RE.search(text)
    if match:
        year, month, day = map(int, match.groups())
        if year < 1700:
            converted = jdatetime.date(year, month, day).togregorian()
            year, month, day = converted.year, converted.month, converted.day
        return datetime(year, month, day, tzinfo=ZoneInfo(timezone)), match.span()
    return local_now, None


def parse(
    text: str,
    *,
    timezone: str = "Asia/Tehran",
    now: datetime | None = None,
    aliases: dict[str, str] | None = None,
    accounts: list[str] | None = None,
) -> ParseResult:
    clean = normalize(text)
    lowered = clean.casefold()
    current = now or datetime.now(UTC)
    amount, currency, amount_span = extract_amount(clean)
    occurred_at, date_span = extract_date(clean, current, timezone)
    intent = TransactionType.EXPENSE
    for candidate, words in INTENT_WORDS:
        if any(word in lowered for word in words):
            intent = candidate
            break
    all_aliases = {
        alias.casefold(): code for code, values in CATEGORY_ALIASES.items() for alias in values
    }
    all_aliases.update({normalize(key).casefold(): value for key, value in (aliases or {}).items()})
    category = next(
        (
            code
            for alias, code in sorted(
                all_aliases.items(), key=lambda item: len(item[0]), reverse=True
            )
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", lowered)
        ),
        None,
    )
    if category == "SALARY":
        intent = TransactionType.INCOME
    if category == "REFUND":
        intent = TransactionType.REFUND
    tags = re.findall(r"#([\w\u0600-\u06ff]+)", clean)
    account = next(
        (item for item in (accounts or []) if normalize(item).casefold() in lowered), None
    )
    payment = next(
        (
            value
            for key, value in {
                "کارت": "CARD",
                "card": "CARD",
                "نقد": "CASH",
                "cash": "CASH",
            }.items()
            if key in lowered
        ),
        None,
    )
    remainder = clean
    for span in sorted([item for item in (amount_span, date_span) if item], reverse=True):
        remainder = remainder[: span[0]] + " " + remainder[span[1] :]
    remainder = re.sub(
        r"#([\w\u0600-\u06ff]+)|\b(?:تومان|ریال|toman|rial|irr)\b", " ", remainder, flags=re.I
    )
    for alias in all_aliases:
        remainder = re.sub(rf"(?<!\w){re.escape(alias)}(?!\w)", " ", remainder, flags=re.I)
    note = " ".join(remainder.split()) or None
    missing = [
        name for name, value in (("amount", amount), ("category", category)) if value is None
    ]
    confidence = Decimal("1") - Decimal("0.2") * len(missing)
    return ParseResult(
        intent,
        amount,
        currency,
        category,
        occurred_at.astimezone(UTC),
        note,
        note,
        tags,
        account,
        payment,
        confidence,
        missing,
    )
