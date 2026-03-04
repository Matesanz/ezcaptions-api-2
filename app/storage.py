import datetime

import google.auth
import google.auth.transport.requests
from google.cloud import storage

from .config import get_settings


def upload_to_gcs(local_path: str, destination: str) -> str:
    """Uploads file to GCS, returns the blob name (destination path)."""
    client = storage.Client()
    bucket = client.bucket(get_settings().gcs_bucket)
    blob = bucket.blob(destination)
    blob.upload_from_filename(local_path)
    return destination


def generate_signed_url(blob_name: str, expiry_minutes: int = 15) -> str:
    """Generates a time-limited signed URL for a private GCS object."""
    credentials, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    client = storage.Client(credentials=credentials)
    bucket = client.bucket(get_settings().gcs_bucket)
    blob = bucket.blob(blob_name)
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expiry_minutes),
        method="GET",
        service_account_email=credentials.service_account_email,
        access_token=credentials.token,
    )
