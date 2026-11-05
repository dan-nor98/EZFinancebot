import csv
import io
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from finance.models import (
    Category,
    CategoryAlias,
    ExternalIdentity,
    IdempotencyKey,
    Status,
    Transaction,
    TransactionType,
    User,
    UserPreference,
)
from finance.parser import parse
from finance.shared.errors import ConflictError, NotFoundError

SYSTEM_CATEGORIES = {
    "TRANSPORTATION": ("حمل‌ونقل", "EXPENSE"),
    "FOOD": ("خوراک", "EXPENSE"),
    "CLOTHING": ("پوشاک", "EXPENSE"),
    "HOUSING": ("مسکن", "EXPENSE"),
    "UTILITIES": ("قبوض و خدمات", "EXPENSE"),
    "SUBSCRIPTION": ("اشتراک", "EXPENSE"),
    "HEALTH": ("سلامت", "EXPENSE"),
    "EDUCATION": ("آموزش", "EXPENSE"),
    "ENTERTAINMENT": ("سرگرمی", "EXPENSE"),
    "GIFT": ("هدیه", "EXPENSE"),
    "FINANCIAL_FEE": ("هزینه مالی", "EXPENSE"),
    "TAX": ("مالیات", "EXPENSE"),
    "OTHER": ("سایر", "EXPENSE"),
    "SALARY": ("حقوق", "INCOME"),
    "FREELANCE": ("فریلنس", "INCOME"),
    "BONUS": ("پاداش", "INCOME"),
    "GIFT_INCOME": ("هدیه دریافتی", "INCOME"),
    "INVESTMENT_INCOME": ("درآمد سرمایه‌گذاری", "INCOME"),
    "REFUND": ("بازپرداخت", "INCOME"),
    "OTHER_INCOME": ("سایر درآمدها", "INCOME"),
}


def bootstrap(
    session: Session, provider: str, external_user_id: str, **profile: str | None
) -> User:
    identity = session.scalar(
        select(ExternalIdentity).where(
            ExternalIdentity.provider == provider,
            ExternalIdentity.external_user_id == external_user_id,
        )
    )
    if identity:
        user = session.get(User, identity.user_id)
        assert user is not None
        return user
    user = User(
        first_name=profile.get("first_name"),
        username=profile.get("username"),
        language_code=profile.get("language_code"),
    )
    session.add(user)
    session.flush()
    session.add_all(
        [
            ExternalIdentity(user_id=user.id, provider=provider, external_user_id=external_user_id),
            UserPreference(user_id=user.id),
        ]
    )
    session.commit()
    return user


def owned(session: Session, model: type[Any], object_id: str, user_id: str) -> Any:
    value = session.scalar(select(model).where(model.id == object_id, model.user_id == user_id))
    if value is None:
        raise NotFoundError("Resource not found")
    return value


def capture(
    session: Session,
    user: User,
    text: str,
    occurred_at: datetime | None = None,
    idempotency_key: str | None = None,
    source: str = "API",
) -> dict[str, Any]:
    if source == "TELEGRAM" and not idempotency_key:
        raise ConflictError("Telegram writes require an idempotency key")
    if idempotency_key:
        previous = session.get(IdempotencyKey, idempotency_key)
        if previous:
            return previous.response
    preference = session.get(UserPreference, user.id)
    assert preference
    alias_rows = session.execute(
        select(CategoryAlias.alias, Category.code)
        .join(Category)
        .where(CategoryAlias.user_id == user.id)
    ).all()
    result = parse(text, timezone=preference.timezone, now=occurred_at, aliases=dict(alias_rows))
    transaction = Transaction(
        user_id=user.id,
        type=result.type,
        amount_irr=result.amount_irr,
        category_code=result.category,
        occurred_at=result.occurred_at,
        description=result.description,
        note=result.note,
        raw_input=text,
        source=source,
        status=Status.COMPLETE if not result.missing_fields else Status.INCOMPLETE,
        parse_confidence=result.confidence,
        tags=result.tags,
        payment_method=result.payment_method,
    )
    session.add(transaction)
    session.flush()
    response = {"result": "TRANSACTION_CREATED", "transaction": serialize_transaction(transaction)}
    if idempotency_key:
        session.add(IdempotencyKey(key=idempotency_key, user_id=user.id, response=response))
    session.commit()
    return response


def serialize_transaction(item: Transaction) -> dict[str, Any]:
    return {
        "id": item.id,
        "type": item.type.value if item.type else None,
        "amountIrr": item.amount_irr,
        "category": item.category_code,
        "status": item.status.value,
        "occurredAt": item.occurred_at.isoformat(),
        "description": item.description,
        "note": item.note,
        "tags": item.tags,
    }


def summary(session: Session, user_id: str, start: datetime, end: datetime) -> dict[str, int]:
    rows = session.execute(
        select(Transaction.type, func.coalesce(func.sum(Transaction.amount_irr), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.status == Status.COMPLETE,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        .group_by(Transaction.type)
    ).all()
    values = dict(rows)
    return {
        "expenseIrr": int(values.get(TransactionType.EXPENSE, 0))
        + int(values.get(TransactionType.BNPL_PURCHASE, 0)),
        "incomeIrr": int(values.get(TransactionType.INCOME, 0)),
        "refundIrr": int(values.get(TransactionType.REFUND, 0)),
    }


def export_csv(session: Session, user_id: str, start: datetime, end: datetime) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "type", "amount_irr", "category", "occurred_at", "description"])
    for item in session.scalars(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
    ).all():
        description = item.description or ""
        description = (
            "'" + description if description.startswith(("=", "+", "-", "@")) else description
        )
        writer.writerow(
            [
                item.id,
                item.type.value if item.type else "",
                item.amount_irr or "",
                item.category_code or "",
                item.occurred_at.isoformat(),
                description,
            ]
        )
    return "\ufeff" + output.getvalue()


def delete_user_data(session: Session, user_id: str) -> None:
    session.execute(delete(User).where(User.id == user_id))
    session.commit()
