"""Cloud SQL/PostgreSQL option; existing sqlite3 transactions remain the local default."""

import re
from collections.abc import Mapping
from functools import lru_cache
from sqlalchemy import create_engine, text


class Row(Mapping):
    def __init__(self, row):
        self.values = tuple(row)
        self.mapping = row._mapping

    def __getitem__(self, key):
        return self.values[key] if isinstance(key, int) else self.mapping[key]

    def __iter__(self):
        return iter(self.mapping)

    def __len__(self):
        return len(self.mapping)


class Result:
    def __init__(self, result):
        self.result = result

    def fetchone(self):
        row = self.result.fetchone()
        return Row(row) if row is not None else None

    def __iter__(self):
        return (Row(row) for row in self.result)


def postgres_sql(statement, parameters=()):
    if statement.startswith("PRAGMA") or statement == "BEGIN IMMEDIATE":
        return "SELECT 1", {}
    statement = statement.replace("INTEGER PRIMARY KEY", "BIGSERIAL PRIMARY KEY")
    statement = re.sub(r"\bREAL\b", "DOUBLE PRECISION", statement)
    if statement.startswith("INSERT OR IGNORE INTO"):
        statement = (
            statement.replace("INSERT OR IGNORE INTO", "INSERT INTO", 1)
            + " ON CONFLICT DO NOTHING"
        )
    parts = statement.split("?")
    if len(parts) - 1 != len(parameters):
        raise ValueError("SQL parameter count mismatch")
    sql = "".join(
        part + (f":p{i}" if i < len(parameters) else "") for i, part in enumerate(parts)
    )
    return sql, {f"p{i}": value for i, value in enumerate(parameters)}


class Connection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, statement, parameters=()):
        sql, values = postgres_sql(statement, parameters)
        return Result(self.connection.execute(text(sql), values))

    def executescript(self, script):
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement.strip())


@lru_cache(maxsize=4)
def engine(url):
    if not url.startswith("postgresql+psycopg://"):
        raise ValueError("DATABASE_URL must use postgresql+psycopg://")
    return create_engine(
        url, pool_pre_ping=True, pool_size=4, max_overflow=4, pool_recycle=1800
    )
