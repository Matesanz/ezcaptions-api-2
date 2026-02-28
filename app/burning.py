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

    except Exception as e:
        job_repo.update_status(job_id, "failed", error=str(e))
