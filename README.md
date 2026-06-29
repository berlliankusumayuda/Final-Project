# README - condensed
# Final Project - LMS (Paket 4 focused)

## Run locally (Docker Compose)
1. Copy .env.example to .env and fill values.
2. docker compose up --build -d
3. docker compose exec web python manage.py migrate
4. docker compose exec web python manage.py seed_demo
5. Open http://localhost:8000/docs for Swagger UI

Demo accounts:
- admin / adminpass
- instructor / instrpass
- student / studpass

Run tests:
- docker compose exec web pytest

