# PRD — Telegram Personal Finance Management Bot

**Version:** 1.0
**Status:** Final for Development
**Target Market:** Iranian users
**Primary Interface:** Telegram Bot
**Bot Language:** Persian
**Accepted Input Languages:** Persian, English, and mixed Persian/English
**Parsing:** Deterministic rules, Regex, dictionaries, and statistical heuristics; no LLM dependency
**Architecture:** Finance Core Services + Telegram Gateway

---

# 1. Product Summary

The product is a personal finance management system delivered initially through Telegram.

The primary product principle is **minimum-friction financial data entry**.

A user should be able to send:

```text
350k taxi
```

or:

```text
۳۵۰ هزار اسنپ
```

or:

```text
350k اسنپ
```

and have the same transaction recorded.

The bot must not force users to complete every field during initial capture. Missing information can be recorded and completed later through a reconciliation mechanism.

Telegram acts only as a gateway. Financial logic, parsing, reporting, loans, debts, assets, budgets, and other business capabilities must exist independently in the Finance Core.

---

# 2. Product Goals

| ID   | Goal                                                                                  |
| ---- | ------------------------------------------------------------------------------------- |
| G-01 | Make financial data entry possible with one short message.                            |
| G-02 | Support Persian, English, and mixed-language transaction inputs.                      |
| G-03 | Keep all bot-generated messages and UI in Persian.                                    |
| G-04 | Avoid requiring AI or an LLM for normal product operation.                            |
| G-05 | Allow incomplete transaction capture without interrupting the user.                   |
| G-06 | Automatically reconcile incomplete information later.                                 |
| G-07 | Detect recurring financial and behavioral patterns.                                   |
| G-08 | Correctly distinguish expenses, income, transfers, liabilities, assets, and savings.  |
| G-09 | Support debts, BNPL, loans, investments, budgets, and goals.                          |
| G-10 | Provide reusable financial services independent of Telegram.                          |
| G-11 | Keep financial calculations precise and auditable.                                    |
| G-12 | Provide a foundation that can later support mobile, web, or other messaging gateways. |

---

# 3. Non-Goals

Version 1 does not require:

* LLM-based transaction understanding.
* Automatic bank account synchronization.
* Open Banking integration.
* Automatic execution of payments.
* Investment trading.
* Tax filing.
* Financial advice.
* Social/community features.
* Multi-user household accounting.
* Business accounting.

The architecture must not prevent these capabilities from being added later.

---

# 4. Language Strategy

## 4.1 Bot Interface

All bot-generated user-facing content must be Persian.

This includes:

* menus
* buttons
* notifications
* errors
* transaction confirmations
* reports
* reconciliation messages
* reminders
* settings
* budget alerts
* loan reminders
* goal updates

Example:

```text
هزینه ثبت شد

مبلغ: ۳۵۰٬۰۰۰ تومان
دسته‌بندی: حمل‌ونقل
شرح: اسنپ
تاریخ: امروز
```

## 4.2 User Input

User input can contain:

```text
Persian
English
Persian + English
Persian digits
Arabic digits
Latin digits
```

All of the following are valid:

```text
350k taxi
۳۵۰ هزار تاکسی
350 هزار snapp
۳۵۰k اسنپ
2m clothes
۲ میلیون لباس
salary 50m
حقوق 50m
دیروز 450k taxi
```

## 4.3 Internal Language

Code, enums, APIs, database fields, domain names, and identifiers remain English.

Example:

```text
TRANSPORTATION
EXPENSE
INCOME
ASSET_BUY
LOAN_PAYMENT
```

Presentation layer:

```text
TRANSPORTATION → حمل‌ونقل
```

Parser aliases:

```text
taxi
snapp
تاکسی
اسنپ
تپسی
```

all map to:

```text
TRANSPORTATION
```

No translation API or LLM should be required.

---

# 5. Iranian Localization

Default configuration:

| Setting               | Default     |
| --------------------- | ----------- |
| Timezone              | Asia/Tehran |
| Calendar              | Jalali      |
| Week Start            | Saturday    |
| Bot Language          | Persian     |
| Display Currency      | Toman       |
| Alternative Currency  | Rial        |
| Input Mode            | Hybrid      |
| Reconciliation Window | 18:00–21:00 |
| Pattern Detection     | Enabled     |
| Reminders             | Enabled     |

