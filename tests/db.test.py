import pytest
from src.database import init_db, add_event, get_user_events
import aiosqlite
import os

@pytest.mark.asyncio
async def test_add_and_retrieve_event():
    test_db = ":memory:"

    import src.database
    old_db = src.database.DB_PATH
    src.database.DB_PATH = test_db
    await init_db()

    await add_event(123, 123, "2026-06-01", "15:00", "Тестовая встреча")
    events = await get_user_events(123)
    assert len(events) == 1
    assert events[0][2] == "15:00"
    assert events[0][3] == "Тестовая встреча"

    src.database.DB_PATH = old_db