# Extended README with commands and notes
# Final Project - LMS (Paket 4 focused)

## Requirements
- Docker & Docker Compose
- Ports 8000 (web), 5432 (postgres), 6379 (redis) available

## Setup
1. Copy .env.example to .env and edit secrets (SECRET_KEY, JWT_SECRET_KEY preferably random)
2. docker compose up --build -d
3. docker compose exec web python manage.py migrate
4. docker compose exec web python manage.py seed_demo
5. Open http://localhost:8000/docs for Swagger UI

## Demo accounts
- admin / adminpass (role: admin)
- instructor / instrpass (role: instructor)
- student / studpass (role: student)

## Endpoints highlights
- POST /auth/login -> obtain JWT token (Authorization: Bearer <token>)
- GET /courses/ -> list courses (supports q, ordering, page, page_size)
- GET /courses/{id} -> course detail (includes lessons)
- POST /enrollments/ -> enroll to a course (auth required)
- POST /progress/complete -> mark lesson complete (auth required)
- GET /courses/cache/stats -> cache hit/miss stats

## Tests
- docker compose exec web pytest

## Notes about Paket 4 features implemented
- Redis caching for course list and detail, with TTLs and metrics
- Cache invalidation on course/lesson changes (granular via redis scan)
- Rate limiting middleware for GET /courses/ (fixed window 60 req/min per IP)
- Query optimization via select_related & prefetch_related; tests include assertNumQueries checks
- Response format standardized via core/response helpers