The user may select either **Toman** or **Rial** as the preferred display denomination.

Internally, Iranian fiat amounts should use a canonical representation.

Recommended:

```text
Internal fiat unit = IRR
```

Example:

```text
User enters:
500,000 Toman

Stored:
5,000,000 IRR
```

---

# 6. Architecture

The system consists of three main applications.

```text
Telegram
    │
    ▼
Telegram Gateway
    │
    ▼
Finance Core API
    │
    ├── PostgreSQL
    └── Redis
         
Scheduler Worker
    │
    ├── Finance Core
    └── Notification Outbox
             │
             ▼
      Telegram Gateway
```

## 6.1 Finance Core

Responsible for:

* users
* preferences
* accounts
* categories
* transactions
* parser
* ledger
* recurring rules
* reconciliation
* pattern detection
* debts
* BNPL
* loans
* assets
* budgets
* goals
* reports
* exports
* notifications

Finance Core contains all financial business rules.

## 6.2 Telegram Gateway

Responsible only for:

* receiving Telegram updates
* displaying Persian UI
* inline keyboards
* conversational states
* calling Finance Core APIs
* sending notifications generated by Finance Core

It must not contain financial calculations or domain rules.

## 6.3 Scheduler Worker

Responsible for asynchronous and scheduled processes such as:

* reconciliation
* recurring transaction prompts
* loan reminders
* BNPL reminders
* budget alerts
* pattern detection
* goal reminders
* notification delivery preparation

---

# 7. User Profile

Telegram already provides basic identity.

Store:

```text
Telegram User ID
First Name
Username
Telegram language
```

Telegram User ID is the external identity.

Username must never be used as the primary identifier.

Additional preferences:

```text
preferred_currency
timezone
input_mode
reconciliation_start
reconciliation_end
reconciliation_cooldown
pattern_detection_enabled
reminders_enabled
```

Minimal onboarding should only ask for necessary preferences.

Default currency:

```text
Toman
```

---

# 8. Accounts

Users may optionally maintain multiple financial accounts.

Initial account types:

```text
CASH
BANK
CARD
WALLET
```

Examples:

```text
ملت
سامان
کیف پول
نقد
دیجی‌پی
```

A transaction does not require an account to be captured.

Account information can be completed later.

Transfers between the user's own accounts must not be classified as expenses.

Example:

```text
5m Mellat to cash
```

means:

```text
Mellat: -5m
Cash: +5m
Net worth impact: 0
Expense impact: 0
```

---

# 9. Categories

Default expense categories:

| Code           | Persian      |
| -------------- | ------------ |
| TRANSPORTATION | حمل‌ونقل     |
| FOOD           | خوراک        |
| CLOTHING       | پوشاک        |
| HOUSING        | مسکن         |
| UTILITIES      | قبوض و خدمات |
| SUBSCRIPTION   | اشتراک       |
| HEALTH         | سلامت        |
| EDUCATION      | آموزش        |
| ENTERTAINMENT  | سرگرمی       |
| GIFT           | هدیه         |
| FINANCIAL_FEE  | هزینه مالی   |
| TAX            | مالیات       |
| OTHER          | سایر         |

Default income categories:

| Code              | Persian            |
| ----------------- | ------------------ |
| SALARY            | حقوق               |
| FREELANCE         | فریلنس             |
| BONUS             | پاداش              |
| GIFT_INCOME       | هدیه دریافتی       |
| INVESTMENT_INCOME | درآمد سرمایه‌گذاری |
| REFUND            | بازپرداخت          |
| OTHER_INCOME      | سایر درآمدها       |

Users can create:

* custom categories
* subcategories
* aliases

Example:

```text
اسنپ → TRANSPORTATION
snapp → TRANSPORTATION
coffee → FOOD
قهوه → FOOD
```

Unknown categories should be marked as unclassified rather than automatically becoming `OTHER`.

---

# 10. Transaction Capture

The primary interaction is plain text.

Example:

```text
350k taxi
```

Expected interpretation:

```text
Type: EXPENSE
Amount: 350000 Toman
Category: TRANSPORTATION
Date: now
```

Another example:

```text
حقوق 50m
```

Expected:

```text
Type: INCOME
Amount: 50,000,000 Toman
Category: SALARY
```

---

# 11. Parser

