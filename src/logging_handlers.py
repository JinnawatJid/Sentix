import logging
from src.database import SessionLocal
from src.models import BotLog
from datetime import datetime

class DBHandler(logging.Handler):
    """
    Custom logging handler that saves logs to the PostgreSQL/SQLite database via SQLAlchemy.
    """
    def emit(self, record):
        try:
            # We open a new session for every log to ensure thread safety
            # and avoid tying it to the main web request session.
            db = SessionLocal()

            # Format message
            msg = self.format(record)

            # Context can be passed via extra={'context': ...}
            context = getattr(record, 'context', None)

            log_entry = BotLog(
                timestamp=datetime.utcfromtimestamp(record.created),
                level=record.levelname,
                message=f"{record.name}: {msg}", # Prefix with Logger Name
                context=context
            )

            db.add(log_entry)
            db.commit()
            db.close()
        except Exception:
            # If logging fails, fall back to standard error to avoid infinite loops
            self.handleError(record)
