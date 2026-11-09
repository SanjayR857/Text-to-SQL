"""
SQLAlchemy 2.x Declarative Base with standardized constraint naming conventions.
"""
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Explicit naming convention for deterministic Alembic migrations and constraint naming
POSTGRESQL_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "chk_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base class for all application models."""

    metadata = MetaData(naming_convention=POSTGRESQL_NAMING_CONVENTION)
