import time
from datetime import UTC, datetime

from sqlalchemy import select

from finance.models import NotificationOutbox
from finance.shared.database import SessionLocal


def prepare_notifications() -> int:
    """Mark due outbox records ready; the gateway remains the only Telegram sender."""
    with SessionLocal() as session:
        records = session.scalars(
            select(NotificationOutbox).where(
                NotificationOutbox.status == "PENDING",
                NotificationOutbox.scheduled_at <= datetime.now(UTC),
            )
        ).all()
        for record in records:
            record.status = "READY"
        session.commit()
        return len(records)


def run() -> None:
    while True:
        prepare_notifications()
        time.sleep(30)


if __name__ == "__main__":
    run()
