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


## 2026-09-29: Frontend (HTML+JS) + отдача статики через Nginx

**Задача:** HTML-страница с формой для создания коротких ссылок.

**Выполнено:**
- `frontend/index.html` — форма: input URL + кнопка + JS через `fetch('/api/shorten')`.
- Nginx отдаёт статику через `try_files /index.html =404;` в `location = /`.
- Nginx проксирует короткие ссылки: `location ~ ^/[A-Za-z0-9_-]+$` → backend (без слэша).
- Volume `./frontend:/usr/share/nginx/html:ro` в docker-compose.yml.
- **Проверено в браузере:** форма работает, ссылка `http://localhost:8080/BB_LUJ8C` создана.

**Ошибки и решения:**
- YAML: `nginx` был вложен в `backend` (неверный отступ) → 2 пробела на одном уровне.
- `root + index` → Nginx искал файл в `/etc/nginx/html/index.html` (непонятная резолюция).
  Решение: **`root + try_files /index.html =404;`** без `index`.
- `alias` + `index` → путь склеивался (`index.htmlindex.html`) → 500.
- Nginx не перечитывает конфиг без `restart` или `nginx -s reload`.

**Что понял:**
- `try_files` — самый гибкий способ отдать конкретный файл.
- `alias` указывает на файл, `root` — на директорию.
- **Канонический паттерн:** `root` + `try_files`.

## 2026-09-30: Frontend (HTML + CSS + JS) и статика через Nginx

**Задача:** добавить фронтенд — простую форму для создания коротких ссылок, отдаваемую Nginx как статика.

**Выполнено:**
- Созданы `frontend/index.html`, `frontend/style.css`, `frontend/app.js`.
- Форма: поле URL + кнопка «Сократить», асинхронный запрос через `fetch` на `/api/shorten`.
- В `nginx/nginx.conf` добавлен `location /` с `root /usr/share/nginx/html` и `index index.html`.
- В `docker-compose.yml` смонтирован том `./frontend:/usr/share/nginx/html:ro`.
- Проверено: `/` отдаёт HTML, `/style.css` и `/app.js` — 200 OK, `/api/*` — проксируется на backend.
- Полный цикл: форма в браузере → POST /api/shorten → короткая ссылка → клик → редирект на GitHub.

**Проблемы и решения:**
- Сначала CSS и JS отдавались с `Content-Type: text/plain`. Причина: наш `nginx.conf` заменил стандартный и не подключал `mime.types`.
- Решение: добавить `include /etc/nginx/mime.types;` и `default_type application/octet-stream;` в блок `http`.

**Что понял:**
- `location /` — самое общее правило, но Nginx выбирает самое специфичное (`/api/` побеждает).
- `root` — это корень файловой системы для URL, не путать с `alias`.
- Volume для статики — правильный подход: файлы меняются без пересборки образа Nginx.
- MIME-типы — не роскошь, а стандарт.

## 2026-10-02: Kubernetes — Redis, Nginx, ConfigMap, NodePort

**Задача:** завершить перенос всего стека в Kubernetes — добавить Redis и Nginx (с ConfigMap для конфига и статики).

**Выполнено:**
- `k8s/redis.yaml`: Deployment + Service (ClusterIP, порт 6379).
- `k8s/nginx.yaml`: ConfigMap `nginx-config` (nginx.conf как inline), Deployment, Service типа NodePort (30080).
- ConfigMap `frontend-static` создан через `kubectl create configmap --from-file`.
- Все четыре сервиса в K8s: backend, postgres, redis, nginx.
- Проверен полный цикл: `POST http://nginx:8080/api/shorten` → `{"short":"hFLaurt-"}` → запись в PostgreSQL.
- `SELECT` из Postgres подтвердил две записи.

**Проблемы и решения:**
- YAML-ошибки отступов (`mapping values are not allowed`, `did not find expected '-' indicator`) — исправлены руками.
- `docker cp` в `/tmp/` не работает для `kubectl create configmap` — как и с образом, нужно `/var/lib/`.
- ConfigMap `frontend-static` создаётся **не из манифеста**, а через `kubectl create configmap --from-file`. В git лежит только nginx-config.

**Что понял:**
- ConfigMap — способ доставки конфигов и статики в поды (вместо volume-ов с хоста).
- `subPath` в `volumeMounts` — монтирует **один ключ** ConfigMap как **файл**.
- Без `subPath` монтируется вся папка.
- NodePort открывает порт на каждой ноде кластера (диапазон 30000–32767).
- YAML: отступы критичны, пробелы (не табы), одинаковый уровень = одинаковое количество.
