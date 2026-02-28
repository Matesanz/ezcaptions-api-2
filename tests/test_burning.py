import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.burning import burn_video
from app.models import Captions, CaptionsEvent, CaptionsWord

JOB_ID = "job-1"
CAPTION_ID = "cap-1"
VIDEO_URL = "https://example.com/video.mp4"
GCS_URL = "https://storage.googleapis.com/bucket/burned/job-1/output.mp4"


def make_captions():
    return Captions(events=[
        CaptionsEvent(Words=[CaptionsWord(text="Hello", start=0, end=1000)])
    ])


def make_caption_record():
    return {"id": CAPTION_ID, "data": make_captions().model_dump()}


def mock_http_client(content=b"fake video", raise_for_status=None):
    """Returns a mock httpx.AsyncClient usable as an async context manager."""
    response = MagicMock()
    response.content = content
    if raise_for_status:
        response.raise_for_status.side_effect = raise_for_status
    client = AsyncMock()
    client.get = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


def mock_subprocess_result(returncode=0, stderr=""):
    result = MagicMock()
    result.returncode = returncode
    result.stderr = stderr
    return result


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_happy_path_sets_processing_then_done():
    job_repo = MagicMock()
    captions_repo = MagicMock()
    captions_repo.get.return_value = make_caption_record()

    with (
        patch("app.burning.BurnJobRepository", return_value=job_repo),
        patch("app.burning.CaptionsRepository", return_value=captions_repo),
        patch("app.burning.httpx.AsyncClient", return_value=mock_http_client()),
        patch("app.burning.subprocess.run", return_value=mock_subprocess_result()),
        patch("app.burning.upload_to_gcs", return_value=GCS_URL),
    ):
        run(burn_video(JOB_ID, CAPTION_ID, VIDEO_URL, MagicMock()))

    calls = [c.args for c in job_repo.update_status.call_args_list]
    assert calls[0] == (JOB_ID, "processing")
    assert calls[1] == (JOB_ID, "done")


def test_happy_path_output_url():
    job_repo = MagicMock()
    captions_repo = MagicMock()
    captions_repo.get.return_value = make_caption_record()

    with (
        patch("app.burning.BurnJobRepository", return_value=job_repo),
        patch("app.burning.CaptionsRepository", return_value=captions_repo),
        patch("app.burning.httpx.AsyncClient", return_value=mock_http_client()),
        patch("app.burning.subprocess.run", return_value=mock_subprocess_result()),
        patch("app.burning.upload_to_gcs", return_value=GCS_URL),
    ):
        run(burn_video(JOB_ID, CAPTION_ID, VIDEO_URL, MagicMock()))

    job_repo.update_status.assert_called_with(JOB_ID, "done", output_url=GCS_URL)


def test_happy_path_ffmpeg_command():
    job_repo = MagicMock()
    captions_repo = MagicMock()
    captions_repo.get.return_value = make_caption_record()
    mock_run = MagicMock(return_value=mock_subprocess_result())

    with (
        patch("app.burning.BurnJobRepository", return_value=job_repo),
        patch("app.burning.CaptionsRepository", return_value=captions_repo),
        patch("app.burning.httpx.AsyncClient", return_value=mock_http_client()),
        patch("app.burning.subprocess.run", mock_run),
        patch("app.burning.upload_to_gcs", return_value=GCS_URL),
    ):
        run(burn_video(JOB_ID, CAPTION_ID, VIDEO_URL, MagicMock()))

    cmd = mock_run.call_args.args[0]
    assert cmd[0] == "ffmpeg"
    assert "-vf" in cmd
    assert any("ass=" in arg for arg in cmd)
    assert "-c:a" in cmd
    assert "copy" in cmd
    assert "-y" in cmd


def test_happy_path_gcs_destination_path():
    job_repo = MagicMock()
    captions_repo = MagicMock()
    captions_repo.get.return_value = make_caption_record()
    mock_upload = MagicMock(return_value=GCS_URL)

    with (
        patch("app.burning.BurnJobRepository", return_value=job_repo),
        patch("app.burning.CaptionsRepository", return_value=captions_repo),
        patch("app.burning.httpx.AsyncClient", return_value=mock_http_client()),
        patch("app.burning.subprocess.run", return_value=mock_subprocess_result()),
        patch("app.burning.upload_to_gcs", mock_upload),
    ):
        run(burn_video(JOB_ID, CAPTION_ID, VIDEO_URL, MagicMock()))

    _, destination = mock_upload.call_args.args
    assert destination == f"burned/{JOB_ID}/output.mp4"


# ---------------------------------------------------------------------------
# Failure cases
# ---------------------------------------------------------------------------

def test_caption_not_found_sets_failed():
    job_repo = MagicMock()
    captions_repo = MagicMock()
    captions_repo.get.return_value = None

    with (
        patch("app.burning.BurnJobRepository", return_value=job_repo),
        patch("app.burning.CaptionsRepository", return_value=captions_repo),
    ):
        run(burn_video(JOB_ID, CAPTION_ID, VIDEO_URL, MagicMock()))

    job_repo.update_status.assert_called_with(
        JOB_ID, "failed", error=f"Caption {CAPTION_ID} not found"
    )


def test_http_error_sets_failed():
    job_repo = MagicMock()
    captions_repo = MagicMock()
    captions_repo.get.return_value = make_caption_record()

    with (
        patch("app.burning.BurnJobRepository", return_value=job_repo),
        patch("app.burning.CaptionsRepository", return_value=captions_repo),
        patch("app.burning.httpx.AsyncClient", return_value=mock_http_client(
            raise_for_status=Exception("HTTP 403")
        )),
    ):
        run(burn_video(JOB_ID, CAPTION_ID, VIDEO_URL, MagicMock()))

    final = job_repo.update_status.call_args
    assert final.args[1] == "failed"
    assert "HTTP 403" in final.kwargs["error"]


def test_ffmpeg_nonzero_exit_sets_failed():
    job_repo = MagicMock()
    captions_repo = MagicMock()
    captions_repo.get.return_value = make_caption_record()

    with (
        patch("app.burning.BurnJobRepository", return_value=job_repo),
        patch("app.burning.CaptionsRepository", return_value=captions_repo),
        patch("app.burning.httpx.AsyncClient", return_value=mock_http_client()),
        patch("app.burning.subprocess.run", return_value=mock_subprocess_result(returncode=1, stderr="Codec error")),
        patch("app.burning.upload_to_gcs"),
    ):
        run(burn_video(JOB_ID, CAPTION_ID, VIDEO_URL, MagicMock()))

    final = job_repo.update_status.call_args
    assert final.args[1] == "failed"
    assert "Codec error" in final.kwargs["error"]


def test_gcs_upload_failure_sets_failed():
    job_repo = MagicMock()
    captions_repo = MagicMock()
    captions_repo.get.return_value = make_caption_record()

    with (
        patch("app.burning.BurnJobRepository", return_value=job_repo),
        patch("app.burning.CaptionsRepository", return_value=captions_repo),
        patch("app.burning.httpx.AsyncClient", return_value=mock_http_client()),
        patch("app.burning.subprocess.run", return_value=mock_subprocess_result()),
        patch("app.burning.upload_to_gcs", side_effect=Exception("GCS auth failed")),
    ):
        run(burn_video(JOB_ID, CAPTION_ID, VIDEO_URL, MagicMock()))

    final = job_repo.update_status.call_args
    assert final.args[1] == "failed"
    assert "GCS auth failed" in final.kwargs["error"]
