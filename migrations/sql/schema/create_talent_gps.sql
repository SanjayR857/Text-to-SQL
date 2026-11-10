-- ============================================================================
-- Schema: create_talent_gps.sql
-- Models: EmployeeTalentGPSInfo, TalentDotOfFameNomination, TalentCertification, TalentAiCertification, TalentTrainingDelivery, TalentMentoring, TalentAiTraining, TalentAiBadge, TalentRecognition, TalentUpskillingWindowOverride, TalentUpskillingPlan, TalentUpskillingTraining, TalentFutureSkill, TalentLegacyIdea, TalentLegacyIdeaAttachment, TalentOption
-- ============================================================================

-- Table: EmployeeTalentGPSInfo
CREATE TABLE IF NOT EXISTS "EmployeeTalentGPSInfo" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeMailId" VARCHAR(255) NOT NULL UNIQUE,
    "currentProjectWorkStream" VARCHAR(255) NOT NULL,
    "primarySkill1" VARCHAR(50) NOT NULL,
    "primarySkill1Proficiency" VARCHAR(20) NOT NULL,
    "primarySkill2" VARCHAR(50),
    "primarySkill2Proficiency" VARCHAR(20),
    "secondarySkill1" VARCHAR(50),
    "secondarySkill1Proficiency" VARCHAR(20),
    "secondarySkill2" VARCHAR(50),
    "secondarySkill2Proficiency" VARCHAR(20),
    "isSmePrimary1" BOOLEAN NOT NULL DEFAULT FALSE,
    "isSmePrimary2" BOOLEAN NOT NULL DEFAULT FALSE,
    "isSmeSecondary1" BOOLEAN NOT NULL DEFAULT FALSE,
    "isSmeSecondary2" BOOLEAN NOT NULL DEFAULT FALSE,
    "interestedInTrainingDelivery" BOOLEAN NOT NULL,
    "attendedAgileTraining" BOOLEAN NOT NULL DEFAULT FALSE,
    "attendedAgileTrainingYear" VARCHAR(20),
    "attendedAgileTrainingComments" TEXT,
    "attendedSafeTraining" BOOLEAN NOT NULL DEFAULT FALSE,
    "attendedSafeTrainingYear" VARCHAR(20),
    "attendedSafeTrainingComments" TEXT,
    "attendedSoftSkillsTraining" BOOLEAN NOT NULL DEFAULT FALSE,
    "attendedSoftSkillsTrainingYear" VARCHAR(20),
    "attendedSoftSkillsTrainingComments" TEXT,
    "attendedAiTraining" BOOLEAN NOT NULL DEFAULT FALSE,
    "attendedAiTrainingDetails" VARCHAR(500),
    "hasAiCertification" BOOLEAN NOT NULL DEFAULT FALSE,
    "hasAiBadge" BOOLEAN NOT NULL DEFAULT FALSE,
    "businessChemistry" VARCHAR(50),
    "hasMentored" BOOLEAN NOT NULL DEFAULT FALSE,
    "mentoredDetails" TEXT,
    "mentoredCount" INTEGER,
    "mentoringType" VARCHAR(20),
    "hasNominatedDotOfFame" BOOLEAN NOT NULL DEFAULT FALSE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255),
    CONSTRAINT fk_employeetalentgpsinfo_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_employeetalentgpsinfo_employeemailid
ON "EmployeeTalentGPSInfo" ("employeeMailId");


-- Table: TalentDotOfFameNomination
CREATE TABLE IF NOT EXISTS "TalentDotOfFameNomination" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "talentGpsId" VARCHAR(255) NOT NULL,
    "nomineeMailId" VARCHAR(255) NOT NULL,
    "recognizedAt" DATE NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_talentdotoffamenomination_talentgpsid FOREIGN KEY ("talentGpsId") REFERENCES "EmployeeTalentGPSInfo"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentdotoffamenomination_talentgpsid
ON "TalentDotOfFameNomination" ("talentGpsId");


