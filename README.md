# MES-EDMS MVP

Система управления конструкторской документацией - MVP Phase 1 ("Конструкторский" модуль).

---

## Quick Start (3 minutes)

### Prerequisites

- Docker & Docker Compose installed
- Ports 3000, 5432, 8000 available

### Setup Steps

**Step 1: Clone and configure**
```bash
cd mes-edms-mvp

# Для Docker окружения (рекомендуется для быстрого старта)
cp env.example .env.docker
sed -i 's/@localhost:/@db:/g' .env.docker  # Linux/Mac
# или вручную заменить localhost на db в DATABASE_URL

# Для локальной разработки (опционально)
cp env.example .env
```

> **Примечание:** `.env.docker` используется для Docker окружения (хост БД = `db`), `.env` для локальной разработки (хост БД = `localhost`). Подробнее в разделе "Конфигурация окружений".

**Step 2: Start all services**
```bash
docker-compose up -d --build
```

**Step 3: Wait for services to be ready**
```bash
# Check health status
docker-compose ps
```

**Step 4: Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Login: `animobit12@mail.ru` / `adminpassword`

### Health Check
```bash
# Verify all services are running
docker-compose ps

# Check backend health
curl http://localhost:8000/health

# View logs if issues
docker-compose logs -f backend
```

### Load Demo Data (Optional)
```bash
docker-compose exec backend python scripts/seed_demo_data.py
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| PDF upload not working | Check `docker-compose logs -f backend` for errors. Verify storage volume is mounted. |
| Database connection error | Wait for db container to be healthy: `docker-compose ps` |
| Frontend shows 404 | Ensure backend is running: `curl http://localhost:8000/health` |
| Login fails | Verify admin was created: check migration logs or run seed script |

### Диагностика проблем с подключением к БД

**Блок 1: Проверка переменных окружения**
```bash
# Проверить DATABASE_URL в backend контейнере
docker-compose exec backend env | grep DATABASE

# Ожидаемый вывод:
# DATABASE_URL=postgresql://postgres:postgres@db:5432/mes_edms
```

**Блок 2: Проверка доступности PostgreSQL**
```bash
# Проверить статус контейнера БД
docker-compose ps db

# Проверить подключение к PostgreSQL из backend
docker-compose exec backend python -c "from app.database import engine; engine.connect()"

# Прямое подключение к PostgreSQL
docker-compose exec db psql -U postgres -d mes_edms -c "SELECT 1"
```

**Блок 3: Анализ логов**
```bash
# Логи backend (ошибки подключения к БД)
docker-compose logs backend | grep -i "database\\|connection\\|password"

# Логи PostgreSQL
docker-compose logs db | tail -50

# Следить за логами в реальном времени
docker-compose logs -f backend db
```

**Блок 4: Сброс и перезапуск**
```bash
# Полная очистка и перезапуск (ВНИМАНИЕ: удаляет данные!)
docker-compose down -v
docker-compose up -d --build

# Проверить healthcheck
curl http://localhost:8000/healthz/db
```

| Ошибка в логах | Причина | Решение |
|----------------|---------|---------|
| `could not connect to server: Connection refused` | PostgreSQL не запущен или недоступен | Проверить `docker-compose ps db`, перезапустить `docker-compose restart db` |
| `password authentication failed for user "postgres"` | Неверный пароль в DATABASE_URL | Проверить `POSTGRES_PASSWORD` в `.env.docker` и DATABASE_URL |
| `database "mes_edms" does not exist` | База данных не создана | Проверить `POSTGRES_DB` в docker-compose.yml, пересоздать контейнер |
| `FATAL: remaining connection slots are reserved` | Исчерпан лимит соединений PostgreSQL | Уменьшить `DB_POOL_SIZE` или увеличить `max_connections` в PostgreSQL |

---

## Структура проекта

```
mes-edms-mvp/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── docker-compose.yml
└── README.md
```

## Требования

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (для production)

## Локальная разработка

### Backend

