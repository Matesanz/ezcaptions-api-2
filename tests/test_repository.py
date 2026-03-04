from unittest.mock import MagicMock
from app.repository import BurnJobRepository, CaptionsRepository, VideoRepository
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


# =============================================================================
# VideoRepository
# =============================================================================

VIDEO_RECORD = {"id": "vid-1", "url": "https://example.com/video.mp4"}


# --- create ---

def test_video_create():
    repo = VideoRepository(make_client(insert_data=[VIDEO_RECORD]))
    assert repo.create("https://example.com/video.mp4") == VIDEO_RECORD


def test_video_create_inserts_url():
    client = make_client(insert_data=[VIDEO_RECORD])
    VideoRepository(client).create("https://example.com/video.mp4")
    client.table.return_value.insert.assert_called_once_with({"url": "https://example.com/video.mp4"})


# --- get ---

def test_video_get_found():
    repo = VideoRepository(make_client(eq_data=[VIDEO_RECORD]))
    assert repo.get("vid-1") == VIDEO_RECORD


def test_video_get_not_found():
    repo = VideoRepository(make_client())
    assert repo.get("missing") is None


# =============================================================================
# CaptionsRepository
# =============================================================================

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


def test_create_with_video_id():
    client = make_client(insert_data=[RECORD])
    CaptionsRepository(client).create(Captions(), video_id="vid-1")
    payload = client.table.return_value.insert.call_args.args[0]
    assert payload["video_id"] == "vid-1"


def test_create_without_video_id():
    client = make_client(insert_data=[RECORD])
    CaptionsRepository(client).create(Captions())
    payload = client.table.return_value.insert.call_args.args[0]
    assert payload["video_id"] is None


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


# =============================================================================
# BurnJobRepository
# =============================================================================

JOB_RECORD = {"id": "job-1", "caption_id": "cap-1", "status": "pending", "output_url": None, "error": None}


# --- create ---

def test_burn_job_create():
    repo = BurnJobRepository(make_client(insert_data=[JOB_RECORD]))
    assert repo.create("cap-1") == JOB_RECORD


# --- get ---

def test_burn_job_get_found():
    repo = BurnJobRepository(make_client(eq_data=[JOB_RECORD]))
    assert repo.get("job-1") == JOB_RECORD


def test_burn_job_get_not_found():
    repo = BurnJobRepository(make_client())
    assert repo.get("missing") is None


# --- update_status ---

def test_burn_job_update_status_pending_to_processing():
    client = make_client()
    BurnJobRepository(client).update_status("job-1", "processing")
    client.table.return_value.update.assert_called_once_with({"status": "processing"})


def test_burn_job_update_status_done_with_url():
    client = make_client()
    BurnJobRepository(client).update_status("job-1", "done", output_url="https://gcs.example.com/out.mp4")
    client.table.return_value.update.assert_called_once_with({
        "status": "done",
        "output_url": "https://gcs.example.com/out.mp4",
    })


def test_burn_job_update_status_failed_with_error():
    client = make_client()
    BurnJobRepository(client).update_status("job-1", "failed", error="ffmpeg crashed")
    client.table.return_value.update.assert_called_once_with({
        "status": "failed",
        "error": "ffmpeg crashed",
    })


def test_burn_job_update_status_targets_correct_job():
    client = make_client()
    BurnJobRepository(client).update_status("job-1", "processing")
    client.table.return_value.update.return_value.eq.assert_called_once_with("id", "job-1")
