from supabase import Client

from .models import Captions

TABLE = "captions"
BURN_JOBS_TABLE = "burn_jobs"


class BurnJobRepository:
    def __init__(self, client: Client):
        self._client = client

    def create(self, caption_id: str) -> dict:
        res = self._client.table(BURN_JOBS_TABLE).insert({"caption_id": caption_id}).execute()
        return res.data[0]

    def get(self, job_id: str) -> dict | None:
        res = self._client.table(BURN_JOBS_TABLE).select("*").eq("id", job_id).execute()
        return res.data[0] if res.data else None

    def update_status(self, job_id: str, status: str, output_url: str | None = None, error: str | None = None) -> None:
        payload: dict = {"status": status}
        if output_url is not None:
            payload["output_url"] = output_url
        if error is not None:
            payload["error"] = error
        self._client.table(BURN_JOBS_TABLE).update(payload).eq("id", job_id).execute()


class CaptionsRepository:
    def __init__(self, client: Client):
        self._client = client

    def list(self) -> list[dict]:
        res = self._client.table(TABLE).select("*").execute()
        return res.data

    def create(self, captions: Captions) -> dict:
        res = self._client.table(TABLE).insert({
            "title": captions.info.Title,
            "data": captions.model_dump(),
        }).execute()
        return res.data[0]

    def get(self, id: str) -> dict | None:
        res = self._client.table(TABLE).select("*").eq("id", id).execute()
        return res.data[0] if res.data else None

    def update(self, id: str, captions: Captions) -> dict | None:
        res = self._client.table(TABLE).update({
            "title": captions.info.Title,
            "data": captions.model_dump(),
        }).eq("id", id).execute()
        return res.data[0] if res.data else None

    def get_text(self, id: str) -> str:
        res = self._client.table(TABLE).select("data").eq("id", id).execute()
        if not res.data:
            return None
        return Captions.model_validate(res.data[0]["data"]).full_text

    def delete(self, id: str) -> None:
        self._client.table(TABLE).delete().eq("id", id).execute()
