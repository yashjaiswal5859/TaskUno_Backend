# Migration Instructions: Developer Organization Structure

## Overview
This migration updates the `developer` table to ensure:
1. `organization_id` is required (NOT NULL) - developers must belong to an organization
2. `owner_id` remains nullable - only used for task assignments, NOT during registration/invite
3. Composite unique constraint on `(email, organization_id)` instead of just `email`

## Changes Made

### Code Changes (Already Applied)
- ✅ Removed `owner_id` assignment during developer invite/registration
- ✅ Developers now only link to organization during registration/invite
- ✅ `owner_id` is only set during task assignment

### Database Migration Required

#### Option 1: Using Alembic (Recommended)
```bash
cd backend
alembic upgrade head
```

This will run the migration file: `alembic/versions/update_developer_table_organization.py`

#### Option 2: Manual SQL Script (If Alembic doesn't work)
```bash
cd backend
sqlite3 your_database.db < migrate_developer_organization.sql
```

Or for PostgreSQL/MySQL:
```bash
psql -d your_database -f migrate_developer_organization.sql
```

## What the Migration Does

1. **Adds `organization_id` column** (if it doesn't exist)
   - Sets it to NOT NULL
   - Adds foreign key to `organization` table

2. **Updates existing records**
   - Sets `organization_id` for existing developers based on their `owner_id` (if owner exists)
   - Ensures all developers have an organization

3. **Updates constraints**
   - Removes single `email` unique constraint
   - Adds composite unique constraint on `(email, organization_id)`
   - Keeps `owner_id` nullable (for task assignments only)

4. **Preserves data**
   - All existing developer records are preserved
   - Only adds missing `organization_id` values

## Verification

After running the migration, verify:

```sql
-- Check table structure
PRAGMA table_info(developer);  -- SQLite
-- OR
\d developer;  -- PostgreSQL

-- Verify organization_id is NOT NULL
SELECT COUNT(*) FROM developer WHERE organization_id IS NULL;
-- Should return 0

-- Verify owner_id can be NULL (for new developers)
SELECT COUNT(*) FROM developer WHERE owner_id IS NULL;
-- Should be >= 0 (some developers may not have tasks assigned)
```

## Rollback

If you need to rollback:

```bash
alembic downgrade -1
```

Or manually revert using the `downgrade()` function in the migration file.

## Notes

- **`owner_id` is NOT removed** - it's still needed for task assignments
- **`owner_id` is nullable** - developers don't need to be linked to an owner during registration
- **`organization_id` is required** - all developers must belong to an organization
- The relationship between developer and owner is now **only for tasks**, not for organizational hierarchy

