FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

# gcc required to compile pyroaring (transitive dep of supabase -> pyiceberg)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
