"""Database migrations for Coach AI."""

import aiosqlite


async def migrate_database(db: aiosqlite.Connection) -> None:
    """Run all necessary database migrations.

    This function checks for and applies missing columns/tables
    to upgrade the database schema without losing data.
    """
    # Check current schema version
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    version_table_exists = await cursor.fetchone()

    if not version_table_exists:
        # Create version tracking table
        await db.execute(
            """
            CREATE TABLE schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute("INSERT INTO schema_version (version) VALUES (0)")
        await db.commit()

    # Get current version
    cursor = await db.execute("SELECT MAX(version) FROM schema_version")
    row = await cursor.fetchone()
    current_version = row[0] if row else 0

    # Apply migrations in order
    if current_version < 1:
        await _migration_1_add_task_tracking(db)
        await db.execute("INSERT INTO schema_version (version) VALUES (1)")
        await db.commit()


async def _migration_1_add_task_tracking(db: aiosqlite.Connection) -> None:
    """Migration 1: Add task tracking columns to todos table.

    Adds:
    - skipped_count: Track how many times task was moved forward
    - time_estimate: Estimated time in minutes for task completion
    - last_scheduled: Last date this task was scheduled in a daily note
    """
    # Check if columns already exist (safe migration)
    cursor = await db.execute("PRAGMA table_info(todos)")
    columns = {row[1] for row in await cursor.fetchall()}

    if "skipped_count" not in columns:
        await db.execute("ALTER TABLE todos ADD COLUMN skipped_count INTEGER DEFAULT 0")

    if "time_estimate" not in columns:
        await db.execute("ALTER TABLE todos ADD COLUMN time_estimate INTEGER")

    if "last_scheduled" not in columns:
        await db.execute("ALTER TABLE todos ADD COLUMN last_scheduled DATE")

    await db.commit()
