# FastAPI Rate Limiter

A small API project that limits how often a signed-in user can make requests. It uses Redis to track requests, PostgreSQL to store accounts, and FastAPI to serve the API.

## Run with Docker (recommended)

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/), then create a `.env` file in this folder:

```env
JWT_SECRET=replace-this-with-a-long-random-value
POSTGRES_USER=rate_limiter
POSTGRES_PASSWORD=change-this-password
POSTGRES_DB=rate_limiter
```

Start the app and its database and cache:

```powershell
docker compose up --build
```

When it starts, open [http://localhost:8000/docs](http://localhost:8000/docs) to explore and try the API. Stop it with `Ctrl+C`. To start it again, run `docker compose up`.

## Run locally

You will need Python 3.11 or newer, plus PostgreSQL and Redis running on your computer.

1. Create and activate a virtual environment, then install the project packages:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Create a `.env` file with the Docker settings above, and add these local connection addresses:

    > [!TIP]
    >
    > Use `.env.example` template to create `.env` file

   Make sure the PostgreSQL username, password, and database name match the ones you set up.

3. Prepare the database and start the API:

   ```powershell
   alembic upgrade head
   uvicorn main:app --reload
   ```

   Open [http://localhost:8000/docs](http://localhost:8000/docs) to try it.

## Notes

- The interactive API page is at `/docs`.
- Keep your `.env` file private; do not share or commit your secret or database password.
- Docker Compose keeps database and cache data in named volumes. `docker compose down -v` removes those volumes and their data.
