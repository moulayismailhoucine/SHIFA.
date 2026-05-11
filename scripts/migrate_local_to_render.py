"""Migrate local SQLite data to a remote Postgres (Render) database.

Usage:
  python scripts/migrate_local_to_render.py --remote <REMOTE_DATABASE_URL>

You can also set env vars:
  REMOTE_DATABASE_URL (remote Postgres connection string)
  LOCAL_DATABASE_URL (defaults to sqlite:///./medisys.db)

Options:
  --force    : If remote tables contain data, delete remote data and replace with local.
  --dry-run  : Print actions without executing.

Notes:
- This script preserves primary keys and attempts to update Postgres sequences after insert.
- It will create missing tables on the remote using the project's SQLAlchemy models.
- Be careful: --force will DELETE remote data for the tables copied.
"""

import os
import argparse
import sys
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Ensure models are imported so metadata is populated
from app import models  # noqa: F401
from app.models import Base


def is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def get_engine(url: str):
    if is_sqlite(url):
        return create_engine(url, connect_args={"check_same_thread": False})
    else:
        return create_engine(url, pool_pre_ping=True)


def update_postgres_sequences(engine):
    """Update SERIAL/SEQUENCE values for tables with integer id primary key."""
    with engine.connect() as conn:
        dialect_name = conn.dialect.name
        if dialect_name != "postgresql":
            return
        for table in Base.metadata.sorted_tables:
            cols = [c.name for c in table.columns]
            if "id" in cols:
                tbl = table.name
                try:
                    # set sequence to max(id) or 1
                    stmt = text(
                        "SELECT setval(pg_get_serial_sequence(:tbl, 'id'), COALESCE((SELECT MAX(id) FROM \"" + tbl + "\"), 1), true)"
                    )
                    conn.execute(stmt, {"tbl": tbl})
                except Exception as e:
                    print(f"Warning: could not update sequence for {tbl}: {e}")


def copy_table(local_engine, remote_engine, table, dry_run=False, force=False):
    tbl_name = table.name
    print(f"Processing table: {tbl_name}")

    with local_engine.connect() as lconn, remote_engine.connect() as rconn:
        # fetch all rows from local
        try:
            result = lconn.execute(select(table))
            rows = result.fetchall()
        except Exception as e:
            print(f"  Skipping {tbl_name}: could not read from local DB: {e}")
            return

        if not rows:
            print(f"  No rows to copy for {tbl_name}")
            return

        # check remote count
        try:
            rcount = rconn.execute(text(f"SELECT COUNT(*) FROM \"{tbl_name}\";"))
            remote_count = rcount.scalar()
        except Exception as e:
            # Table may not exist remotely
            remote_count = 0

        if remote_count > 0 and not force:
            print(f"  Remote table {tbl_name} already has {remote_count} rows. Use --force to overwrite. Skipping.")
            return

        if dry_run:
            print(f"  Would copy {len(rows)} rows to remote {tbl_name} (force={force})")
            return

        try:
            with remote_engine.begin() as trans:
                # create table on remote if missing
                try:
                    trans.execute(text(f"SELECT 1 FROM \"{tbl_name}\" LIMIT 1;"))
                except Exception:
                    print(f"  Creating table {tbl_name} on remote")
                    Base.metadata.create_all(bind=remote_engine, tables=[table])

                if force and remote_count > 0:
                    print(f"  Deleting existing {remote_count} rows from remote.{tbl_name}")
                    trans.execute(text(f"DELETE FROM \"{tbl_name}\";"))

                # Prepare data
                mapped = [dict(row._mapping) for row in rows]
                if mapped:
                    # insert preserving primary keys
                    trans.execute(table.insert(), mapped)

            print(f"  Copied {len(rows)} rows to remote.{tbl_name}")
        except SQLAlchemyError as e:
            print(f"  Error copying table {tbl_name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Copy local DB data into a remote Postgres DB")
    parser.add_argument("--local", help="Local DB URL", default=os.getenv("LOCAL_DATABASE_URL", "sqlite:///./medisys.db"))
    parser.add_argument("--remote", help="Remote DB URL (Postgres)", default=os.getenv("REMOTE_DATABASE_URL") or os.getenv("DATABASE_URL"))
    parser.add_argument("--dry-run", help="Show actions without executing", action="store_true")
    parser.add_argument("--force", help="Delete remote data before copying", action="store_true")
    parser.add_argument("--tables", help="Comma-separated list of table names to copy (default=all)")

    args = parser.parse_args()

    if not args.remote:
        print("Remote DB URL is required. Provide --remote or set REMOTE_DATABASE_URL / DATABASE_URL env var.")
        sys.exit(1)

    local_url = args.local
    remote_url = args.remote

    print(f"Local DB: {local_url}")
    print(f"Remote DB: {remote_url}")

    local_engine = get_engine(local_url)
    remote_engine = get_engine(remote_url)

    # Import models already done above to populate Base.metadata

    # Create tables on remote if missing
    if not args.dry_run:
        print("Ensuring remote schema exists (create missing tables)")
        try:
            Base.metadata.create_all(bind=remote_engine)
        except Exception as e:
            print(f"Warning: could not create tables on remote: {e}")

    table_names = None
    if args.tables:
        table_names = {t.strip() for t in args.tables.split(",") if t.strip()}

    # Use dependency-sorted tables from metadata
    for table in Base.metadata.sorted_tables:
        if table_names and table.name not in table_names:
            continue
        # skip alembic_version if present
        if table.name == "alembic_version":
            continue
        copy_table(local_engine, remote_engine, table, dry_run=args.dry_run, force=args.force)

    # update sequences for Postgres
    if not is_sqlite(remote_url) and not args.dry_run:
        print("Updating Postgres sequences to match max(id) values")
        update_postgres_sequences(remote_engine)

    print("Migration complete.")


if __name__ == "__main__":
    main()
