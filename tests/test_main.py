from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from app.main import app, get_repo

RECORD = {"id": "abc", "title": "Test", "data": {}}


@pytest.fixture
def client():
    return TestClient(app)


def override(repo):
    app.dependency_overrides[get_repo] = lambda: repo


def mock_repo(**kwargs):
    repo = MagicMock()
    for method, value in kwargs.items():
        getattr(repo, method).return_value = value
    return repo


# --- /health ---

def test_health(client):
    assert client.get("/health").status_code == 200


# --- GET /captions ---

def test_list_captions(client):
    override(mock_repo(list=[RECORD]))
    res = client.get("/captions")
    assert res.status_code == 200
    assert res.json() == [RECORD]


# --- POST /captions ---

def test_create_captions(client):
    override(mock_repo(create=RECORD))
    res = client.post("/captions", json={})
    assert res.status_code == 201
    assert res.json() == RECORD


# --- GET /captions/{id} ---

def test_get_captions_found(client):
    override(mock_repo(get=RECORD))
    assert client.get("/captions/abc").status_code == 200


def test_get_captions_not_found(client):
    override(mock_repo(get=None))
    assert client.get("/captions/missing").status_code == 404


# --- GET /captions/{id}/text ---

def test_get_text_found(client):
    override(mock_repo(get_text="Hello world"))
    res = client.get("/captions/abc/text")
    assert res.status_code == 200
    assert res.json() == "Hello world"


def test_get_text_not_found(client):
    override(mock_repo(get_text=None))
    assert client.get("/captions/missing/text").status_code == 404


# --- PUT /captions/{id} ---

def test_update_captions_found(client):
    override(mock_repo(update=RECORD))
    assert client.put("/captions/abc", json={}).status_code == 200


def test_update_captions_not_found(client):
    override(mock_repo(update=None))
    assert client.put("/captions/missing", json={}).status_code == 404


# --- DELETE /captions/{id} ---

def test_delete_captions(client):
    override(mock_repo())
    assert client.delete("/captions/abc").status_code == 204
