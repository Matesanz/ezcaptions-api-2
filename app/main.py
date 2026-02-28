from fastapi import FastAPI, HTTPException, Depends
from supabase import Client

from .database import get_supabase
from .models import Captions
from .repository import CaptionsRepository
from . import __version__, __title__

app = FastAPI(title=__title__, version=__version__)


def get_repo(client: Client = Depends(get_supabase)) -> CaptionsRepository:
    return CaptionsRepository(client)


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
