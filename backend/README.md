# AI Course Project

## Running the project

First, start the docker containers for frontend, backend, and DB

```bash
docker compose up -d --build
```

Then, we want to run the inital DB migration if it's the first time running the
project:

```bash
cd backend/src/backend
alembic upgrade head
```
