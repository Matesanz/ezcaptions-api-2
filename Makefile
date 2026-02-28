.PHONY: up down build logs dev test

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose up -d --build

logs:
	docker compose logs -f api

dev:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest tests/ -v
