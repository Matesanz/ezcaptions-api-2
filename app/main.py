from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends
from supabase import Client

from .burning import burn_video
from .database import get_supabase
from .models import BurnJob, BurnRequest, Captions, VideoTranscribeRequest
from .repository import BurnJobRepository, CaptionsRepository
from .transcription import transcribe
from . import __version__, __title__

app = FastAPI(title=__title__, version=__version__)


def get_repo(client: Client = Depends(get_supabase)) -> CaptionsRepository:
    return CaptionsRepository(client)


def get_burn_repo(client: Client = Depends(get_supabase)) -> BurnJobRepository:
    return BurnJobRepository(client)


@app.get("/health")
def health() -> bool:
    return True


@app.get("/captions")
def list_captions(repo: CaptionsRepository = Depends(get_repo)):
    return repo.list()


@app.post("/captions", status_code=201)
def create_captions(captions: Captions, repo: CaptionsRepository = Depends(get_repo)):
    return repo.create(captions)


@app.get("/captions/{id}")
def get_captions(id: str, repo: CaptionsRepository = Depends(get_repo)):
    record = repo.get(id)
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    return record


@app.get("/captions/{id}/text")
def get_captions_text(id: str, repo: CaptionsRepository = Depends(get_repo)):
    lines = repo.get_text(id)
    if lines is None:
        raise HTTPException(status_code=404, detail="Not found")
    return lines


@app.put("/captions/{id}")
def update_captions(id: str, captions: Captions, repo: CaptionsRepository = Depends(get_repo)):
    record = repo.update(id, captions)
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    return record


@app.delete("/captions/{id}", status_code=204)
def delete_captions(id: str, repo: CaptionsRepository = Depends(get_repo)):
    repo.delete(id)


@app.post("/captions/from-video", status_code=201)
def transcribe_video(request: VideoTranscribeRequest, repo: CaptionsRepository = Depends(get_repo)):
    try:
        captions = transcribe(request.url, request.title, request.language, request.speech_model)
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return repo.create(captions)


@app.post("/captions/{id}/burn", status_code=202)
def burn_captions(
    id: str,
    request: BurnRequest,
    background_tasks: BackgroundTasks,
    repo: CaptionsRepository = Depends(get_repo),
    burn_repo: BurnJobRepository = Depends(get_burn_repo),
    client: Client = Depends(get_supabase),
) -> BurnJob:
    record = repo.get(id)
    if not record:
        raise HTTPException(status_code=404, detail="Not found")
    job = burn_repo.create(id)
    background_tasks.add_task(burn_video, job["id"], id, request.video_url, client)
    return BurnJob(**job)


@app.get("/captions/{id}/burn/{job_id}")
def get_burn_job(
    id: str,
    job_id: str,
    burn_repo: BurnJobRepository = Depends(get_burn_repo),
) -> BurnJob:
    job = burn_repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    return BurnJob(**job)
