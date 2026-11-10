-- ============================================================================
-- Schema: create_chief_goals_and_recognition.sql
-- Models: ChiefGoal, EmployeeChiefAreaSelection, ChiefGoalRating, RecognitionPolicy, Recognition, BadgeOfHonorAward, QuarterExclusion
-- ============================================================================

-- Table: ChiefGoal
CREATE TABLE IF NOT EXISTS "ChiefGoal" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "verticalCode" VARCHAR(5) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    weightage DECIMAL(5, 2) NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "isFinalized" BOOLEAN NOT NULL DEFAULT FALSE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255),
    CONSTRAINT fk_chiefgoal_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chiefgoal_verticalcode_appraisalyearid
ON "ChiefGoal" ("verticalCode", "appraisalYearId");


-- Table: EmployeeChiefAreaSelection
CREATE TABLE IF NOT EXISTS "EmployeeChiefAreaSelection" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    "verticalCode" VARCHAR(5) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    "submittedAt" TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_employeechiefareaselection_employeemailid_appraisalyearid_ve UNIQUE ("employeeMailId", "appraisalYearId", "verticalCode"),
    CONSTRAINT fk_employeechiefareaselection_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE,
    CONSTRAINT fk_employeechiefareaselection_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_employeechiefareaselection_employeemailid_appraisalyearid
ON "EmployeeChiefAreaSelection" ("employeeMailId", "appraisalYearId");


-- Table: ChiefGoalRating
CREATE TABLE IF NOT EXISTS "ChiefGoalRating" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "goalId" VARCHAR(255) NOT NULL,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    quarter VARCHAR(2) NOT NULL,
    "starRating" INTEGER NOT NULL,
    "achievementPct" DECIMAL(5, 2) NOT NULL,
    "recalcWeightage" DECIMAL(8, 4) NOT NULL,
    "earnedScore" DECIMAL(8, 4) NOT NULL,
    "cumulativeScore" DECIMAL(8, 4),
    "publishedResults" BOOLEAN NOT NULL DEFAULT FALSE,
    "submittedBy" VARCHAR(255),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_chiefgoalrating_goalid_employeemailid_appraisalyearid_quarte UNIQUE ("goalId", "employeeMailId", "appraisalYearId", quarter),
    CONSTRAINT fk_chiefgoalrating_goalid FOREIGN KEY ("goalId") REFERENCES "ChiefGoal"(id) ON DELETE CASCADE,
    CONSTRAINT fk_chiefgoalrating_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE,
    CONSTRAINT fk_chiefgoalrating_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chiefgoalrating_employeemailid_appraisalyearid
ON "ChiefGoalRating" ("employeeMailId", "appraisalYearId");


-- Table: RecognitionPolicy
CREATE TABLE IF NOT EXISTS "RecognitionPolicy" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "recognitionTeamPercent" DECIMAL(5, 2) NOT NULL DEFAULT 10,
    "maxRecognitionPerChiefPerQuarter" INTEGER NOT NULL DEFAULT 5,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255)
);


-- Table: Recognition
CREATE TABLE IF NOT EXISTS "Recognition" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    quarter VARCHAR(2) NOT NULL,
    description VARCHAR(1000) NOT NULL,
    "bonusPoints" DECIMAL(5, 2) NOT NULL,
    "createdBy" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "projectId" VARCHAR(255),
    CONSTRAINT fk_recognition_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE,
    CONSTRAINT fk_recognition_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE,
    CONSTRAINT fk_recognition_projectid FOREIGN KEY ("projectId") REFERENCES "ProjectName"(id)
);

CREATE INDEX IF NOT EXISTS idx_recognition_employeemailid_appraisalyearid_quarter
ON "Recognition" ("employeeMailId", "appraisalYearId", quarter);

CREATE INDEX IF NOT EXISTS idx_recognition_projectid_appraisalyearid_quarter
ON "Recognition" ("projectId", "appraisalYearId", quarter);


-- Table: BadgeOfHonorAward
CREATE TABLE IF NOT EXISTS "BadgeOfHonorAward" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "badgeCode" VARCHAR(50) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    "conferredBy" VARCHAR(255) NOT NULL,
    "conferredAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note VARCHAR(500),
    "certificatePresented" BOOLEAN NOT NULL DEFAULT FALSE,
    "certificatePresentedAt" DATE,
    "badgePresented" BOOLEAN NOT NULL DEFAULT FALSE,
    "badgePresentedAt" DATE,
    "isCurrent" BOOLEAN NOT NULL DEFAULT TRUE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    CONSTRAINT fk_badgeofhonoraward_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE,
    CONSTRAINT fk_badgeofhonoraward_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_badgeofhonoraward_employeemailid_appraisalyearid
ON "BadgeOfHonorAward" ("employeeMailId", "appraisalYearId");

CREATE INDEX IF NOT EXISTS idx_badgeofhonoraward_employeemailid_iscurrent
ON "BadgeOfHonorAward" ("employeeMailId", "isCurrent");

CREATE INDEX IF NOT EXISTS idx_badgeofhonoraward_conferredat
ON "BadgeOfHonorAward" ("conferredAt");


-- Table: QuarterExclusion
CREATE TABLE IF NOT EXISTS "QuarterExclusion" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    quarter VARCHAR(2) NOT NULL,
    reason VARCHAR(50) NOT NULL,
    note VARCHAR(500),
    "createdBy" VARCHAR(255),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_quarterexclusion_employeemailid_appraisalyearid_quarter UNIQUE ("employeeMailId", "appraisalYearId", quarter),
    CONSTRAINT fk_quarterexclusion_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE,
    CONSTRAINT fk_quarterexclusion_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

