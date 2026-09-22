## 2026-09-22: Docker Compose с PostgreSQL и Redis

**Задача:** превратить одиночный Flask-контейнер в многосервисное приложение с постоянным хранилищем.

**Выполнено:**
- Flask API (URL shortener): `/health`, `POST /shorten`, `GET /<code>`.
- Dockerfile с multi-stage build, non-root user, образ 134 МБ.
- `docker-compose.yml` с тремя сервисами: backend, PostgreSQL 16, Redis 7.
- PostgreSQL с volume `postgres_data` — данные переживают перезапуск.
- Redis на порту 6380 (6379 занят системным Redis).
- Healthcheck для каждого сервиса + depends_on condition.
- Проверен полный цикл: create → redirect → 404.
- Проверен перезапуск: старая ссылка `HxqUKomr` работает после `docker-compose up`.

**Проблемы и решения:**
- `docker compose` (v2) не установлен → используем `docker-compose` (v1).
- Порт 5000 не пробрасывался (DOCKER-USER блокирует spoofed loopback).
  Решение: `network_mode: host` для всех сервисов.
- Порт 6379 занят системным Redis → наш Redis на 6380.
- Опечатка `=` вместо `==` в requirements.txt → исправлено.

**Что понял:**
- Multi-stage build уменьшает образ в 7 раз.
- Volume в Compose — не то же самое, что bind mount.
- Healthcheck + depends_on решает race condition при старте.
- `RealDictCursor` и `%s` плейсхолдеры против SQL-injection.
