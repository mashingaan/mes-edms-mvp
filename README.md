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
cp env.example .env
# Edit .env if needed (default values work for demo)
```

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
- Login: `admin@example.com` / `adminpassword`

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
| SECRET_KEY | JWT secret key (256-bit) | - |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT token TTL | 480 (8 часов) |
| FILE_STORAGE_PATH | Путь для хранения файлов | /var/app/storage/documents |
| TECH_FILE_STORAGE_PATH | Путь для хранения технологических Excel-документов (fallback: FILE_STORAGE_PATH) | /var/app/storage/tech_documents |
| MAX_FILE_SIZE_MB | Максимальный размер файла | 100 |
| CORS_ORIGINS | Разрешенные origins | ["http://localhost:3000"] |
| ADMIN_EMAIL | Email администратора | admin@example.com |
| ADMIN_PASSWORD | Пароль администратора | - |

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