The parser must be implemented as a deterministic pipeline rather than a single large Regex.

```text
Raw Message
    ↓
Unicode Normalization
    ↓
Character Normalization
    ↓
Digit Normalization
    ↓
Tokenization
    ↓
Amount Extraction
    ↓
Currency Detection
    ↓
Intent Detection
    ↓
Date Detection
    ↓
Category / Alias Matching
    ↓
Account Detection
    ↓
Debt / Loan / Asset Detection
    ↓
Tag Extraction
    ↓
Remaining Text → Note
    ↓
Validation
```

## 11.1 Supported Amount Formats

Examples:

```text
350000
۳۵۰۰۰۰

350k
۳۵۰k

350 thousand
350 هزار
۳۵۰ هزار

2m
۲m

2 million
2 میلیون
۲ میلیون

2.5m
۲.۵m

1b
۱b

1 billion
1 میلیارد
```

Money must never use floating-point arithmetic.

Use:

```text
BIGINT
Decimal
NUMERIC
```

---

# 12. Notes, Description and Tags

Every transaction supports:

```text
note
description
tags[]
```

Example:

```text
450k taxi #work جلسه شرکت
```

Possible interpretation:

```text
Amount: 450,000 Toman
Category: TRANSPORTATION
Tag: work
Note: جلسه شرکت
```

Notes should be searchable.

---

# 13. Guided Data Entry

Users uncomfortable with text input can use buttons.

Flow:

```text
ثبت تراکنش
      ↓
هزینه | درآمد
      ↓
مبلغ
      ↓
دسته‌بندی
      ↓
حساب
      ↓
توضیحات
      ↓
ثبت
```

Supported interaction modes:

```text
TEXT
GUIDED
HYBRID
```

Default:

```text
HYBRID
```

A user must be able to move between text and buttons.

---

# 14. Incomplete Transactions

Transaction capture must not require all fields.

Required fields for a complete standard transaction:

```text
type
amount
occurred_at
category
```

Example:

```text
taxi
```

can create:

```text
Type: EXPENSE
Category: TRANSPORTATION
Amount: NULL
Date: now
Status: INCOMPLETE
```

The user should not necessarily be interrupted immediately.

---

# 15. Reconciliation

Default reconciliation window:

```text
18:00–21:00
```

Suppose six incomplete transactions exist.

The bot chooses one incomplete transaction and asks:

```text
صبح یک هزینه اسنپ ثبت کرده بودی.
مبلغش چقدر بود؟
```

After receiving an answer:

```text
ادامه
بعداً
امروز دیگه نپرس
```

### ادامه

Show another incomplete transaction immediately.

### بعداً

Pause reconciliation.

Default cooldown:

```text
30–60 minutes
```

The bot may continue later during the same reconciliation window.

### امروز دیگه نپرس

Stop reconciliation until the following day.

Only one unsolicited reconciliation question may be active at a time.

---

# 16. Recurring Transactions

Two kinds of recurring behavior are supported.

## Fixed Recurrence

Example:

```text
اجاره
20m
monthly
```

## Recurring Question

Example:

At the beginning of each month:

```text
حقوق این ماهت چقدر بود؟
```

This supports recurring income whose amount varies.

Recurring rules should include:

```text
frequency
expected_date
category
expected_amount
amount_tolerance
notification_mode
next_due_at
```

Notification modes:

```text
PROMPT
REMIND
AUTO_CREATE
```

`AUTO_CREATE` should not be the default.

---

# 17. Pattern Detection

The system should recognize repeated behavior automatically without AI.

Example:

A user records approximately the same taxi transaction every morning.

Pattern dimensions:

```text
category
merchant/alias
amount range
time range
weekday
recurrence frequency
```

Example detection:

```text
08:10 taxi
08:15 taxi
08:06 taxi
08:21 taxi
08:12 taxi
```

The system can propose:

```text
به نظر می‌رسد بیشتر روزها حدود ساعت ۸ صبح هزینه رفت‌وآمد داری.
این الگو را ثبت کنم؟
```

Detected patterns must require user confirmation before becoming recurring rules.

Initial recommended rules:

| Pattern | Initial Detection                              |
| ------- | ---------------------------------------------- |
| Daily   | At least 5 occurrences in approximately 7 days |
| Weekly  | At least 3 similar occurrences across 4 weeks  |
| Monthly | At least 3 similar monthly occurrences         |

