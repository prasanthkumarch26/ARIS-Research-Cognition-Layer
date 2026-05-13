import os
import time
from pathlib import Path
import hashlib

import asyncio
import asyncpg
from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent
MIGRATIONS_DIR = BASE_DIR / "db" / "migrations"

if not MIGRATIONS_DIR.exists():
    raise FileNotFoundError(f"Migrations directory not found: {MIGRATIONS_DIR}")


def get_database_url():
    db_url = os.getenv("APP_DATABASE_URL")
    if not db_url:
        raise ValueError("Error: DATABASE_URL is not set in environment variables")
    return db_url


async def connect():
    database_url = get_database_url()

    start = time.time()
    try:
        conn = await asyncpg.connect(database_url)
    except Exception as e:
        print("Error: Failed to connect to database")
        raise e

    end = time.time()
    print(f"Success: Connected in {end - start:.2f}s")

    return conn


async def close(conn):
    if conn:
        await conn.close()
        print("Success: Connection closed")


LOCK_ID = int(
    hashlib.sha256("paper_intelligence_migrations".encode()).hexdigest()[:8],
    16
)

async def acquire_lock(conn):
    print("Acquiring migration lock...")

    row = await conn.fetchrow(
        "SELECT pg_try_advisory_lock($1) AS acquired;", LOCK_ID
    )

    if not row["acquired"]:
        raise RuntimeError("Error: Another migration process is already running")

    print("Success: Lock acquired")

async def release_lock(conn):
    await conn.execute("SELECT pg_advisory_unlock($1);", LOCK_ID)
    print("Success: Lock released")



async def ensure_migrations_table(conn):
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Success: Migration table ensured")
    except Exception as e:
        print("Error: Failed to ensure migration table")
        raise e


async def validate_migrations_table(conn):
    rows = await conn.fetch("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = $1
      AND table_schema = 'public';
    """, "schema_migrations")

    if not rows:
        raise RuntimeError("Error: schema_migrations table does not exist or is inaccessible")

    columns = {row["column_name"]: row["data_type"] for row in rows}

    expected = {
        "version": "text",
        "applied_at": "timestamp without time zone"
    }

    for col, dtype in expected.items():
        if col not in columns:
            raise RuntimeError(f"Error: schema_migrations missing column: {col}")

        if columns[col] != dtype:
            raise RuntimeError(
                f"Error: schema_migrations column '{col}' has wrong type: "
                f"{columns[col]} (expected {dtype})"
            )

    print("Success: schema_migrations table validated")


async def get_applied_migrations(conn):
    rows = await conn.fetch("SELECT version FROM schema_migrations;")
    return {row["version"] for row in rows}


def get_migration_files():
    files = sorted(MIGRATIONS_DIR.glob("*.sql"), key=lambda f: f.name)
    return files


async def apply_migration(conn, version: str, sql: str):
    async with conn.transaction():
        await conn.execute(sql)
        await conn.execute(
            "INSERT INTO schema_migrations (version) VALUES ($1);",
            version
        )
    print(f"Success: Applied migration: {version}")


async def run_migration():
    conn = await connect()
    lock_acquired = False
    try:
        await acquire_lock(conn)
        lock_acquired = True

        await ensure_migrations_table(conn)
        await validate_migrations_table(conn)

        applied = await get_applied_migrations(conn)

        files = get_migration_files()

        if not files:
            print("Warning: No migration files found")
            return

        for file in files:
            version = file.name

            if version in applied:
                print(f"Skipping already applied migration: {version}")
                continue

            print(f"Applying migration: {version}")

            sql = file.read_text()
            start = time.time()
            await apply_migration(conn, version, sql)
            end = time.time()
            print(f"Success: Applied migration {version} in {end - start:.2f}s")

        print("Success: All migrations applied successfully")

    except Exception as e:
        print("Error: Migration failed:", e)
        raise

    finally:
        if lock_acquired:
            try:
                await release_lock(conn)
            except Exception:
                print("Warning: Failed to release lock (connection may be closed)")

        await close(conn)

async def initialize_database():
    await run_migration()


if __name__ == "__main__":
    asyncio.run(initialize_database())
