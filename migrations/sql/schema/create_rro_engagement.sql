-- ============================================================================
-- Schema: create_rro_engagement.sql
-- Models: RroPhase, RroStep, RroSubStep, RroTaskTemplate, RroEngagement, RroTask, RroTaskComment, RroTaskEvidence
-- ============================================================================

-- Table: RroPhase
CREATE TABLE IF NOT EXISTS "RroPhase" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(150) NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "isActive" BOOLEAN NOT NULL DEFAULT TRUE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Table: RroStep
CREATE TABLE IF NOT EXISTS "RroStep" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "phaseId" VARCHAR(255) NOT NULL,
    name VARCHAR(150) NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "isActive" BOOLEAN NOT NULL DEFAULT TRUE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rrostep_phaseid FOREIGN KEY ("phaseId") REFERENCES "RroPhase"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rrostep_phaseid
ON "RroStep" ("phaseId");


-- Table: RroSubStep
CREATE TABLE IF NOT EXISTS "RroSubStep" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "stepId" VARCHAR(255) NOT NULL,
    name VARCHAR(200) NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "isActive" BOOLEAN NOT NULL DEFAULT TRUE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rrosubstep_stepid FOREIGN KEY ("stepId") REFERENCES "RroStep"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rrosubstep_stepid
ON "RroSubStep" ("stepId");


-- Table: RroTaskTemplate
CREATE TABLE IF NOT EXISTS "RroTaskTemplate" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "subStepId" VARCHAR(255) NOT NULL,
    name VARCHAR(300) NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "isActive" BOOLEAN NOT NULL DEFAULT TRUE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rrotasktemplate_substepid FOREIGN KEY ("subStepId") REFERENCES "RroSubStep"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rrotasktemplate_substepid
ON "RroTaskTemplate" ("subStepId");


-- Table: RroEngagement
CREATE TABLE IF NOT EXISTS "RroEngagement" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(200) NOT NULL,
    "emMail" VARCHAR(255),
    "emName" VARCHAR(150),
    "engagementType" VARCHAR(50) NOT NULL,
    "opportunityId" VARCHAR(50) NOT NULL UNIQUE,
    "projectId" VARCHAR(255),
    "isActive" BOOLEAN NOT NULL DEFAULT TRUE,
    "overrideValue" INTEGER,
    "overrideReason" VARCHAR(1000),
    "overrideBy" VARCHAR(255),
    "overrideAt" TIMESTAMP,
    "lastActivityAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_rroengagement_isactive
ON "RroEngagement" ("isActive");


-- Table: RroTask
CREATE TABLE IF NOT EXISTS "RroTask" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "engagementId" VARCHAR(255) NOT NULL,
    "taskTemplateId" VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'NotStarted',
    "ownerMail" VARCHAR(255),
    "dueDate" DATE,
    "completedAt" TIMESTAMP,
    "completedBy" VARCHAR(255),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedBy" VARCHAR(255),
    CONSTRAINT uq_rrotask_engagementid_tasktemplateid UNIQUE ("engagementId", "taskTemplateId"),
    CONSTRAINT fk_rrotask_engagementid FOREIGN KEY ("engagementId") REFERENCES "RroEngagement"(id) ON DELETE CASCADE,
    CONSTRAINT fk_rrotask_tasktemplateid FOREIGN KEY ("taskTemplateId") REFERENCES "RroTaskTemplate"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rrotask_engagementid
ON "RroTask" ("engagementId");


-- Table: RroTaskComment
CREATE TABLE IF NOT EXISTS "RroTaskComment" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "taskId" VARCHAR(255) NOT NULL,
    text VARCHAR(2000) NOT NULL,
    "authorMail" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rrotaskcomment_taskid FOREIGN KEY ("taskId") REFERENCES "RroTask"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rrotaskcomment_taskid
ON "RroTaskComment" ("taskId");


-- Table: RroTaskEvidence
CREATE TABLE IF NOT EXISTS "RroTaskEvidence" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "taskId" VARCHAR(255) NOT NULL,
    kind VARCHAR(10) NOT NULL,
    name VARCHAR(300) NOT NULL,
    url VARCHAR(1000),
    "blobName" VARCHAR(500),
    "mimeType" VARCHAR(150),
    "sizeBytes" INTEGER,
    "addedBy" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rrotaskevidence_taskid FOREIGN KEY ("taskId") REFERENCES "RroTask"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rrotaskevidence_taskid
ON "RroTaskEvidence" ("taskId");