Thresholds should remain configurable.

---

# 18. Debts

Support:

```text
RECEIVABLE
PAYABLE
```

Example:

```text
قرض دادم به علی 5m
```

Financial result:

```text
Cash: -5m
Receivable: +5m
Expense: 0
```

Example:

```text
10m قرض گرفتم از رضا
```

Result:

```text
Cash: +10m
Payable: +10m
Income: 0
```

Debt information:

```text
counterparty
direction
original_amount
remaining_amount
currency
created_at
due_date
status
note
```

Partial repayments must be supported.

---

# 19. Shared Expenses

Transactions may contain amounts owed by another person.

Example:

```text
Dinner: 2m
My share: 1m
Ali owes: 1m
```

The transaction creates:

```text
Expense attributable to user: 1m
Receivable from Ali: 1m
```

Settlement of the receivable must not be counted again as income.

---

# 20. Credit and BNPL

Credit and BNPL must be modeled separately from normal expenses.

When an item is purchased using BNPL:

```text
Expense = purchase amount
Liability = outstanding BNPL amount
```

When installments are paid:

```text
Cash decreases
Liability decreases
```

Only fees or interest are additional expenses.

The purchase itself must not be counted again during installment repayment.

Track:

```text
provider
purchase
principal
fees
installment_count
installments
next_due_date
remaining_balance
status
```

---

# 21. Loans

Bank loans require a dedicated module.

Store:

```text
provider
principal
net_amount_received
nominal_rate
subscription_fee
origination_fee
recurring_fee
commission
term
start_date
installments
early_repayment_rules
```

Installment data:

```text
due_date
principal_component
interest_component
fee_component
total_due
paid_amount
status
paid_at
```

Calculate:

```text
Net funds received
Total repayment
Total financing cost
Remaining principal
Remaining payments
Next installment
Effective monthly cost
Effective annual cost
```

Effective cost should be based on actual cash flows, including subscription fees and commissions.

An XIRR-style calculation should be used where payment dates are irregular.

---

# 22. Assets and Investments

Support assets such as:

```text
Gold
Silver
USD
EUR
ETH
BTC
```

An asset purchase is a conversion of value, not an expense.

Example:

```text
Buy 0.05 ETH
```

creates:

```text
Cash decreases
ETH asset increases
```

Transaction fees are expenses.

Store:

```text
asset
quantity
transaction_type
price
base_value
fees
date
account
```

Calculate:

```text
Current quantity
Cost basis
Average purchase price
Current market value
Realized P/L
Unrealized P/L
```

Initial cost basis:

```text
Weighted Average Cost
```

Market prices must be accessed through a provider abstraction.

Manual prices can be supported initially.

---

# 23. Budgets

Support:

```text
Overall monthly budget
Category monthly budget
```

Example:

```text
خوراک: 8m
رفت‌وآمد: 5m
کل هزینه ماهانه: 40m
```

Default alerts:

```text
75%
100%
```

Only genuine expenses count toward budgets.

The following do not:

```text
Account transfers
Loan disbursement
Loan principal repayment
Asset purchases
Savings goal transfers
Debt principal movement
```

---

# 24. Saving Goals

Users can define financial goals.

Example:

```text
نام: مک‌بوک
هدف: 150m
تاریخ هدف: 1406/01/01
```

Store:

```text
name
target_amount
current_amount
target_date
status
```

Display:

```text
Progress
Remaining amount
Completion percentage
Required monthly contribution
Estimated completion date
```

Funding a goal is not an expense.

---

# 25. Reminders

Reminder sources:

| Type              | Example                           |
| ----------------- | --------------------------------- |
| Recurring income  | Ask for monthly salary            |
| Recurring expense | Rent                              |
| Reconciliation    | Missing amount/category           |
| Pattern           | Missing expected taxi transaction |
| Loan              | Upcoming installment              |
| BNPL              | Installment                       |
| Debt              | Due receivable/payable            |
| Budget            | 75% / 100% threshold              |
| Goal              | Progress reminder                 |

Reminder actions:

```text
انجام شد
بعداً یادآوری کن
غیرفعال کردن یادآوری
```

Users can disable individual reminder categories.

---

# 26. Reports

Supported periods:

```text
امروز
این هفته
این ماه
ماه قبل
بازه دلخواه
```

