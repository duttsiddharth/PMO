"""Database engine / session factory.

Centralises engine creation so every module shares one configured engine and
a thread-safe scoped session. Works transparently for SQLite or PostgreSQL.
"""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

import config
from core.models import Base

# SQLite needs check_same_thread disabled for Streamlit's threading model.
_connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(config.DATABASE_URL, echo=False, connect_args=_connect_args, future=True)
SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
Session = scoped_session(SessionFactory)


def init_db() -> None:
    """Create all tables if they do not yet exist."""
    Base.metadata.create_all(engine)


def reset_db() -> None:
    """Drop and recreate every table. Used by seeding and tests."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    s = Session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
