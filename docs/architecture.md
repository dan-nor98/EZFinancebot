# Architecture

The system is a modular monolith with three processes. Finance Core exposes HTTP and
owns parsing, ownership, accounting semantics, idempotency, reporting, and persistence.
The Telegram Gateway authenticates webhooks, translates transport DTOs, and renders
Persian UI; it contains no financial classifications. The worker prepares durable
outbox messages while only the gateway sends them.

PostgreSQL is the source of truth. Redis may be introduced only for ephemeral locks,
rate limits, cache, or conversation state. All writes are committed atomically and
schema changes occur only through Alembic.

## Accounting invariants

Only `EXPENSE` and `BNPL_PURCHASE` affect expense totals; BNPL repayment, transfers,
principal, asset buys, lending, and goal contributions do not. Only `INCOME` affects
income totals. Fiat is integer IRR; asset values use `NUMERIC(38,18)`/`Decimal`.