Definitions:

```text
Week = Saturday through Friday
Month = Jalali calendar month
```

Reports can contain:

```text
Income
Expenses
Net cash flow
Largest expense categories
Account balances
Receivables
Payables
Loan obligations
BNPL obligations
Asset values
Investment P/L
Goal progress
Net worth
```

Telegram reports should prioritize text over complex graphical output.

---

# 27. CSV Export

Users can export their transactions.

Default range:

```text
Current month
```

Custom range must also be available.

Initial columns:

```text
date
type
amount
currency
category
account
tags
note
```

Requirements:

```text
UTF-8
Excel-compatible
CSV injection protection
```

The bot UI remains Persian.

The underlying column names may remain English for interoperability.

---

# 28. Notification Outbox

Finance Core must never directly send Telegram messages.

Create:

```text
notification_outbox
```

Fields:

```text
id
user_id
channel
template_key
payload
scheduled_at
status
attempt_count
deduplication_key
created_at
sent_at
```

Flow:

```text
Finance Core / Worker
        ↓
Notification Outbox
        ↓
Telegram Gateway
        ↓
Telegram
```

This allows future delivery channels such as:

```text
Mobile Push
SMS
Email
Web
```

---

# 29. Core Transaction Semantics

These rules are mandatory.

| Event                         |                            Expense |                 Income |
| ----------------------------- | ---------------------------------: | ---------------------: |
| Food purchase                 |                                Yes |                     No |
| Salary                        |                                 No |                    Yes |
| Transfer between accounts     |                                 No |                     No |
| Lend money                    |                                 No |                     No |
| Borrow money                  |                                 No |                     No |
| Debt principal repayment      |                                 No |                     No |
| Debt interest                 |                                Yes |                     No |
| Receive bank loan             |                                 No |                     No |
| Loan principal payment        |                                 No |                     No |
| Loan interest                 |                                Yes |                     No |
| Buy gold                      |                                 No |                     No |
| Sell asset with profit        | Realized P/L calculated separately | No normal income entry |
| Asset transaction fee         |                                Yes |                     No |
| Fund goal                     |                                 No |                     No |
| Receive repayment from friend |                                 No |                     No |
| BNPL purchase                 |                                Yes |                     No |
| BNPL principal repayment      |                                 No |                     No |
| BNPL fee                      |                                Yes |                     No |

---

# 30. Core Data Model

Initial core tables:

```text
users
external_identities
user_preferences

accounts

categories
category_aliases

transactions
tags
transaction_tags

recurring_rules
pattern_candidates

reconciliation_sessions

debts
debt_payments

credit_facilities
credit_transactions
credit_installments

loans
loan_fees
loan_installments

assets
asset_transactions
asset_price_snapshots

budgets

goals
goal_contributions

notification_preferences
notification_outbox

idempotency_keys
```

Core financial information should use relational columns rather than generic JSON structures.

JSON may be used for flexible metadata.

---

# 31. Transaction Model

Recommended transaction fields:

```text
id UUID
user_id UUID

type

amount_irr BIGINT NULL

category_id UUID NULL
account_id UUID NULL

occurred_at TIMESTAMPTZ

description TEXT NULL
note TEXT NULL

raw_input TEXT NULL

source

status

parse_version
parse_confidence

created_at
updated_at
```

Initial transaction types:

```text
EXPENSE
INCOME

TRANSFER

DEBT_GIVEN
DEBT_RECEIVED
DEBT_PAYMENT

LOAN_DISBURSEMENT
LOAN_PAYMENT

BNPL_PURCHASE
BNPL_PAYMENT

ASSET_BUY
ASSET_SELL

GOAL_CONTRIBUTION

REFUND
```

Status:

```text
INCOMPLETE
COMPLETE
VOID
```

---

# 32. Primary API

## Users

```http
POST  /v1/users/bootstrap
GET   /v1/users/me
PATCH /v1/users/me/preferences
```

## Capture

```http
POST /v1/capture/text
```

Example:

```json
{
  "externalProvider": "telegram",
  "externalUserId": "123456",
  "text": "۳۵۰k taxi",
  "occurredAt": "2026-09-18T10:30:00+03:30"
}
```

Possible response:

