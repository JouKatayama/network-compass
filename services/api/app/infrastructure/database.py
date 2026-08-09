import os

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://network_compass:network_compass_local@localhost:5432/network_compass"
)

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


metadata = Base.metadata


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_database_engine(database_url: str | None = None) -> Engine:
    return create_engine(database_url or get_database_url(), pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )


def check_database_connection(engine: Engine | None = None) -> bool:
    active_engine = engine or create_database_engine()
    owns_engine = engine is None

    try:
        with active_engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar_one()
            return bool(result == 1)
    finally:
        if owns_engine:
            active_engine.dispose()


def main() -> None:
    if not check_database_connection():
        raise SystemExit("database connection check failed")
    print("database connection ok")


if __name__ == "__main__":
    main()