-- Table: TalentCertification
CREATE TABLE IF NOT EXISTS "TalentCertification" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "talentGpsId" VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    "validUntil" DATE,
    "expectedBy" DATE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "attachmentBlobName" VARCHAR(500),
    "attachmentFileName" VARCHAR(255),
    "attachmentMimeType" VARCHAR(100),
    CONSTRAINT fk_talentcertification_talentgpsid FOREIGN KEY ("talentGpsId") REFERENCES "EmployeeTalentGPSInfo"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentcertification_talentgpsid
ON "TalentCertification" ("talentGpsId");


-- Table: TalentAiCertification
CREATE TABLE IF NOT EXISTS "TalentAiCertification" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "talentGpsId" VARCHAR(255) NOT NULL,
    source VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    "validityDate" DATE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_talentaicertification_talentgpsid FOREIGN KEY ("talentGpsId") REFERENCES "EmployeeTalentGPSInfo"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentaicertification_talentgpsid
ON "TalentAiCertification" ("talentGpsId");


-- Table: TalentTrainingDelivery
CREATE TABLE IF NOT EXISTS "TalentTrainingDelivery" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "talentGpsId" VARCHAR(255) NOT NULL,
    topic VARCHAR(50) NOT NULL,
    "expertiseLevel" VARCHAR(20) NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_talenttrainingdelivery_talentgpsid FOREIGN KEY ("talentGpsId") REFERENCES "EmployeeTalentGPSInfo"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talenttrainingdelivery_talentgpsid
ON "TalentTrainingDelivery" ("talentGpsId");


-- Table: TalentMentoring
CREATE TABLE IF NOT EXISTS "TalentMentoring" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "talentGpsId" VARCHAR(255) NOT NULL,
    "mentoringType" VARCHAR(20) NOT NULL,
    "mentoredCount" INTEGER,
    "mentoredDetails" TEXT NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_talentmentoring_talentgpsid FOREIGN KEY ("talentGpsId") REFERENCES "EmployeeTalentGPSInfo"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentmentoring_talentgpsid
ON "TalentMentoring" ("talentGpsId");


-- Table: TalentAiTraining
CREATE TABLE IF NOT EXISTS "TalentAiTraining" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "talentGpsId" VARCHAR(255) NOT NULL,
    "trainingType" VARCHAR(10),
    "trainingName" VARCHAR(500) NOT NULL,
    platform VARCHAR(100),
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_talentaitraining_talentgpsid FOREIGN KEY ("talentGpsId") REFERENCES "EmployeeTalentGPSInfo"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentaitraining_talentgpsid
ON "TalentAiTraining" ("talentGpsId");


-- Table: TalentAiBadge
CREATE TABLE IF NOT EXISTS "TalentAiBadge" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "talentGpsId" VARCHAR(255) NOT NULL,
    "badgeType" VARCHAR(30) NOT NULL,
    level VARCHAR(10) NOT NULL,
    year INTEGER NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_talentaibadge_talentgpsid FOREIGN KEY ("talentGpsId") REFERENCES "EmployeeTalentGPSInfo"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentaibadge_talentgpsid
ON "TalentAiBadge" ("talentGpsId");


-- Table: TalentRecognition
CREATE TABLE IF NOT EXISTS "TalentRecognition" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "talentGpsId" VARCHAR(255) NOT NULL,
    type VARCHAR(30) NOT NULL,
    name VARCHAR(255) NOT NULL,
    "blobName" VARCHAR(500) NOT NULL,
    "fileName" VARCHAR(255) NOT NULL,
    "fileSize" INTEGER,
    "mimeType" VARCHAR(100),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    CONSTRAINT fk_talentrecognition_talentgpsid FOREIGN KEY ("talentGpsId") REFERENCES "EmployeeTalentGPSInfo"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentrecognition_talentgpsid
ON "TalentRecognition" ("talentGpsId");


-- Table: TalentUpskillingWindowOverride
CREATE TABLE IF NOT EXISTS "TalentUpskillingWindowOverride" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    quarter VARCHAR(2) NOT NULL,
    "windowStartDate" TIMESTAMP NOT NULL,
    "windowEndDate" TIMESTAMP NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "modifiedBy" VARCHAR(255),
    CONSTRAINT uq_talentupskillingwindowoverride_appraisalyearid_quarter UNIQUE ("appraisalYearId", quarter),
    CONSTRAINT fk_talentupskillingwindowoverride_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);


