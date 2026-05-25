import pytest
from src.database import init_db, add_event, get_user_events

@pytest.mark.asyncio
async def test_add_and_retrieve_event(monkeypatch):
    monkeypatch.setattr("src.config.DB_PATH", ":memory:")

    await init_db()

    await add_event(user_id=123, chat_id=456, event_date="2026-06-01", event_time="15:00", text="Тест")
    
    events = await get_user_events(user_id=123)
    assert len(events) == 1
    assert events[0][1] == "2026-06-01"
    assert events[0][2] == "15:00"
    assert events[0][3] == "Тест"
    assert events[0][4] == 0