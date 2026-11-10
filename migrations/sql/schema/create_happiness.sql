-- ============================================================================
-- Schema: create_happiness.sql
-- Models: HappinessAllocationState, HappinessMembership, HappinessLedgerEntry, HappinessChiefEvent, HappinessMediaFolder, HappinessMedia
-- ============================================================================

-- Enums
DO $$ BEGIN
    CREATE TYPE "HappinessHouse" AS ENUM (
    'APOLLO',
    'LUNA',
    'ATLAS',
    'PHOENIX',
    'NOVA',
    'TERRA',
    'ORION'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


-- Table: HappinessAllocationState
CREATE TABLE IF NOT EXISTS "HappinessAllocationState" (
    id INTEGER PRIMARY KEY DEFAULT 1,
    "initialAllocatedAt" TIMESTAMP NOT NULL,
    "initialAllocatedBy" VARCHAR(255) NOT NULL,
    "lastAllocatedAt" TIMESTAMP NOT NULL,
    "lastAllocatedBy" VARCHAR(255) NOT NULL
);


-- Table: HappinessMembership
CREATE TABLE IF NOT EXISTS "HappinessMembership" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeId" VARCHAR(255) NOT NULL UNIQUE,
    house "HappinessHouse" NOT NULL,
    "pointsEarned" INTEGER NOT NULL DEFAULT 0,
    "joinedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_happinessmembership_employeeid FOREIGN KEY ("employeeId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_happinessmembership_house
ON "HappinessMembership" (house);


-- Table: HappinessLedgerEntry
CREATE TABLE IF NOT EXISTS "HappinessLedgerEntry" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    house "HappinessHouse",
    points INTEGER NOT NULL,
    category VARCHAR(50) NOT NULL,
    description VARCHAR(500) NOT NULL,
    "membershipId" VARCHAR(255),
    "loggedByEmail" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_happinessledgerentry_membershipid FOREIGN KEY ("membershipId") REFERENCES "HappinessMembership"(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_happinessledgerentry_createdat
ON "HappinessLedgerEntry" ("createdAt");

CREATE INDEX IF NOT EXISTS idx_happinessledgerentry_membershipid
ON "HappinessLedgerEntry" ("membershipId");


-- Table: HappinessChiefEvent
CREATE TABLE IF NOT EXISTS "HappinessChiefEvent" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "chiefOrder" INTEGER NOT NULL,
    "chiefArea" VARCHAR(150) NOT NULL,
    title VARCHAR(255) NOT NULL,
    "eventDate" DATE NOT NULL,
    description VARCHAR(1000),
    "displayDays" INTEGER NOT NULL DEFAULT 7,
    "displayUntil" DATE NOT NULL,
    "createdByEmail" VARCHAR(255) NOT NULL,
    "updatedByEmail" VARCHAR(255),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_happinesschiefevent_chieforder
ON "HappinessChiefEvent" ("chiefOrder");


-- Table: HappinessMediaFolder
CREATE TABLE IF NOT EXISTS "HappinessMediaFolder" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(100) NOT NULL UNIQUE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Table: HappinessMedia
CREATE TABLE IF NOT EXISTS "HappinessMedia" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "folderId" VARCHAR(255) NOT NULL,
    "blobName" VARCHAR(500) NOT NULL,
    "fileName" VARCHAR(255) NOT NULL,
    "mimeType" VARCHAR(100),
    description VARCHAR(500),
    "uploadedByEmail" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_happinessmedia_folderid FOREIGN KEY ("folderId") REFERENCES "HappinessMediaFolder"(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_happinessmedia_folderid
ON "HappinessMedia" ("folderId");

