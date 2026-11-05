import enum
import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from finance.shared.database import Base as Base


def uuid4() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(UTC)


class TransactionType(enum.StrEnum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    TRANSFER = "TRANSFER"
    DEBT_GIVEN = "DEBT_GIVEN"
    DEBT_RECEIVED = "DEBT_RECEIVED"
    DEBT_PAYMENT = "DEBT_PAYMENT"
    LOAN_DISBURSEMENT = "LOAN_DISBURSEMENT"
    LOAN_PAYMENT = "LOAN_PAYMENT"
    BNPL_PURCHASE = "BNPL_PURCHASE"
    BNPL_PAYMENT = "BNPL_PAYMENT"
    ASSET_BUY = "ASSET_BUY"
    ASSET_SELL = "ASSET_SELL"
    GOAL_CONTRIBUTION = "GOAL_CONTRIBUTION"
    REFUND = "REFUND"


class Status(enum.StrEnum):
    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"
    VOID = "VOID"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    first_name: Mapped[str | None] = mapped_column(String(200))
    username: Mapped[str | None] = mapped_column(String(200))
    language_code: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ExternalIdentity(Base):
    __tablename__ = "external_identities"
    __table_args__ = (UniqueConstraint("provider", "external_user_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(30))
    external_user_id: Mapped[str] = mapped_column(String(200))


class UserPreference(Base):
    __tablename__ = "user_preferences"
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    preferred_currency: Mapped[str] = mapped_column(String(8), default="TOMAN")
    timezone: Mapped[str] = mapped_column(String(60), default="Asia/Tehran")
    calendar: Mapped[str] = mapped_column(String(20), default="JALALI")
    week_start: Mapped[str] = mapped_column(String(20), default="SATURDAY")
    input_mode: Mapped[str] = mapped_column(String(20), default="HYBRID")
    reconciliation_start: Mapped[time] = mapped_column(Time, default=time(18))
    reconciliation_end: Mapped[time] = mapped_column(Time, default=time(21))
    reconciliation_cooldown_minutes: Mapped[int] = mapped_column(Integer, default=45)
    pattern_detection_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class OwnedNamed(Base):
    __abstract__ = True
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))


class Account(OwnedNamed):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("user_id", "name"),)
    type: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("user_id", "code"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(80))
    name_fa: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20))
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"))
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)


class CategoryAlias(Base):
    __tablename__ = "category_aliases"
    __table_args__ = (UniqueConstraint("user_id", "normalized_alias"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(String(200))
    normalized_alias: Mapped[str] = mapped_column(String(200))


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[TransactionType | None] = mapped_column(Enum(TransactionType))
    amount_irr: Mapped[int | None] = mapped_column(BigInteger)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"))
    category_code: Mapped[str | None] = mapped_column(String(80))
    account_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.id"))
    destination_account_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.id"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    raw_input: Mapped[str | None] = mapped_column(Text)
    payment_method: Mapped[str | None] = mapped_column(String(80))
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(30), default="API")
    status: Mapped[Status] = mapped_column(Enum(Status))
    parse_version: Mapped[str] = mapped_column(String(20), default="1.0")
    parse_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("1"))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    response: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RecurringRule(Base):
    __tablename__ = "recurring_rules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    frequency: Mapped[str] = mapped_column(String(20))
    expected_amount_irr: Mapped[int | None] = mapped_column(BigInteger)
    notification_mode: Mapped[str] = mapped_column(String(20), default="PROMPT")
    next_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ReconciliationSession(Base):
    __tablename__ = "reconciliation_sessions"
    __table_args__ = (UniqueConstraint("user_id", "active"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE")
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    done_date: Mapped[date | None] = mapped_column(Date)


class NotificationOutbox(Base):
    __tablename__ = "notification_outbox"
    __table_args__ = (UniqueConstraint("deduplication_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    deduplication_key: Mapped[str] = mapped_column(String(255))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, default=0)


class FinancialEntity(Base):
    __abstract__ = True
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Debt(FinancialEntity):
    __tablename__ = "debts"


class CreditFacility(FinancialEntity):
    __tablename__ = "credit_facilities"


class Loan(FinancialEntity):
    __tablename__ = "loans"


class Asset(FinancialEntity):
    __tablename__ = "assets"


class Goal(FinancialEntity):
    __tablename__ = "goals"


class Budget(FinancialEntity):
    __tablename__ = "budgets"


class AssetTransaction(Base):
    __tablename__ = "asset_transactions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    price_irr: Mapped[Decimal] = mapped_column(Numeric(38, 18))
    fee_irr: Mapped[int] = mapped_column(BigInteger, default=0)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
