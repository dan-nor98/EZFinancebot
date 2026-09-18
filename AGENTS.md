# Product Rules

All Telegram-generated user interface content is Persian.

User input can be Persian, English, or mixed.

Source code, internal domain identifiers, API schemas, enums, and database fields
remain English.

Transaction parsing must not depend on an LLM or external translation service.

# Architecture

Telegram Gateway is an adapter only.

Every business and financial rule belongs in Finance Core.

PostgreSQL is the source of truth.

Redis is limited to temporary state, caching, rate limiting, locks, and
conversational state.

# Financial Safety

Never use `float` for financial calculations.

Store Iranian fiat canonically as integer IRR.

Use `Decimal` and PostgreSQL `NUMERIC` for asset quantities and prices.

Transfers are not expenses.

Borrowing is not income.

Lending is not an expense.

Loan principal repayments are not expenses.

Loan interest and fees are expenses.

Asset purchases are not expenses.

Goal contributions are not expenses.

A BNPL purchase is counted as an expense exactly once. Repayment of its
principal must not create another expense.

# Testing

Every feature requires tests.

Every parser defect requires a permanent regression case.

Before completing a task, run:

```text
uv run ruff check .
uv run mypy .
uv run pytest
```

# Scope

Implement only the requested development ticket.

Do not perform unrelated refactoring.
