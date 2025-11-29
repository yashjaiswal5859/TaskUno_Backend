-- Migration script to update developer table for organization structure
-- This ensures:
-- 1. organization_id exists and is NOT NULL
-- 2. owner_id remains nullable (only for task assignments)
-- 3. Composite unique constraint on (email, organization_id)

-- Step 1: Add organization_id if it doesn't exist
-- (Check first: SELECT sql FROM sqlite_master WHERE type='table' AND name='developer';)

-- For SQLite, we need to recreate the table
BEGIN TRANSACTION;

-- Create new table with correct structure
CREATE TABLE developer_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50),
    email VARCHAR(255),
    "firstName" VARCHAR(50),
    "lastName" VARCHAR(50),
    password VARCHAR(255),
    owner_id INTEGER REFERENCES product_owner(id) ON DELETE SET NULL,  -- Nullable: only for task assignments
    organization_id INTEGER NOT NULL REFERENCES organization(id) ON DELETE SET NULL,  -- NOT NULL: required
    UNIQUE(email, organization_id)
);

-- Copy data from old table, setting organization_id from owner if missing
INSERT INTO developer_new 
(id, username, email, "firstName", "lastName", password, owner_id, organization_id)
SELECT 
    id, 
    username, 
    email, 
    "firstName", 
    "lastName", 
    password, 
    owner_id,
    COALESCE(
        (SELECT organization_id FROM developer WHERE developer.id = d.id),
        (SELECT organization_id FROM product_owner WHERE product_owner.id = d.owner_id)
    ) as organization_id
FROM developer d;

-- Drop old table
DROP TABLE developer;

-- Rename new table
ALTER TABLE developer_new RENAME TO developer;

COMMIT;

-- Verify the changes
-- SELECT sql FROM sqlite_master WHERE type='table' AND name='developer';

