# AI Course Project

## Environment

Create a new file `.env` under the backend directory.

Put your OpenAI API key in the `backend/.env` file:

```bash
OPENAI_API_KEY="..."
```

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
