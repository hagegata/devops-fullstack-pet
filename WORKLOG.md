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
## 2026-09-23: Nginx как reverse proxy

**Задача:** добавить Nginx перед backend — единая точка входа, проксирование /api/* на Flask.

**Выполнено:**
- Конфиг nginx/nginx.conf: `listen 8080`, `upstream backend_upstream`, `location /api/`, `location = /`.
- Nginx-сервис в docker-compose.yml, конфиг монтируется через volume (`:ro`).
- Проверено: `/` возвращает заглушку, `/api/health` проксируется на backend.
- Сравнены заголовки: прямой запрос → Server: Werkzeug, через Nginx → Server: nginx/1.27.5.
- Полный цикл через Nginx: POST /api/shorten → 201, GET /api/<code> → 302.

**Ошибки и решения:**
- Сначала `ss -tlnp | grep 8080` показывал пусто — Nginx ещё не успел стартовать. После запуска порт появился.

**Эксперимент с proxy_pass (главное):**
- Со слэшем (`http://backend_upstream/`): Nginx срезает /api/, Flask видит `/health` → 200.
- Без слэша (`http://backend_upstream`): Nginx оставляет /api/, Flask видит `/api/health` → 404.
- Подтверждено логами backend-а. Правило запомнил: **со слэшем — срезает, без слэша — оставляет**.
