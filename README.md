# ass-api-2

FastAPI service for managing ASS subtitle captions, backed by Supabase.

## Setup

1. Create the table in your Supabase project by running [`schema.sql`](schema.sql) in the SQL editor.
2. Copy `.env.example` to `.env` and fill in your credentials:

   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-or-service-role-key
   ```

## Commands

| Command | Description |
| --- | --- |
| `make dev` | Run locally with hot reload |
| `make up` | Start with Docker (detached) |
| `make build` | Rebuild image and start |
| `make logs` | Tail container logs |
| `make down` | Stop containers |

## API

Swagger docs available at `http://localhost:8000/docs` once running.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `GET` | `/captions` | List all captions |
| `POST` | `/captions` | Create a captions entry |
| `GET` | `/captions/{id}` | Get by id |
| `PUT` | `/captions/{id}` | Update by id |
| `DELETE` | `/captions/{id}` | Delete by id |
