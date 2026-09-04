"""
Real async SQLAlchemy session setup (SQLite by default, swap DATABASE_URL
for Postgres with no code change). This replaces the in-memory dicts that
app/agents/tools/*.py used to use directly.
"""
from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.models import Base

settings = get_settings()


def _ensure_sqlite_directory_exists(database_url: str) -> None:
    """
    Real bug hit on a fresh Windows clone: sqlite3.connect() does NOT
    create missing parent directories, only the database file itself (and
    only if the directory already exists) -- "unable to open database
    file" with no other explanation. `var/` is gitignored and nothing
    else in this codebase creates it, so this failed on first run on any
    platform, not just Windows.

    Uses SQLAlchemy's own make_url() rather than hand-rolled urllib
    parsing -- an earlier version of this fix used urlparse().path with a
    blanket .lstrip("/"), which is WRONG for four-slash absolute-path
    sqlite URLs (sqlite:////abs/path.db): it strips the leading slash
    that makes the path absolute, silently turning it into a relative
    path resolved against the wrong directory. Caught by testing both
    forms directly, not assumed correct from the three-slash case alone.
    """
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database:
        return  # not sqlite, or sqlite in-memory (":memory:" / no database)
    directory = os.path.dirname(url.database)
    if directory:
        os.makedirs(directory, exist_ok=True)


_ensure_sqlite_directory_exists(settings.database_url)

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables. Call once at app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session