-- Table: TalentUpskillingPlan
CREATE TABLE IF NOT EXISTS "TalentUpskillingPlan" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    "emAlignmentConfirmed" BOOLEAN NOT NULL DEFAULT FALSE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255),
    CONSTRAINT uq_talentupskillingplan_employeemailid_appraisalyearid UNIQUE ("employeeMailId", "appraisalYearId"),
    CONSTRAINT fk_talentupskillingplan_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE,
    CONSTRAINT fk_talentupskillingplan_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentupskillingplan_employeemailid
ON "TalentUpskillingPlan" ("employeeMailId");


-- Table: TalentUpskillingTraining
CREATE TABLE IF NOT EXISTS "TalentUpskillingTraining" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    quarter VARCHAR(2) NOT NULL,
    "skillCode" VARCHAR(50) NOT NULL,
    "trainingName" VARCHAR(255) NOT NULL,
    "completedDate" DATE NOT NULL,
    source VARCHAR(20) NOT NULL DEFAULT 'TALENT_TEAM',
    "uploadedBy" VARCHAR(255) NOT NULL DEFAULT 'Talent Nexus Team',
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255),
    CONSTRAINT fk_talentupskillingtraining_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE,
    CONSTRAINT fk_talentupskillingtraining_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentupskillingtraining_employeemailid_appraisalyearid
ON "TalentUpskillingTraining" ("employeeMailId", "appraisalYearId");


-- Table: TalentFutureSkill
CREATE TABLE IF NOT EXISTS "TalentFutureSkill" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "upskillingPlanId" VARCHAR(255) NOT NULL,
    "skillCode" VARCHAR(50) NOT NULL,
    "targetProficiency" VARCHAR(20) NOT NULL,
    remarks TEXT,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_talentfutureskill_upskillingplanid FOREIGN KEY ("upskillingPlanId") REFERENCES "TalentUpskillingPlan"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentfutureskill_upskillingplanid
ON "TalentFutureSkill" ("upskillingPlanId");


-- Table: TalentLegacyIdea
CREATE TABLE IF NOT EXISTS "TalentLegacyIdea" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    category VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    "ideaType" VARCHAR(20) NOT NULL DEFAULT 'PROJECT_INITIATIVE',
    "spocEmail" VARCHAR(255),
    "stage1Completed" BOOLEAN NOT NULL DEFAULT FALSE,
    "stage1Date" DATE,
    "stage2Completed" BOOLEAN NOT NULL DEFAULT FALSE,
    "stage2Date" DATE,
    "stage3Completed" BOOLEAN NOT NULL DEFAULT FALSE,
    "stage3Date" DATE,
    "efficiencyGainPercent" DECIMAL(5, 2),
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255),
    CONSTRAINT fk_talentlegacyidea_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE,
    CONSTRAINT fk_talentlegacyidea_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentlegacyidea_employeemailid_appraisalyearid
ON "TalentLegacyIdea" ("employeeMailId", "appraisalYearId");


-- Table: TalentLegacyIdeaAttachment
CREATE TABLE IF NOT EXISTS "TalentLegacyIdeaAttachment" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "legacyIdeaId" VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    "blobName" VARCHAR(500) NOT NULL,
    "fileName" VARCHAR(255) NOT NULL,
    "fileSize" INTEGER,
    "mimeType" VARCHAR(100),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    CONSTRAINT fk_talentlegacyideaattachment_legacyideaid FOREIGN KEY ("legacyIdeaId") REFERENCES "TalentLegacyIdea"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_talentlegacyideaattachment_legacyideaid
ON "TalentLegacyIdeaAttachment" ("legacyIdeaId");


-- Table: TalentOption
CREATE TABLE IF NOT EXISTS "TalentOption" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    type VARCHAR(30) NOT NULL,
    label VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    "iconUrl" VARCHAR(500),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255),
    CONSTRAINT uq_talentoption_type_code UNIQUE (type, code)
);

CREATE INDEX IF NOT EXISTS idx_talentoption_type
ON "TalentOption" (type);

