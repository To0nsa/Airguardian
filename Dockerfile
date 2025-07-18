# Dockerfile

# 1. Base image
FROM python:3.10-slim

# 2. Environment
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1

# 3. Install system deps (for psycopg2-binary, Redis client, etc.)
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
       build-essential \
       gcc \
       libpq-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Install Poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# 5. Create app directory
WORKDIR /app

# 6. Copy metadata and install dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# 7. Copy the rest of the code
COPY . .

# 8. Expose FastAPI port
EXPOSE 8000

# 9. Default entrypoint (overridden in docker-compose for worker/beat)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
