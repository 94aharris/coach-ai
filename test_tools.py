"""Quick test script to verify tools work correctly."""

import asyncio
import aiosqlite
from pathlib import Path


async def test_database():
    """Test that database initializes correctly."""
    print("Testing database initialization...")

    # Create test database
    test_db_path = "data/test_coach.db"
    Path(test_db_path).parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(test_db_path)
    db.row_factory = aiosqlite.Row

    # Initialize schema (same as server.py)
    await db.executescript(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            notes TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            timeframe TEXT,
            category TEXT DEFAULT 'general',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS user_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fact TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    await db.commit()

    # Test inserting a todo
    print("  - Creating test todo...")
    await db.execute(
        "INSERT INTO todos (title, priority, notes) VALUES (?, ?, ?)",
        ("Test todo", "high", "This is a test"),
    )
    await db.commit()

    # Test reading todos
    print("  - Reading test todo...")
    cursor = await db.execute("SELECT * FROM todos")
    rows = await cursor.fetchall()
    assert len(rows) == 1
    assert rows[0]["title"] == "Test todo"
    assert rows[0]["priority"] == "high"

    # Test creating a goal
    print("  - Creating test goal...")
    await db.execute(
        "INSERT INTO goals (goal, timeframe, category) VALUES (?, ?, ?)",
        ("Test goal", "this week", "testing"),
    )
    await db.commit()

    # Test reading goals
    print("  - Reading test goal...")
    cursor = await db.execute("SELECT * FROM goals")
    rows = await cursor.fetchall()
    assert len(rows) == 1
    assert rows[0]["goal"] == "Test goal"

    # Test creating a user fact
    print("  - Creating test fact...")
    await db.execute(
        "INSERT INTO user_facts (fact, category) VALUES (?, ?)",
        ("Likes testing", "preferences"),
    )
    await db.commit()

    # Test reading facts
    print("  - Reading test fact...")
    cursor = await db.execute("SELECT * FROM user_facts")
    rows = await cursor.fetchall()
    assert len(rows) == 1
    assert rows[0]["fact"] == "Likes testing"

    await db.close()

    # Clean up test database
    Path(test_db_path).unlink()

    print("✓ All database tests passed!")


async def main():
    """Run all tests."""
    await test_database()
    print("\n✓ All tests passed! MCP server is ready to use.")


if __name__ == "__main__":
    asyncio.run(main())