```json
{
  "result": "TRANSACTION_CREATED",
  "transaction": {
    "type": "EXPENSE",
    "amountIrr": 3500000,
    "category": "TRANSPORTATION",
    "status": "COMPLETE"
  }
}
```

## Transactions

```http
GET   /v1/transactions
POST  /v1/transactions
GET   /v1/transactions/{id}
PATCH /v1/transactions/{id}
POST  /v1/transactions/{id}/void
```

## Reconciliation

```http
GET  /v1/reconciliation/next
POST /v1/reconciliation/{id}/answer
POST /v1/reconciliation/{id}/snooze
POST /v1/reconciliation/done-today
```

## Reports

```http
GET /v1/reports/summary
```

## Export

```http
GET /v1/exports/csv
```

---

# 33. Idempotency

Telegram updates may be delivered multiple times.

Every Telegram-originating write operation requires an idempotency key.

Recommended:

```text
telegram:{bot_id}:{update_id}
```

Repeating the same update must return the previous result instead of creating another transaction.

---

# 34. Security and Privacy

Requirements:

* All financial records scoped by internal user ID.
* Gateway authenticates to Finance Core.
* Telegram webhook validation required.
* TLS required.
* Database encryption at rest.
* Encrypted backups.
* Raw financial messages excluded from standard logs.
* Secrets must never exist in source control.
* Input rate limiting required.
* CSV injection protection required.
* User can delete all personal financial data.
* Destructive deletion requires explicit confirmation.
* No external analytics SDK by default.
* No financial information stored solely in Redis.

---

# 35. Non-Functional Requirements

## Financial Precision

Never use:

```python
float
```

for money.

Use integer IRR for Iranian fiat.

Use:

```text
NUMERIC(38,18)
```

or equivalent Decimal representation for asset quantities and prices.

## Time

Persist timestamps in UTC.

Convert according to the user's configured timezone at the application boundary.

Default:

```text
Asia/Tehran
```

## Reliability

The following must be idempotent:

```text
Telegram writes
scheduled jobs
notification generation
recurring processing
```

## Logging

Structured logs may contain:

```text
request_id
internal_user_id
operation
duration
result
```

Do not log:

```text
raw transaction message
notes
bank information
CSV contents
financial report contents
```

---

# 36. Recommended Technology Stack

| Component        | Technology              |
| ---------------- | ----------------------- |
| Language         | Python 3.13             |
| Package Manager  | uv                      |
| API              | FastAPI                 |
| Telegram Gateway | aiogram 3               |
| Validation       | Pydantic                |
| ORM              | SQLAlchemy 2            |
| Database         | PostgreSQL              |
| Migrations       | Alembic                 |
| Temporary State  | Redis                   |
| HTTP Client      | httpx                   |
| Testing          | pytest                  |
| Property Testing | Hypothesis              |
| Linting          | Ruff                    |
| Static Typing    | mypy                    |
| Containers       | Docker / Docker Compose |
| CI               | GitHub Actions          |

Use a **modular monolith** initially.

Do not start with microservices.

---

# 37. Repository Structure

```text
telegram-finance/
│
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── docker-compose.yml
├── .env.example
│
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   └── adr/
│
├── apps/
│   ├── api/
│   │   └── main.py
│   │
│   ├── telegram_gateway/
│   │   └── main.py
│   │
│   └── worker/
│       └── main.py
│
├── src/
│   └── finance/
│       ├── users/
│       ├── accounts/
│       ├── categories/
│       ├── transactions/
│       ├── parser/
│       ├── recurring/
│       ├── reconciliation/
│       ├── patterns/
│       ├── debts/
│       ├── credit/
│       ├── loans/
│       ├── assets/
│       ├── budgets/
│       ├── goals/
│       ├── reports/
│       ├── notifications/
│       └── shared/
│
├── migrations/
│
└── tests/
    ├── unit/
    ├── integration/
    ├── contract/
    └── parser_cases/
```

---

# 38. Development Phases

### Phase 0 — Foundation

Implement repository structure, PostgreSQL, SQLAlchemy, Alembic, configuration, Docker Compose, CI, logging, errors, and tests.

### Phase 1 — User Foundation

Implement Telegram identity, preferences, accounts, categories, aliases, and Iranian defaults.

### Phase 2 — Parser

Implement normalization, Persian/English numbers, Toman/Rial recognition, intent detection, dates, categories, notes, and aliases.