```bash
cd backend

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt

# Скопировать и настроить переменные окружения
cp ../env.example .env
# Отредактировать .env файл

# Запустить миграции
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Установить зависимости
npm install

# Запустить dev сервер
npm run dev
```

## Docker

```bash
# Запустить все сервисы
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановить
docker-compose down
```

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| DATABASE_URL | PostgreSQL connection string | postgresql://postgres:postgres@localhost:5432/mes_edms |
| DB_POOL_SIZE | Размер пула соединений (количество постоянных соединений) | 10 |
| DB_MAX_OVERFLOW | Максимальное количество дополнительных соединений сверх pool_size | 20 |
| DB_POOL_PRE_PING | Проверка соединения перед использованием (защита от stale connections) | true |
| DB_POOL_RECYCLE | Время в секундах для автоматического переподключения | 3600 |
| DB_POOL_TIMEOUT | Таймаут ожидания доступного соединения из пула (сек) | 30 |
| DB_CONNECT_TIMEOUT | Таймаут установления соединения на уровне драйвера (сек) | 5 |
| DB_ECHO_POOL | Логирование событий пула соединений (для отладки) | false |
| SECRET_KEY | JWT secret key (256-bit) | - |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT token TTL | 480 (8 часов) |
| FILE_STORAGE_PATH | Путь для хранения файлов | /var/app/storage/documents |
| TECH_FILE_STORAGE_PATH | Путь для хранения технологических Excel-документов (fallback: FILE_STORAGE_PATH) | /var/app/storage/tech_documents |
| MAX_FILE_SIZE_MB | Максимальный размер файла | 100 |
| CORS_ORIGINS | Разрешенные origins | ["http://localhost:3000"] |
| ADMIN_EMAIL | Email администратора | animobit12@mail.ru |
| ADMIN_PASSWORD | Пароль администратора | - |

### Рекомендуемые настройки пула соединений

Примечание (production): `DB_POOL_SIZE` и `DB_MAX_OVERFLOW` задаются **на процесс/воркер**. Если у вас несколько воркеров, суммарное число соединений примерно равно `workers * (DB_POOL_SIZE + DB_MAX_OVERFLOW)` — учитывайте это при масштабировании (PostgreSQL `max_connections`, ресурсы сервера).

| Параметр | Development | Production | Описание |
|----------|-------------|------------|----------|
| `DB_POOL_SIZE` | 5 | 10-20 | Базовый размер пула |
| `DB_MAX_OVERFLOW` | 10 | 20-40 | Дополнительные соединения |
| `DB_POOL_PRE_PING` | true | true | Всегда включать |
| `DB_POOL_RECYCLE` | 3600 | 3600 | 1 час оптимально |
| `DB_POOL_TIMEOUT` | 30 | 30 | Таймаут ожидания |
| `DB_ECHO_POOL` | true | false | Только для отладки |

## Конфигурация окружений

### Разделение конфигураций: .env vs .env.docker

`.env` используется для локальной разработки (DATABASE_URL с `localhost`), `.env.docker` для Docker окружения (DATABASE_URL с хостом `db`)

| Файл | Назначение | DATABASE_URL | Использование |
|------|-----------|--------------|---------------|
| `.env` | Локальная разработка | `postgresql://postgres:postgres@localhost:5432/mes_edms` | Запуск backend напрямую через `uvicorn` |
| `.env.docker` | Docker окружение | `postgresql://postgres:postgres@db:5432/mes_edms` | Запуск через `docker-compose up` |

### Создание .env.docker для Docker

```bash
# Скопировать шаблон
cp env.example .env.docker

# Отредактировать DATABASE_URL: заменить localhost на db
# Linux/Mac:
sed -i 's/@localhost:/@db:/g' .env.docker

# Windows (PowerShell):
(Get-Content .env.docker) -replace '@localhost:', '@db:' | Set-Content .env.docker
```

- Примечание: `docker-compose.yml` автоматически использует `.env.docker` через директиву `env_file`

---

## Мониторинг здоровья системы

### Health Check Endpoints

Описание доступных endpoints:

