"""Database type utilities for cross-platform compatibility."""

import uuid
from typing import Any

from sqlalchemy import String, TypeDecorator
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.engine import Dialect


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL UUID when available,
    otherwise uses CHAR(36) for SQLite.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value: Any, dialect: Dialect) -> Any:
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(value)

    def process_result_value(self, value: Any, dialect: Dialect) -> Any:
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


def new_uuid() -> str:
    """Generate a new UUID as string."""
    return str(uuid.uuid4())
