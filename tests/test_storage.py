import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.storage import generate_signed_url, upload_to_gcs


# --- upload_to_gcs ---

def test_upload_to_gcs_returns_blob_name():
    mock_blob = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket

    with patch("app.storage.storage.Client", return_value=mock_client), \
         patch("app.storage.get_settings") as mock_settings:
        mock_settings.return_value.gcs_bucket = "my-bucket"
        result = upload_to_gcs("/tmp/output.mp4", "burned/job-1/output.mp4")

    assert result == "burned/job-1/output.mp4"
    mock_blob.upload_from_filename.assert_called_once_with("/tmp/output.mp4")


# --- generate_signed_url ---

@pytest.fixture
def mock_gcs():
    mock_credentials = MagicMock()
    mock_credentials.service_account_email = "sa@project.iam.gserviceaccount.com"
    mock_credentials.token = "mock-token"

    mock_blob = MagicMock()
    mock_blob.generate_signed_url.return_value = "https://signed.url/output.mp4"
    mock_bucket = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client = MagicMock()
    mock_client.bucket.return_value = mock_bucket

    with patch("google.auth.default", return_value=(mock_credentials, "project")), \
         patch("google.auth.transport.requests.Request"), \
         patch("app.storage.storage.Client", return_value=mock_client), \
         patch("app.storage.get_settings") as mock_settings:
        mock_settings.return_value.gcs_bucket = "my-bucket"
        yield mock_blob


def test_generate_signed_url_returns_url(mock_gcs):
    result = generate_signed_url("burned/job-1/output.mp4")
    assert result == "https://signed.url/output.mp4"


def test_generate_signed_url_uses_v4_and_get(mock_gcs):
    generate_signed_url("burned/job-1/output.mp4")
    kwargs = mock_gcs.generate_signed_url.call_args.kwargs
    assert kwargs["version"] == "v4"
    assert kwargs["method"] == "GET"


def test_generate_signed_url_default_expiry(mock_gcs):
    generate_signed_url("burned/job-1/output.mp4")
    kwargs = mock_gcs.generate_signed_url.call_args.kwargs
    assert kwargs["expiration"] == datetime.timedelta(minutes=15)


def test_generate_signed_url_custom_expiry(mock_gcs):
    generate_signed_url("burned/job-1/output.mp4", expiry_minutes=60)
    kwargs = mock_gcs.generate_signed_url.call_args.kwargs
    assert kwargs["expiration"] == datetime.timedelta(minutes=60)


def test_generate_signed_url_passes_credentials(mock_gcs):
    generate_signed_url("burned/job-1/output.mp4")
    kwargs = mock_gcs.generate_signed_url.call_args.kwargs
    assert kwargs["service_account_email"] == "sa@project.iam.gserviceaccount.com"
    assert kwargs["access_token"] == "mock-token"
