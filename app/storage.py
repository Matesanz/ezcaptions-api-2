from google.cloud import storage

from .config import get_settings


def upload_to_gcs(local_path: str, destination: str) -> str:
    """Uploads file to GCS, returns public URL."""
    client = storage.Client()
    bucket = client.bucket(get_settings().gcs_bucket)
    blob = bucket.blob(destination)
    blob.upload_from_filename(local_path)
    return blob.public_url
