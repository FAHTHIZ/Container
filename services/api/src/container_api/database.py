# SPDX-License-Identifier: Apache-2.0
"""SQLAlchemy engine, session factory, and request-scoped database dependency."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from container_api.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


def build_engine(database_url: str | None = None):
    """Build an engine with safe defaults for the selected database."""
    url = database_url or settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)

    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield one database session per request and always close it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
