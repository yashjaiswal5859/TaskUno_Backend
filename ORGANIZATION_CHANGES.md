# Organization Changes - Database Schema Updates

## Summary
Both ProductOwner and Developer now have `organization_id` column and are linked directly to Organization. Email uniqueness is now per organization (email + organization_id combination).

## Database Schema Changes

### ProductOwner Table
- **Removed**: `email` unique constraint
- **Added**: Composite unique constraint on `(email, organization_id)`
- **Changed**: `organization_id` is now `nullable=False` (required)

### Developer Table
- **Added**: `organization_id` column (ForeignKey to `organization.id`, nullable=False)
- **Removed**: `email` unique constraint
- **Added**: Composite unique constraint on `(email, organization_id)`
- **Added**: `organization` relationship

## API Changes

### Registration (`POST /auth/`)
- **New field**: `org_id` (optional) - if provided, uses existing organization
- **Behavior**: 
  - If `org_id` provided: uses that organization
  - If `org_id` not provided: creates/finds organization by name
  - Checks email uniqueness **within the organization only**
  - Same email can exist in different organizations

### Invitation (`POST /auth/invite`)
- **New field**: `org_id` (optional) - if provided, uses that organization
- **Behavior**:
  - If `org_id` provided: uses that organization
  - If `org_id` not provided: uses inviter's organization
  - Checks email uniqueness **within the organization only**
  - Sets `organization_id` for both ProductOwner and Developer

## Validation Logic

### Email Uniqueness
- **Old**: Email must be unique across all tables
- **New**: Email must be unique **per organization** (email + organization_id)
- **Result**: Same email can exist in different organizations

### Example
- `user@example.com` in Organization A ✅
- `user@example.com` in Organization B ✅ (allowed)
- `user@example.com` in Organization A again ❌ (not allowed)

## Migration Required

You need to run a database migration to:
1. Add `organization_id` column to `developer` table
2. Remove unique constraint from `email` in both `product_owner` and `developer` tables
3. Add composite unique constraints: `(email, organization_id)` for both tables
4. Update existing Developer records to have `organization_id` (can be derived from their owner's organization_id)

## Code Changes

### Models
- `ProductOwner`: Removed email unique, added composite unique constraint
- `Developer`: Added `organization_id` column and composite unique constraint

### Repository
- `email_exists_in_organization()`: New method to check email + org_id
- `email_exists_anywhere()`: Kept for backward compatibility

### Service
- `register_user()`: Now checks email + org_id, accepts `org_id` in payload
- `invite_user()`: Now checks email + org_id, accepts `org_id` in payload, sets org_id for Developer

### Schemas
- `UserCreate`: Added optional `org_id` field
- `InviteUserRequest`: Added optional `org_id` field


