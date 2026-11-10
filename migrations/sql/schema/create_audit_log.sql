-- ============================================================================
-- Schema: create_audit_log.sql
-- Models: AuditLog
-- ============================================================================

-- Enums
DO $$ BEGIN
    CREATE TYPE "AuditAction" AS ENUM (
    'CREATE',
    'UPDATE',
    'DELETE'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


-- Table: AuditLog
CREATE TABLE IF NOT EXISTS "AuditLog" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "entityType" VARCHAR(50) NOT NULL,
    "entityId" VARCHAR(100),
    action "AuditAction" NOT NULL,
    "actorEmail" VARCHAR(255),
    method VARCHAR(10) NOT NULL,
    path VARCHAR(500) NOT NULL,
    "requestBody" JSONB,
    "statusCode" INTEGER NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_auditlog_entitytype_entityid
ON "AuditLog" ("entityType", "entityId");

CREATE INDEX IF NOT EXISTS idx_auditlog_actoremail
ON "AuditLog" ("actorEmail");

CREATE INDEX IF NOT EXISTS idx_auditlog_createdat
ON "AuditLog" ("createdAt");