### Phase 3 — Transactions

Implement transaction creation, incomplete records, editing, voiding, idempotency, and `/capture/text`.

**First major milestone:**

```text
350k اسنپ
```

must successfully produce:

```text
هزینه ثبت شد
۳۵۰٬۰۰۰ تومان
حمل‌ونقل
```

with the transaction persisted in PostgreSQL.

### Phase 4 — Telegram Gateway

Implement webhook, Persian UI, text capture, buttons, settings, confirmations, and errors.

### Phase 5 — Reports and Export

Implement daily, weekly, Jalali monthly reports and CSV export.

### Phase 6 — Reconciliation and Recurrence

Implement incomplete transaction queues, evening reconciliation, recurring rules, recurring prompts, snoozing, and notification outbox.

### Phase 7 — Pattern Detection

Implement deterministic daily, weekly, and monthly pattern detection.

### Phase 8 — Debts, BNPL and Loans

Implement receivables, payables, settlements, credit facilities, installments, financing cost, XIRR, and reminders.

### Phase 9 — Assets

Implement holdings, asset transactions, cost basis, realized/unrealized P/L, and pricing abstraction.

### Phase 10 — Budgets and Goals

Implement budgets, thresholds, saving goals, contributions, and progress calculations.

---

# 39. Parser Testing Requirements

Maintain a permanent regression corpus.

Examples:

```text
350k taxi
۳۵۰ هزار اسنپ
350k اسنپ
۳۵۰ هزار taxi

2m clothes
۲ میلیون لباس

salary 50m
حقوق 50m

دیروز 450k taxi

قرض دادم به علی 5m
10m قرض گرفتم از رضا

0.1 ETH خریدم

قهوه
2m
```

Each case should define expected structured output.

Example:

```json
{
  "input": "۳۵۰ هزار اسنپ",
  "expected": {
    "type": "EXPENSE",
    "amountIrr": 3500000,
    "category": "TRANSPORTATION"
  }
}
```

Every parser defect must become a permanent regression test.

---

# 40. Codex Development Policy

`AGENTS.md` should establish these mandatory rules:

```markdown
# Product Rules

The Telegram user interface is Persian.

User transaction input can be Persian, English, or mixed.

Internal domain names, API schemas, enums, database fields,
and source code remain English.

No LLM or external translation service may be required
for transaction parsing.

# Architecture

Telegram Gateway is an adapter only.

Business and financial rules belong in Finance Core.

PostgreSQL is the source of truth.

Redis is only for temporary state, caching, rate limiting,
or conversational state.

# Financial Safety

Never use float for monetary calculations.

Store Iranian fiat canonically in IRR.

Use Decimal / NUMERIC for assets and prices.

Transfers are not expenses.

Borrowing is not income.

Lending is not an expense.

Loan principal repayment is not an expense.

Loan fees and interest are expenses.

Asset purchases are not expenses.

Goal contributions are not expenses.

BNPL purchase is recorded as an expense once.
BNPL principal repayment must not create another expense.

# Testing

Every feature requires tests.

Every parser bug requires a permanent regression case.

Before completing a task run:

uv run ruff check .
uv run mypy .
uv run pytest

# Scope

Implement only the requested development ticket.

Do not perform unrelated refactors.
```

---

# 41. MVP Definition

The first production-capable MVP is complete when a user can:

```text
/start
```

and then send:

```text
۳۵۰ هزار اسنپ
```

or:

```text
350k taxi
```

and receive a Persian confirmation.

The MVP must support:

* Telegram identity
* Toman/Rial preference
* Persian UI
* Persian/English/mixed input
* expense capture
* income capture
* categories
* aliases
* accounts
* notes
* incomplete transactions
* editing
* undo/void
* daily reconciliation
* basic recurring rules
* daily/weekly/monthly reports
* CSV export
* idempotency
* data deletion
* PostgreSQL persistence

Loans, BNPL, assets, budgets, goals, and advanced pattern detection follow after the core capture/reconciliation loop is stable.

---

# 42. Product Principle

The central behavior of the system is:

```text
Capture now
Understand deterministically
Store safely
Ask only when necessary
Complete later
Report correctly
```

The bot should optimize for **the smallest possible interruption at the moment money is spent or received**, while the Finance Core preserves enough structure to become a complete personal financial management platform later.
