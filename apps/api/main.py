import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from finance.core import (
    bootstrap,
    capture,
    delete_user_data,
    export_csv,
    owned,
    serialize_transaction,
    summary,
)
from finance.models import (
    Account,
    Category,
    CategoryAlias,
    ExternalIdentity,
    Status,
    Transaction,
    TransactionType,
    User,
    UserPreference,
)
from finance.shared.config import get_settings
from finance.shared.database import get_session
from finance.shared.errors import AuthorizationError, FinanceError, NotFoundError
from finance.shared.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_settings()
    yield


app = FastAPI(title="EZFinance Core", version="1.0.0", lifespan=lifespan)
Db = Annotated[Session, Depends(get_session)]


@app.middleware("http")
async def correlation(request: Request, call_next: Any) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))[:100]
    if int(request.headers.get("content-length", "0")) > get_settings().max_request_bytes:
        return JSONResponse(
            {
                "error": {
                    "code": "REQUEST_TOO_LARGE",
                    "message": "Request too large",
                    "requestId": request_id,
                }
            },
            413,
        )
    started = time.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request complete",
        extra={
            "request_id": request_id,
            "operation": request.url.path,
            "duration": round((time.monotonic() - started) * 1000),
            "result": response.status_code,
        },
    )
    return response


@app.exception_handler(FinanceError)
async def finance_error(request: Request, error: FinanceError) -> JSONResponse:
    return JSONResponse(
        {
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
                "requestId": request.headers.get("X-Request-ID"),
            }
        },
        error.status_code,
    )


