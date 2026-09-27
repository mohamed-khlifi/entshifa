"""Write an anonymized SQL dump of the current database (architecture §28)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

import pymysql
from pymysql.connections import Connection
from sqlalchemy.engine.url import make_url

from ent.core.privacy.anonymize import anonymize_row, build_offsets
from ent.core.security.passwords import hash_password
from ent.seeds.identity import LOCAL_DEV_PASSWORD
from ent.seeds.paths import repo_root
from ent.settings import load_settings


def default_output_path() -> Path:
    return repo_root() / "build" / "anonymized-dev.sql"


def _connect() -> Connection:
    settings = load_settings()
    async_url = settings.database_url
    if async_url.startswith("mysql+aiomysql://"):
        async_url = "mysql+pymysql://" + async_url.removeprefix("mysql+aiomysql://")
    url = make_url(async_url)
    if url.host is None or url.username is None or url.database is None:
        msg = "database url is missing host, user, or database"
        raise RuntimeError(msg)
    return pymysql.connect(
        host=url.host,
        port=url.port or 3306,
        user=url.username,
        password=url.password or "",
        database=url.database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def _literal(connection: Connection, value: Any) -> str:
    if isinstance(value, dict | list):
        value = json.dumps(value, ensure_ascii=False, default=str)
    escaped = connection.escape(value)
    if isinstance(escaped, bytes):
        return escaped.decode("utf-8")
    return str(escaped)


def _tables(connection: Connection) -> list[str]:
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        fetched = cast(list[dict[str, Any]], list(cursor.fetchall()))
    names: list[str] = []
    for row in fetched:
        names.append(str(next(iter(row.values()))))
    return names


def _generated_columns(connection: Connection, table: str) -> set[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COLUMN_NAME, EXTRA FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s",
            (table,),
        )
        fetched = cast(list[dict[str, Any]], list(cursor.fetchall()))
    generated: set[str] = set()
    for row in fetched:
        extra = str(row["EXTRA"] or "").upper()
        if "GENERATED" in extra:
            generated.add(str(row["COLUMN_NAME"]))
    return generated


def _create_table(connection: Connection, table: str) -> str:
    with connection.cursor() as cursor:
        cursor.execute(f"SHOW CREATE TABLE `{table}`")
        row = cast(dict[str, Any] | None, cursor.fetchone())
    if row is None:
        msg = f"missing create table for {table}"
        raise RuntimeError(msg)
    statement = row.get("Create Table") or row.get("Create View")
    return str(statement)


def _rows(connection: Connection, table: str) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM `{table}`")
        fetched = cast(list[dict[str, Any]], list(cursor.fetchall()))
    return [dict(item) for item in fetched]


def build_dump(connection: Connection, *, password_hash: str) -> str:
    """Anonymize every table and return a restorable SQL script."""

    patients = _rows(connection, "patient") if "patient" in _tables(connection) else []
    offsets = build_offsets(patients)
    lines = [
        "-- EntShifa anonymized development dump",
        "SET NAMES utf8mb4;",
        "SET FOREIGN_KEY_CHECKS=0;",
        "",
    ]
    for table in _tables(connection):
        generated = _generated_columns(connection, table)
        lines.append(f"DROP TABLE IF EXISTS `{table}`;")
        lines.append(_create_table(connection, table) + ";")
        rows = _rows(connection, table)
        if not rows:
            lines.append("")
            continue
        columns = [name for name in rows[0] if name not in generated]
        column_sql = ", ".join(f"`{name}`" for name in columns)
        for row in rows:
            safe = anonymize_row(
                table,
                row,
                offsets=offsets,
                password_hash=password_hash,
            )
            values = ", ".join(_literal(connection, safe.get(name)) for name in columns)
            lines.append(f"INSERT INTO `{table}` ({column_sql}) VALUES ({values});")
        lines.append("")
    lines.append("SET FOREIGN_KEY_CHECKS=1;")
    lines.append("")
    return "\n".join(lines)


def write_anonymized_dump(out_path: Path) -> Path:
    connection = _connect()
    try:
        script = build_dump(connection, password_hash=hash_password(LOCAL_DEV_PASSWORD))
    finally:
        connection.close()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(script, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Write an anonymized SQL dump of the current database."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=default_output_path(),
        help="Output .sql path",
    )
    args = parser.parse_args(argv)
    load_settings()
    out_path = write_anonymized_dump(args.out.resolve())
    print(f"Anonymized dump written to {out_path}")


if __name__ == "__main__":
    main()
