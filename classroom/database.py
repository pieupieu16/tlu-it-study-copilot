"""Khởi tạo SQLAlchemy engine + session factory cho classroom subsystem."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, text, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False, "timeout": 30.0} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    pass


# Cột thêm sau khi đã có DB chạy. create_all chỉ tạo bảng mới, không sửa
# bảng cũ, nên thêm tự động nếu chưa có.
_ADDED_COLUMNS: list[tuple[str, str, str]] = [
    ("slides", "page_image", "VARCHAR(255) NOT NULL DEFAULT ''"),
]


def ensure_added_columns() -> None:
    """Thêm các cột mới vào DB đã tồn tại. Chạy được nhiều lần, an toàn dữ liệu."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, column, ddl in _ADDED_COLUMNS:
            if table not in tables:
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            if column in existing:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))


def get_db() -> Iterator[Session]:
    """FastAPI Request-scoped dependency generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Iterator[Session]:
    """Context manager cho Socket.IO coroutines và background worker threads."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
