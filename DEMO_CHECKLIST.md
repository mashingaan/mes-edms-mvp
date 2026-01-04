# Demo Verification Checklist

## Setup
- [ ] docker-compose up --build works from clean machine
- [ ] Alembic migrations run automatically
- [ ] Admin credentials documented (admin@example.com)

## Demo Flow
- [ ] Project deletion button visible and functional
- [ ] PDF upload working (file saved to storage)
- [ ] Revision management (-, A, B increments)
- [ ] Progress tracking with history
- [ ] Notifications on upload/progress
- [ ] Audit log shows all actions
- [ ] RBAC works (viewer/responsible/admin)

## File Import Feature
- [ ] Sections are visible in project detail page
- [ ] Section selector filters items correctly
- [ ] Import modal opens and displays file selection
- [ ] Parsed preview is shown inline (filename, section, name)
- [ ] Import creates items with documents
- [ ] original_filename is displayed in item cards
- [ ] Section badge is displayed in item cards
- [ ] Audit log shows import actions (item.import)
- [ ] Notifications are sent to responsible users and admins

## Quick Start
- [ ] README has 3-minute setup instructions
- [ ] DEMO_SCRIPT.md is complete and tested

