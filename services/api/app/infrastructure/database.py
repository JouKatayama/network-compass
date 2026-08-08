import os

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Engine

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://network_compass:network_compass_local@localhost:5432/network_compass"
)

metadata = MetaData()


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_database_engine() -> Engine:
    return create_engine(get_database_url(), pool_pre_ping=True)


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
