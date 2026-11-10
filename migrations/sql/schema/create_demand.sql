-- ============================================================================
-- Schema: create_demand.sql
-- Models: Demand, DemandSourcingRound, DemandCandidate, PanelInfo, DemandFeedback, DemandEvent
-- ============================================================================

-- Enums
DO $$ BEGIN
    CREATE TYPE "DemandStatus" AS ENUM (
    'INITIATED',
    'VALIDATED',
    'REJECTED',
    'SENT_FOR_PROJECT_REVIEW',
    'UNDER_SCREENING',
    'FULFILLED',
    'ON_HOLD'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "DemandCandidateSource" AS ENUM (
    'INTERNAL',
    'EXTERNAL'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "DemandReviewStatus" AS ENUM (
    'PENDING',
    'NEEDS_SCREENING',
    'REJECTED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "DemandCandidateStatus" AS ENUM (
    'R1_SELECT',
    'R2_SELECT',
    'R1_REJECT',
    'R2_REJECT',
    'SUITABLE_FOR_OTHER_ROLE',
    'HIRED',
    'ON_HOLD'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "PanelRound" AS ENUM (
    'R1',
    'R2'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "PanelStatus" AS ENUM (
    'SCHEDULED',
    'COMPLETED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


-- Table: Demand
CREATE TABLE IF NOT EXISTS "Demand" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "demandNumber" VARCHAR(20) NOT NULL UNIQUE,
    "demandYear" INTEGER NOT NULL,
    "yearNumber" INTEGER NOT NULL,
    "projectId" VARCHAR(255) NOT NULL,
    "demandName" VARCHAR(500) NOT NULL,
    "skillCode" VARCHAR(50) NOT NULL,
    "positionsOpen" INTEGER NOT NULL,
    "jobDescription" VARCHAR(5000) NOT NULL,
    "projectExpectedDate" DATE,
    "tentativeFulfillmentDate" DATE,
    "actualFulfilledDate" DATE,
    "interviewPanelFromProject" BOOLEAN NOT NULL DEFAULT FALSE,
    "r1PanelEmail" VARCHAR(255),
    "r2PanelEmail" VARCHAR(255),
    status "DemandStatus" NOT NULL DEFAULT 'INITIATED',
    "initiatedBy" VARCHAR(255) NOT NULL,
    "initiatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "validatedBy" VARCHAR(255),
    "validatedAt" TIMESTAMP,
    "rejectionReason" VARCHAR(1000),
    "statusBeforeHold" "DemandStatus",
    "heldBy" VARCHAR(255),
    "heldAt" TIMESTAMP,
    "holdReason" VARCHAR(1000),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "modifiedBy" VARCHAR(255),
    CONSTRAINT uq_demand_demandyear_yearnumber UNIQUE ("demandYear", "yearNumber"),
    CONSTRAINT fk_demand_projectid FOREIGN KEY ("projectId") REFERENCES "ProjectName"(id)
);

CREATE INDEX IF NOT EXISTS idx_demand_projectid
ON "Demand" ("projectId");

CREATE INDEX IF NOT EXISTS idx_demand_status
ON "Demand" (status);


-- Table: DemandSourcingRound
CREATE TABLE IF NOT EXISTS "DemandSourcingRound" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "demandId" VARCHAR(255) NOT NULL,
    "roundNo" INTEGER NOT NULL,
    "internalProfilesAvailable" BOOLEAN,
    "sentForReviewAt" TIMESTAMP,
    "reviewCompletedAt" TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_demandsourcinground_demandid_roundno UNIQUE ("demandId", "roundNo"),
    CONSTRAINT fk_demandsourcinground_demandid FOREIGN KEY ("demandId") REFERENCES "Demand"(id) ON DELETE CASCADE
);


-- Table: DemandCandidate
CREATE TABLE IF NOT EXISTS "DemandCandidate" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "demandId" VARCHAR(255) NOT NULL,
    "sourcingRound" INTEGER NOT NULL,
    source "DemandCandidateSource" NOT NULL,
    "candidateName" VARCHAR(255) NOT NULL,
    "employeeMailId" VARCHAR(255),
    "primarySkill1" VARCHAR(50) NOT NULL,
    "primarySkill2" VARCHAR(50) NOT NULL,
    "resumeBlobName" VARCHAR(500) NOT NULL,
    "resumeFileName" VARCHAR(255) NOT NULL,
    "resumeMimeType" VARCHAR(100) NOT NULL,
    "reviewStatus" "DemandReviewStatus" NOT NULL DEFAULT 'PENDING',
    "reviewedBy" VARCHAR(255),
    "reviewedAt" TIMESTAMP,
    "candidateStatus" "DemandCandidateStatus",
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255) NOT NULL,
    "modifiedBy" VARCHAR(255),
    CONSTRAINT fk_demandcandidate_demandid FOREIGN KEY ("demandId") REFERENCES "Demand"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_demandcandidate_demandid_sourcinground
ON "DemandCandidate" ("demandId", "sourcingRound");


-- Table: PanelInfo
CREATE TABLE IF NOT EXISTS "PanelInfo" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "candidateId" VARCHAR(255) NOT NULL,
    round "PanelRound" NOT NULL,
    "panelEmail" VARCHAR(255) NOT NULL,
    "scheduledAt" TIMESTAMP NOT NULL,
    status "PanelStatus" NOT NULL DEFAULT 'SCHEDULED',
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255),
    CONSTRAINT uq_panelinfo_candidateid_round UNIQUE ("candidateId", round),
    CONSTRAINT fk_panelinfo_candidateid FOREIGN KEY ("candidateId") REFERENCES "DemandCandidate"(id) ON DELETE CASCADE
);


-- Table: DemandFeedback
CREATE TABLE IF NOT EXISTS "DemandFeedback" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "candidateId" VARCHAR(255) NOT NULL,
    round "PanelRound" NOT NULL,
    "candidateStatus" "DemandCandidateStatus" NOT NULL,
    feedback VARCHAR(3000) NOT NULL,
    "fileBlobName" VARCHAR(500),
    "fileName" VARCHAR(255),
    "fileMimeType" VARCHAR(100),
    "givenBy" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_demandfeedback_candidateid FOREIGN KEY ("candidateId") REFERENCES "DemandCandidate"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_demandfeedback_candidateid_round
ON "DemandFeedback" ("candidateId", round);


-- Table: DemandEvent
CREATE TABLE IF NOT EXISTS "DemandEvent" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "demandId" VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    note VARCHAR(1000),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_demandevent_demandid FOREIGN KEY ("demandId") REFERENCES "Demand"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_demandevent_demandid_createdat
ON "DemandEvent" ("demandId", "createdAt");

