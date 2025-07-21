# Airguardian - Backend

---

## Introduction

**Airguardian** is a lightweight, containerized backend service designed to safeguard critical airspace by monitoring real-time drone activity and automatically detecting unauthorized incursions into designated no-fly zones (NFZs). Built on FastAPI and Celery, Airguardian:

- **Continuously polls** an external drones API for live position data (x, y, z coordinates).
- **Applies geospatial logic** to flag any drone whose horizontal position falls within a 1,000-unit radius of a protected center point.
- **Enriches each violation** with owner details (name, SSN, phone) fetched on-demand from a users API.
- **Persists all incidents** in PostgreSQL for audit, reporting, and retrieval of violations from the last 24 hours.
- **Exposes a simple, secure API** to check system health, retrieve raw drone feeds, and list recent NFZ violations (protected via a secret header).

Packaged with Docker and Docker Compose, Airguardian can be up and running in minutes—no special setup required—making it ideal for rapid testing, demos, or as the foundation of a larger air-space surveillance platform.

---

## Tech stack

| Category               | Technology                          |
| ---------------------  | ------------------------------------|
| Language               | Python 3                            |
| Web Framework          | FastAPI                             |
| ASGI Server            | Uvicorn                             |
| Task Queue             | Celery                              |
| Scheduler              | Celery Beat                         |
| Broker & Backend       | Redis                               |
| Database               | PostgreSQL                          |
| ORM                    | SQLAlchemy                          |
| Migrations             | Alembic                             |
| HTTP Client            | httpx                               |
| Validation & Settings  | Pydantic & Pydantic Settings        |
| Configuration          | `.env`                              |
| Containerization       | Docker & Docker Compose             |

---

## Airguardian Setup Guide

This guide shows you how to install, configure, and run the Airguardian backend from scratch on a new machine (Linux, Mac, or WSL2). This project is fully containerized. All dependencies are handled by Docker.

---

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (latest)
- [Docker Compose](https://docs.docker.com/compose/install/) (latest, v2+ preferred)
- (Optional) [git](https://git-scm.com/downloads) if not already present

---

### 1. Clone the repository

```bash
git clone https://github.com/To0nsa/Airguardian airguardian
cd airguardian
```

---

### 2. Copy environment variables

Edit the `.env` file if needed. Example (provided in repo):

```env
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
DATABASE_URL=postgresql://user:pass@postgres:5432/airguardian
API_SECRET=ma-vraie-valeur-secrète
DRONES_API_URL=https://drones-api.hive.fi/drones
USERS_API_URL=https://drones-api.hive.fi/users
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
DEBUG=false
```

If you want, copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

---

### 3. Build and start the stack

This command builds images and runs all containers:

```bash
docker-compose up -d --build
```

This will:

- Pull or build the Docker images for web, worker, beat, postgres, and redis
- Start the containers in the background

---

### 4. Database and migrations

**No manual migration is needed.**

The `web` service runs Alembic migrations automatically on startup. If the service starts, your tables are up-to-date.

---

### 5. Check if everything is running

List all services:

```bash
docker-compose ps
```

You should see `web`, `worker`, `beat`, `postgres`, and `redis` with a healthy status.d

---

### 6. API quick test

- **Health:**

  ```bash
  curl http://localhost:8000/api/v1/health
  ```

- **Drones:**

  ```bash
  curl http://localhost:8000/api/v1/drones | jq .
  ```

- **NFZ Violations (using your secret as an environment variable):**

  ```bash
  export X_SECRET=ma-vraie-valeur-secrète
  curl -H "X-Secret: $X_SECRET" http://localhost:8000/api/v1/nfz | jq .
  ```

---

### 7. Development tips

- **Hot reload**: Bind mounts is set in `docker-compose.yml` and we use `uvicorn --reload`, code changes take effect without a rebuild.
- **Manual migrations**: If needed (rare), you can run them in the web container:
  
  ```bash
  docker-compose exec web alembic upgrade head
  ```

- **Inspect the database**:

  ```bash
  docker-compose exec postgres psql -U user -d airguardian
  ```

---

### 8. Stopping and restarting

- Simply restart containers:

  ```bash
  docker-compose down && docker-compose up -d
  ```

- For Celery, you’ll still need to restart worker and beat if you change tasks:

  ```bash
  docker-compose up -d worker beat
  ```

- If any change is done to the database schema, generate & commit a new migration. Inside the project (host machine), run:

  ```bash
  docker-compose exec web alembic revision --autogenerate -m "describe your change"
  ```

And restart containers.

---

**With these steps, you’ll have Airguardian running on any new machine with just Docker, Docker Compose, and git.**3

---

## Container Navigation Guide

This guide shows you how to inspect and navigate the Docker containers in the Airguardian stack to verify that each service is running and healthy.

---

### 1. List all running containers

```bash
docker-compose ps
```

You should see services: `postgres`, `redis`, `web`, `worker`, `beat`.

---

### 2. View service logs

Follow logs in real time for each service:

```bash
docker-compose logs -f web      # FastAPI application

docker-compose logs -f worker   # Celery worker

docker-compose logs -f beat     # Celery beat scheduler

docker-compose logs -f postgres # PostgreSQL database

docker-compose logs -f redis    # Redis broker/backend
```

Look for:

- **web**: Uvicorn startup, HTTP request logs
- **worker**: Celery ready, task execution and NFZ violation logs
- **beat**: Scheduling of `fetch_and_process_drones`
- **postgres** / **redis**: any errors or startup messages

---

### 3. Open a shell inside a container

#### a) FastAPI app

```bash
docker-compose exec web sh
```

Once inside:

```bash
# Check code files
ls /app

# Manually run migrations
alembic history

# Test API with curl (from inside container)
curl -H "X-Secret: $X_SECRET" http://localhost:8000/api/v1/nfz
```

#### b) Celery worker

```bash
docker-compose exec worker sh
```

Inside the worker container you can:

```bash
# List installed tasks
celery -A app.celery.celery_app inspect registered
```

#### c) PostgreSQL

```bash
docker-compose exec postgres psql -U user -d airguardian
```

Inside `psql`:

```sql
-- List tables
\dt

-- Query recent violations
SELECT * FROM violations ORDER BY timestamp DESC LIMIT 10;

-- Query drones currently in the NFZ
SELECT * FROM nfz_active;
```

Exit with `\q`.

#### d) Redis

```bash
docker-compose exec redis redis-cli
```

Inside the Redis CLI:

```text
# Check connectivity
PING

# List all keys
KEYS *
```

Exit with `exit`.

---

### 4. Test HTTP endpoints from host

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Drones proxy
curl http://localhost:8000/api/v1/drones | jq .

# NFZ violations (requires secret)
curl -H "X-Secret: $X_SECRET" http://localhost:8000/api/v1/nfz | jq .
```

---

With these steps, you can navigate inside each container, inspect logs, databases, and verify that everything in the Airguardian backend is up and running properly. If you encounter any errors or unexpected behavior, check the logs in the relevant service container.
