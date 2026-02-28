from unittest.mock import MagicMock
from app.repository import CaptionsRepository
from app.models import Captions, CaptionsInfo, CaptionsEvent, CaptionsWord

RECORD = {"id": "abc", "title": "Test", "data": {}}


def make_client(*, select_data=None, eq_data=None, insert_data=None, update_data=None):
    """Build a MagicMock Supabase client with preset return values."""
    client = MagicMock()
    client.table.return_value.select.return_value.execute.return_value.data = select_data or []
    client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = eq_data or []
    client.table.return_value.insert.return_value.execute.return_value.data = insert_data or []
    client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = update_data or []
    return client


# --- list ---

def test_list_returns_rows():
    repo = CaptionsRepository(make_client(select_data=[RECORD]))
    assert repo.list() == [RECORD]


def test_list_empty():
    repo = CaptionsRepository(make_client())
    assert repo.list() == []


# --- get ---

def test_get_found():
    repo = CaptionsRepository(make_client(eq_data=[RECORD]))
    assert repo.get("abc") == RECORD


def test_get_not_found():
    repo = CaptionsRepository(make_client())
    assert repo.get("missing") is None


# --- create ---

def test_create_returns_row():
    repo = CaptionsRepository(make_client(insert_data=[RECORD]))
    result = repo.create(Captions(info=CaptionsInfo(Title="Test")))
    assert result == RECORD


# --- update ---

def test_update_found():
    repo = CaptionsRepository(make_client(update_data=[RECORD]))
    result = repo.update("abc", Captions())
    assert result == RECORD


def test_update_not_found():
    repo = CaptionsRepository(make_client())
    assert repo.update("missing", Captions()) is None


# --- get_text ---

def test_get_text_found():
    captions = Captions(events=[
        CaptionsEvent(Words=[CaptionsWord(text="Hello", start=0, end=500)])
    ])
    row = {"data": captions.model_dump()}
    repo = CaptionsRepository(make_client(eq_data=[row]))
    assert repo.get_text("abc") == "Hello"


def test_get_text_not_found():
    repo = CaptionsRepository(make_client())
    assert repo.get_text("missing") is None