def current_user(
    session: Db,
    x_external_provider: Annotated[str, Header()] = "telegram",
    x_external_user_id: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if authorization != f"Bearer {get_settings().core_api_key}":
        raise AuthorizationError("Invalid service credential")
    if not x_external_user_id:
        raise AuthorizationError("Missing external identity")
    identity = session.scalar(
        select(ExternalIdentity).where(
            ExternalIdentity.provider == x_external_provider,
            ExternalIdentity.external_user_id == x_external_user_id,
        )
    )
    if not identity:
        raise NotFoundError("User is not onboarded")
    user = session.get(User, identity.user_id)
    assert user
    return user


CurrentUser = Annotated[User, Depends(current_user)]


class Bootstrap(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    external_provider: str = Field(alias="externalProvider")
    external_user_id: str = Field(alias="externalUserId")
    first_name: str | None = Field(None, alias="firstName")
    username: str | None = None
    language_code: str | None = Field(None, alias="languageCode")


class Capture(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    external_provider: str = Field(alias="externalProvider")
    external_user_id: str = Field(alias="externalUserId")
    text: str = Field(min_length=1, max_length=4000)
    occurred_at: datetime | None = Field(None, alias="occurredAt")
    source: str = "API"


class Preferences(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    preferred_currency: Literal["TOMAN", "RIAL"] | None = Field(None, alias="preferredCurrency")
    timezone: str | None = None
    input_mode: Literal["TEXT", "GUIDED", "HYBRID"] | None = Field(None, alias="inputMode")


class Resource(BaseModel):
    name: str
    type: str | None = None
    code: str | None = None
    name_fa: str | None = Field(None, alias="nameFa")
    kind: str | None = None
    category_id: str | None = Field(None, alias="categoryId")
    alias: str | None = None


class TransactionBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    type: TransactionType | None = None
    amount_irr: int | None = Field(None, alias="amountIrr", ge=0)
    category: str | None = None
    occurred_at: datetime | None = Field(None, alias="occurredAt")
    description: str | None = None
    note: str | None = None


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready(session: Db) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ready"}


@app.post("/v1/users/bootstrap")
def onboard(body: Bootstrap, session: Db) -> dict[str, Any]:
    user = bootstrap(
        session,
        body.external_provider,
        body.external_user_id,
        first_name=body.first_name,
        username=body.username,
        language_code=body.language_code,
    )
    return {"id": user.id, "onboarded": True}


@app.get("/v1/users/me")
def me(user: CurrentUser, session: Db) -> dict[str, Any]:
    preference = session.get(UserPreference, user.id)
    assert preference
    return {
        "id": user.id,
        "firstName": user.first_name,
        "preferences": {
            "preferredCurrency": preference.preferred_currency,
            "timezone": preference.timezone,
            "calendar": preference.calendar,
            "weekStart": preference.week_start,
            "inputMode": preference.input_mode,
        },
    }


@app.patch("/v1/users/me/preferences")
def preferences(body: Preferences, user: CurrentUser, session: Db) -> dict[str, Any]:
    item = session.get(UserPreference, user.id)
    assert item
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(item, key, value)
    session.commit()
    return me(user, session)


@app.post("/v1/capture/text")
def capture_text(
    body: Capture,
    session: Db,
    idempotency_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    if authorization != f"Bearer {get_settings().core_api_key}":
        raise AuthorizationError("Invalid service credential")
    user = bootstrap(session, body.external_provider, body.external_user_id)
    return capture(session, user, body.text, body.occurred_at, idempotency_key, body.source.upper())


@app.get("/v1/accounts")
def list_accounts(user: CurrentUser, session: Db) -> list[dict[str, Any]]:
    return [
        {"id": row.id, "name": row.name, "type": row.type}
        for row in session.scalars(select(Account).where(Account.user_id == user.id)).all()
    ]


@app.post("/v1/accounts")
def create_account(body: Resource, user: CurrentUser, session: Db) -> dict[str, Any]:
    item = Account(user_id=user.id, name=body.name, type=body.type or "CASH")
    session.add(item)
    session.commit()
    return {"id": item.id, "name": item.name, "type": item.type}


@app.post("/v1/categories")
def create_category(body: Resource, user: CurrentUser, session: Db) -> dict[str, Any]:
    item = Category(
        user_id=user.id,
        code=body.code or body.name.upper().replace(" ", "_"),
        name_fa=body.name_fa or body.name,
        kind=body.kind or "EXPENSE",
    )
    session.add(item)
    session.commit()
    return {"id": item.id, "code": item.code, "nameFa": item.name_fa}


@app.post("/v1/aliases")
def create_alias(body: Resource, user: CurrentUser, session: Db) -> dict[str, Any]:
    if not body.category_id or not body.alias:
        raise FinanceError("categoryId and alias are required")
    owned(session, Category, body.category_id, user.id)
    item = CategoryAlias(
        user_id=user.id,
        category_id=body.category_id,
        alias=body.alias,
        normalized_alias=body.alias.casefold(),
    )
    session.add(item)
    session.commit()
    return {"id": item.id, "alias": item.alias}


@app.get("/v1/transactions")
def transactions(user: CurrentUser, session: Db) -> list[dict[str, Any]]:
    return [
        serialize_transaction(row)
        for row in session.scalars(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.occurred_at.desc())
        ).all()
    ]


@app.post("/v1/transactions")
def create_transaction(body: TransactionBody, user: CurrentUser, session: Db) -> dict[str, Any]:
    missing = body.type is None or body.amount_irr is None or body.category is None
    item = Transaction(
        user_id=user.id,
        type=body.type,
        amount_irr=body.amount_irr,
        category_code=body.category,
        occurred_at=body.occurred_at or datetime.now(UTC),
        description=body.description,
        note=body.note,
        status=Status.INCOMPLETE if missing else Status.COMPLETE,
    )
    session.add(item)
    session.commit()
    return serialize_transaction(item)


@app.get("/v1/transactions/{transaction_id}")
def get_transaction(transaction_id: str, user: CurrentUser, session: Db) -> dict[str, Any]:
    return serialize_transaction(owned(session, Transaction, transaction_id, user.id))


@app.patch("/v1/transactions/{transaction_id}")
def update_transaction(
    transaction_id: str, body: TransactionBody, user: CurrentUser, session: Db
) -> dict[str, Any]:
    item = owned(session, Transaction, transaction_id, user.id)
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(item, "category_code" if key == "category" else key, value)
    item.status = (
        Status.COMPLETE
        if item.type and item.amount_irr is not None and item.category_code
        else Status.INCOMPLETE
    )
    session.commit()
    return serialize_transaction(item)


@app.post("/v1/transactions/{transaction_id}/void")
def void_transaction(transaction_id: str, user: CurrentUser, session: Db) -> dict[str, Any]:
    item = owned(session, Transaction, transaction_id, user.id)
    item.status = Status.VOID
    session.commit()
    return serialize_transaction(item)


@app.get("/v1/reconciliation/next")
def reconciliation_next(user: CurrentUser, session: Db) -> dict[str, Any] | None:
    item = session.scalar(
        select(Transaction)
        .where(Transaction.user_id == user.id, Transaction.status == Status.INCOMPLETE)
        .order_by(Transaction.created_at)
    )
    return serialize_transaction(item) if item else None


@app.get("/v1/reports/summary")
def report(
    user: CurrentUser, session: Db, start: datetime | None = None, end: datetime | None = None
) -> dict[str, int]:
    finish = end or datetime.now(UTC)
    return summary(session, user.id, start or finish - timedelta(days=30), finish)


@app.get("/v1/exports/csv")
def csv_export(
    user: CurrentUser, session: Db, start: datetime | None = None, end: datetime | None = None
) -> Response:
    finish = end or datetime.now(UTC)
    data = export_csv(session, user.id, start or finish - timedelta(days=3650), finish)
    return Response(
        data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@app.delete("/v1/users/me")
def delete_me(
    user: CurrentUser, session: Db, x_confirm_deletion: Annotated[str | None, Header()] = None
) -> Response:
    if x_confirm_deletion != "DELETE":
        raise FinanceError("Explicit deletion confirmation required")
    delete_user_data(session, user.id)
    return Response(status_code=204)
