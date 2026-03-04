import asyncio
import subprocess
import tempfile
from pathlib import Path

import httpx
from supabase import Client

from .models import Captions
from .repository import BurnJobRepository, CaptionsRepository
from .storage import upload_to_gcs


async def burn_video(job_id: str, caption_id: str, video_url: str, supabase: Client) -> None:
    job_repo = BurnJobRepository(supabase)
    captions_repo = CaptionsRepository(supabase)

    video_url = video_url.strip()

    job_repo.update_status(job_id, "processing")
    try:
        record = captions_repo.get(caption_id)
        if not record:
            raise ValueError(f"Caption {caption_id} not found")

        captions = Captions.model_validate(record["data"])
        ass_content = captions.to_ass()

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.mp4"
            ass_path = Path(tmpdir) / "captions.ass"
            output_path = Path(tmpdir) / "output.mp4"

            async with httpx.AsyncClient() as client:
                response = await client.get(video_url, follow_redirects=True)
                response.raise_for_status()
                input_path.write_bytes(response.content)

            ass_path.write_text(ass_content, encoding="utf-8")

            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "ffmpeg",
                    "-i", str(input_path),
                    "-vf", f"ass={ass_path}",
                    "-c:a", "copy",
                    "-y",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise RuntimeError(result.stderr)

            public_url = upload_to_gcs(str(output_path), f"burned/{job_id}/output.mp4")

        job_repo.update_status(job_id, "done", output_url=public_url)

    except httpx.HTTPStatusError as e:
        error_msg = f"Failed to download video: {e.response.status_code} {e.response.reason_phrase} for URL: '{video_url}'"
        job_repo.update_status(job_id, "failed", error=error_msg)
    except httpx.RequestError as e:
        error_msg = f"Network error while downloading video from URL '{video_url}': {str(e)}"
        job_repo.update_status(job_id, "failed", error=error_msg)
    except RuntimeError as e:
        error_msg = f"FFmpeg failed: {str(e)}"
        job_repo.update_status(job_id, "failed", error=error_msg)
    except ValueError as e:
        error_msg = f"Invalid data: {str(e)}"
        job_repo.update_status(job_id, "failed", error=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during burning: {type(e).__name__}: {str(e)}"
        job_repo.update_status(job_id, "failed", error=error_msg)
