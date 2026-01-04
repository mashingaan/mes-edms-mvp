# MES-EDMS Demo Script

## Prerequisites

1. System is running via `docker-compose up` or locally
2. Database migrations applied (`alembic upgrade head`)
3. Admin user created (see seed migration)

## Login Credentials

- **Email:** `admin@example.com`
- **Password:** `adminpassword` (or value from `.env` ADMIN_PASSWORD)

## Seed Demo Data (1 min)

1. Run `docker-compose exec backend python scripts/seed_demo_data.py`
2. This pre-imports sample PDFs so the import-first UX can be demoed without manual setup.

Sample filenames pre-imported:

**Project: Turbine Assembly A-100**
- `БНС.КМД.123.456.789.001 Корпус.pdf`
- `БНС.КМД.123.456.789.002 Крышка.pdf`
- `БНС.ТХ.24. Ротор сборка.pdf`

**Project: Control Panel B-200**
- `ЭЛ.ПУ.111.222.333.001 Main Board.pdf`
- `ЭЛ.ПУ.111.222.333.002 Power Supply.pdf`
- `МЕХ.СБ.45. Панель интерфейса.pdf`

---

## Demo Walkthrough (10-15 minutes)

### 1. Login and Dashboard (2 min)

1. Open `http://localhost:3000`
2. Enter admin credentials
3. Click "Войти"
4. View the dashboard with system overview

### 2. Project Creation (2 min)

1. Navigate to "Проекты" in sidebar
2. Click "Создать проект"
3. Enter project details:
   - Name: "Изделие А-100"
   - Description: "Разработка нового изделия"
4. Click "Создать"
5. Project appears in the list

### 3. File Import Workflow (3 min)

1. Click on the created project (or use pre-seeded "Turbine Assembly A-100")
2. Click "Импортировать файлы"
3. Import modal opens
4. Select PDF files to upload (use these sample filenames):
   - `БНС.КМД.123.456.789.001 Корпус.pdf`
   - `БНС.КМД.123.456.789.002 Крышка.pdf`
   - `БНС.ТХ.24. Ротор сборка.pdf`
5. Preview shows parsed data:
   - Detected section code (e.g., "БНС.КМД")
   - Part number extracted from filename (e.g., "123.456.789.001")
   - Name extracted from filename (e.g., "Корпус")
6. Optionally select section override and responsible user
7. Click "Импортировать"
8. Success message shows created items count
9. Verify items appear in project with:
   - Correct section assignment (visible as badge)
   - Original filename displayed
   - Documents attached

### 3.1 Section Filtering (1 min)

1. In project detail page, notice Section Selector tabs
2. Click "Все" to show all items
3. Click "БНС.КМД" to filter items in that section
4. Click "БНС.ТХ" to filter items in that section
5. Click "Без раздела" to show items without section assignment

### 4. PDF Upload and Revision Management (3 min)

1. Click on first item (Корпус)
2. Click "Загрузить документ"
3. Select a PDF file
4. Document appears with revision "-" (initial)
5. Upload another version of the document
6. Revision automatically increments to "A"
7. Upload again - revision becomes "B"
8. Show revision history panel

### 5. Progress Tracking (2 min)

1. On item detail page, find progress section
2. Click edit progress
3. Change progress from 0% to 45%
4. Add comment: "Завершен первый этап"
5. Save changes
6. Show progress history with timestamps

### 6. Notifications (1 min)

1. Click notification bell in header
2. Show notifications for:
   - Document uploads
   - Progress changes
3. Click notification to navigate to related item

### 7. Audit Log (2 min)

1. Navigate to "Аудит" in sidebar
2. Show list of all actions:
   - User logins
   - Project/item creation
   - Document uploads
   - Progress updates
3. Demonstrate filtering by action type

### 8. RBAC Demonstration (2 min)

**Show three role levels:**

1. **Admin (current user):**
   - Can create/edit/delete projects and items
   - Can manage users
   - Full access to audit log

2. **Responsible:**
   - Can view assigned items
   - Can upload documents to assigned items
   - Can update progress on assigned items
   - Cannot delete projects

3. **Viewer:**
   - Read-only access to all projects/items
   - Can view documents
   - Cannot edit or upload

---

## Key Features to Highlight

- **File Import:** Upload PDFs to create items automatically with filename parsing
- **Sections:** Organize items within projects (auto-detected from filenames)
- **Original Filename:** Track source filename in item cards and details
- **Revision Control:** Automatic revision increment (-, A, B, C...)
- **Progress History:** Full audit trail of progress changes
- **Notifications:** Real-time updates for relevant actions
- **RBAC:** Role-based access control
- **Audit Log:** Complete action history

---

## Troubleshooting During Demo

### PDF Upload Not Working
- Check backend logs: `docker-compose logs -f backend`
- Verify storage path exists: `/var/app/storage/documents`
- Check file size limit (default 100MB)

### Login Issues
- Verify database has admin user
- Check password in `.env` file
- Run seed script if needed

### Frontend Not Loading
- Check if backend is running: `http://localhost:8000/docs`
- Verify CORS settings in docker-compose.yml
- Check browser console for errors