**1. Базовый healthcheck приложения**
```bash
curl http://localhost:8000/health

# Ответ:
# {"status": "healthy"}
```
Назначение: Проверка работоспособности FastAPI приложения (не проверяет БД)

**2. Healthcheck подключения к БД**
```bash
curl http://localhost:8000/healthz/db

# Успешный ответ (HTTP 200):
# {"status": "ok"}

# Ошибка (HTTP 503):
# {"detail": "Database unavailable"}
```
Назначение: Проверка доступности PostgreSQL (выполняет `SELECT 1`)

### Startup Healthcheck

Описание: При запуске backend автоматически проверяет подключение к БД. Если БД недоступна, приложение не запустится (fail-fast стратегия).

Пример логов при успешном старте:
```
INFO: Database engine created with pool_size=10, max_overflow=20
INFO: ✓ Database connection successful
INFO: Application startup complete
```

### Интеграция с Docker Healthcheck

Описание: `docker-compose.yml` настроен на автоматическую проверку здоровья контейнеров:

```bash
# Проверить статус healthcheck
docker-compose ps

# Ожидаемый вывод:
# NAME                 STATUS
# mes_edms_backend     Up (healthy)
# mes_edms_db          Up (healthy)
# mes_edms_frontend    Up
```

Параметры healthcheck для backend:
- Интервал проверки: 10 секунд
- Таймаут: 5 секунд
- Количество попыток: 5

---

## Диаграмма: Разделение конфигураций

```mermaid
graph TD
    A[env.example] -->|cp + edit| B[.env]
    A -->|cp + sed| C[.env.docker]
    
    B -->|DATABASE_URL: localhost| D[Локальная разработка]
    C -->|DATABASE_URL: db| E[Docker окружение]
    
    D -->|uvicorn app.main:app| F[Backend процесс]
    E -->|docker-compose up| G[Backend контейнер]
    
    F -->|подключение| H[PostgreSQL на localhost:5432]
    G -->|подключение| I[PostgreSQL контейнер db:5432]
    
    style B fill:#e1f5ff
    style C fill:#fff4e1
    style D fill:#e1f5ff
    style E fill:#fff4e1
```

---

## API Документация

После запуска backend, документация доступна:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Учетные записи по умолчанию

После первого запуска миграций создается пользователь-администратор:
- Email: значение из ADMIN_EMAIL
- Пароль: значение из ADMIN_PASSWORD

## Безопасность

### Файловое хранилище

Рекомендуется монтировать директорию хранения файлов с флагом `noexec`:

```bash
mount -o noexec /var/app/storage
```

### JWT

- Access token: 8 часов TTL
- Хранение: в памяти на клиенте
- При истечении токена: переавторизация

## Тестирование

```bash
cd backend

# Запустить все тесты
pytest

# Запустить с coverage
pytest --cov=app

# Только unit тесты
pytest tests/unit/

# Только integration тесты
pytest tests/integration/
```

## Роли пользователей

| Роль | Возможности |
|------|-------------|
| admin | Полный доступ: управление пользователями, проектами, изделиями, документами |
| responsible | Загрузка документов и обновление прогресса для назначенных изделий |
| viewer | Только просмотр |

## Лицензия

Proprietary



## Технологический модуль

Функции:
- Просмотр Excel-документов для разделов проекта (ProjectSection)
- Загрузка/обновление/удаление документов с версиями
- Логи в audit log и notifications

API endpoints:
- GET /api/tech/sections/{section_id}/documents
- POST /api/tech/sections/{section_id}/documents
- GET /api/tech/documents/{document_id}
- GET /api/tech/documents/{document_id}/download
- GET /api/tech/documents/{document_id}/preview
- PUT /api/tech/documents/{document_id}
- DELETE /api/tech/documents/{document_id}?mode=soft|hard
- GET /api/tech/documents/{document_id}/versions

UI навигация:
- Технологический > проект > раздел > документы

RBAC:
- admin: полный доступ (upload/update/delete)
- non-admin: просмотр и скачивание
