import pytest
from src.utils import normalize_day

def test_normalize_day():
    assert normalize_day("пн") == "Понедельник"
    assert normalize_day("вторник") == "Вторник"
    assert normalize_day("Ср") == "Среда"
    assert normalize_day("Воскресенье") == "Воскресенье"
    assert normalize_day("неизвестный") == "Неизвестный"