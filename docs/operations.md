# Operations

## Migrations

Run `uv run alembic upgrade head` before deploying an application revision. Validate a
release against a disposable PostgreSQL database with upgrade, downgrade to base, then
upgrade. Never call `create_all` from an application process.

## Backup and restore

Create encrypted, access-controlled backups with `pg_dump --format=custom --dbname
$DATABASE_URL --file backup.dump`; encrypt the resulting file using the operator's KMS
before it leaves the database host. Test monthly restoration into an isolated database
using `pg_restore --clean --if-exists --dbname $RESTORE_DATABASE_URL backup.dump`, run
`alembic upgrade head`, and verify row counts and report totals. Never place dumps in
source control. Define retention and deletion schedules consistent with local law.

## Failure safety

PostgreSQL transactions contain the domain write and idempotency response. Outbox
deduplication keys make scheduled retries safe. Monitor failed outbox attempts, database
health, HTTP error rate, and backup age. Rotate API, webhook, database, and bot secrets;
logs must contain correlation IDs but not raw messages, notes, reports, or CSV data.
