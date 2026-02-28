from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from app.database import get_supabase
from app.main import app, get_repo, get_burn_repo
from app.models import Captions

RECORD = {"id": "abc", "title": "Test", "data": {}}


@pytest.fixture
def client():
    return TestClient(app)


def override(repo):
    app.dependency_overrides[get_repo] = lambda: repo


def override_burn(burn_repo):
    app.dependency_overrides[get_burn_repo] = lambda: burn_repo
    # get_supabase is a direct dependency of burn_captions (passed to burn_video)
    app.dependency_overrides[get_supabase] = lambda: MagicMock()


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


# --- POST /captions/from-video ---

def test_transcribe_video(client):
    override(mock_repo(create=RECORD))
    with patch("app.main.transcribe", return_value=Captions()):
        res = client.post("/captions/from-video", json={"url": "https://example.com/video.mp4"})
    assert res.status_code == 201
    assert res.json() == RECORD


def test_transcribe_video_forwards_all_params(client):
    override(mock_repo(create=RECORD))
    with patch("app.main.transcribe", return_value=Captions()) as mock_t:
        client.post("/captions/from-video", json={
            "url": "https://example.com/video.mp4",
            "title": "My Video",
            "language": "fr",
            "speech_model": "nano",
        })
    mock_t.assert_called_once_with("https://example.com/video.mp4", "My Video", "fr", "nano")


def test_transcribe_video_defaults(client):
    override(mock_repo(create=RECORD))
    with patch("app.main.transcribe", return_value=Captions()) as mock_t:
        client.post("/captions/from-video", json={"url": "https://example.com/video.mp4"})
    mock_t.assert_called_once_with("https://example.com/video.mp4", "Default Title", None, "nano")


def test_transcribe_video_error(client):
    override(mock_repo())
    with patch("app.main.transcribe", side_effect=RuntimeError("Audio file not found")):
        res = client.post("/captions/from-video", json={"url": "https://example.com/bad.mp4"})
    assert res.status_code == 422
    assert "Audio file not found" in res.json()["detail"]


# --- POST /captions/{id}/burn ---

JOB_RECORD = {"id": "job-1", "caption_id": "abc", "status": "pending", "output_url": None, "error": None}


def test_burn_captions_returns_202(client):
    override(mock_repo(get=RECORD))
    override_burn(mock_repo(create=JOB_RECORD))
    with patch("app.main.burn_video", new_callable=AsyncMock):
        res = client.post("/captions/abc/burn", json={"video_url": "https://example.com/video.mp4"})
    assert res.status_code == 202


def test_burn_captions_returns_job(client):
    override(mock_repo(get=RECORD))
    override_burn(mock_repo(create=JOB_RECORD))
    with patch("app.main.burn_video", new_callable=AsyncMock):
        res = client.post("/captions/abc/burn", json={"video_url": "https://example.com/video.mp4"})
    data = res.json()
    assert data["id"] == "job-1"
    assert data["status"] == "pending"


def test_burn_captions_not_found(client):
    override(mock_repo(get=None))
    override_burn(mock_repo())
    res = client.post("/captions/missing/burn", json={"video_url": "https://example.com/video.mp4"})
    assert res.status_code == 404


def test_burn_schedules_background_task(client):
    override(mock_repo(get=RECORD))
    override_burn(mock_repo(create=JOB_RECORD))
    with patch("app.main.burn_video", new_callable=AsyncMock) as mock_bv:
        client.post("/captions/abc/burn", json={"video_url": "https://example.com/video.mp4"})
    mock_bv.assert_called_once()
    args = mock_bv.call_args.args
    assert args[0] == "job-1"                                    # job_id
    assert args[1] == "abc"                                       # caption_id
    assert args[2] == "https://example.com/video.mp4"            # video_url


# --- GET /captions/{id}/burn/{job_id} ---

def test_get_burn_job_found(client):
    override_burn(mock_repo(get=JOB_RECORD))
    res = client.get("/captions/abc/burn/job-1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "job-1"
    assert data["status"] == "pending"


def test_get_burn_job_not_found(client):
    override_burn(mock_repo(get=None))
    assert client.get("/captions/abc/burn/missing").status_code == 404


def test_get_burn_job_done(client):
    done_job = {**JOB_RECORD, "status": "done", "output_url": "https://gcs.example.com/out.mp4"}
    override_burn(mock_repo(get=done_job))
    res = client.get("/captions/abc/burn/job-1")
    assert res.status_code == 200
    assert res.json()["output_url"] == "https://gcs.example.com/out.mp4"
