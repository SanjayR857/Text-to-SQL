-- ============================================================================
-- Schema: create_partner_and_em_goals.sql
-- Models: PartnerGoal, PartnerGoalRating, PartnerGoalAcceptance, PartnerGoalMessage, EmGoal, EmGoalRating, EmGoalAcceptance, EmGoalMessage, RatingComment
-- ============================================================================

-- Table: PartnerGoal
CREATE TABLE IF NOT EXISTS "PartnerGoal" (
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
    CONSTRAINT fk_partnergoal_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_partnergoal_verticalcode_appraisalyearid
ON "PartnerGoal" ("verticalCode", "appraisalYearId");


-- Table: PartnerGoalRating
CREATE TABLE IF NOT EXISTS "PartnerGoalRating" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "goalId" VARCHAR(255) NOT NULL,
    "chiefEmail" VARCHAR(255) NOT NULL,
    "verticalCode" VARCHAR(5) NOT NULL,
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
    CONSTRAINT uq_partnergoalrating_goalid_chiefemail_appraisalyearid_quarter UNIQUE ("goalId", "chiefEmail", "appraisalYearId", quarter),
    CONSTRAINT fk_partnergoalrating_goalid FOREIGN KEY ("goalId") REFERENCES "PartnerGoal"(id) ON DELETE CASCADE,
    CONSTRAINT fk_partnergoalrating_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_partnergoalrating_chiefemail_appraisalyearid
ON "PartnerGoalRating" ("chiefEmail", "appraisalYearId");


-- Table: PartnerGoalAcceptance
CREATE TABLE IF NOT EXISTS "PartnerGoalAcceptance" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "verticalCode" VARCHAR(5) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    "acceptedBy" VARCHAR(255) NOT NULL,
    "acceptedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_partnergoalacceptance_verticalcode_appraisalyearid UNIQUE ("verticalCode", "appraisalYearId"),
    CONSTRAINT fk_partnergoalacceptance_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);


-- Table: PartnerGoalMessage
CREATE TABLE IF NOT EXISTS "PartnerGoalMessage" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "verticalCode" VARCHAR(5) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    "goalId" VARCHAR(255),
    quarter VARCHAR(2),
    "senderEmail" VARCHAR(255) NOT NULL,
    "senderRole" VARCHAR(10) NOT NULL,
    body VARCHAR(2000) NOT NULL,
    "isHighlight" BOOLEAN NOT NULL DEFAULT FALSE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_partnergoalmessage_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_partnergoalmessage_verticalcode_appraisalyearid_createdat
ON "PartnerGoalMessage" ("verticalCode", "appraisalYearId", "createdAt");


-- Table: EmGoal
CREATE TABLE IF NOT EXISTS "EmGoal" (
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
    CONSTRAINT fk_emgoal_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_emgoal_verticalcode_appraisalyearid
ON "EmGoal" ("verticalCode", "appraisalYearId");


-- Table: EmGoalRating
CREATE TABLE IF NOT EXISTS "EmGoalRating" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "goalId" VARCHAR(255) NOT NULL,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "verticalCode" VARCHAR(5) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    quarter VARCHAR(2) NOT NULL,
    "starRating" INTEGER NOT NULL,
    "achievementPct" DECIMAL(5, 2) NOT NULL,
    "recalcWeightage" DECIMAL(8, 4) NOT NULL,
    "earnedScore" DECIMAL(8, 4) NOT NULL,
    "publishedResults" BOOLEAN NOT NULL DEFAULT FALSE,
    "submittedBy" VARCHAR(255),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_emgoalrating_goalid_employeemailid_appraisalyearid_quarter UNIQUE ("goalId", "employeeMailId", "appraisalYearId", quarter),
    CONSTRAINT fk_emgoalrating_goalid FOREIGN KEY ("goalId") REFERENCES "EmGoal"(id) ON DELETE CASCADE,
    CONSTRAINT fk_emgoalrating_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_emgoalrating_employeemailid_appraisalyearid
ON "EmGoalRating" ("employeeMailId", "appraisalYearId");


-- Table: EmGoalAcceptance
CREATE TABLE IF NOT EXISTS "EmGoalAcceptance" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "verticalCode" VARCHAR(5) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "acceptedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_emgoalacceptance_verticalcode_appraisalyearid_employeemailid UNIQUE ("verticalCode", "appraisalYearId", "employeeMailId"),
    CONSTRAINT fk_emgoalacceptance_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);


-- Table: EmGoalMessage
CREATE TABLE IF NOT EXISTS "EmGoalMessage" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "verticalCode" VARCHAR(5) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "goalId" VARCHAR(255),
    quarter VARCHAR(2),
    "senderEmail" VARCHAR(255) NOT NULL,
    "senderRole" VARCHAR(10) NOT NULL,
    body VARCHAR(2000) NOT NULL,
    "isHighlight" BOOLEAN NOT NULL DEFAULT FALSE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_emgoalmessage_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_emgoalmessage_verticalcode_appraisalyearid_employeemailid_c
ON "EmGoalMessage" ("verticalCode", "appraisalYearId", "employeeMailId", "createdAt");


-- Table: RatingComment
CREATE TABLE IF NOT EXISTS "RatingComment" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    module VARCHAR(15) NOT NULL,
    "rateeEmail" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    quarter VARCHAR(2) NOT NULL,
    "contextKey" VARCHAR(255) NOT NULL,
    comment VARCHAR(2000) NOT NULL,
    "createdBy" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_ratingcomment_module_rateeemail_appraisalyearid_quarter_cont UNIQUE (module, "rateeEmail", "appraisalYearId", quarter, "contextKey"),
    CONSTRAINT fk_ratingcomment_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ratingcomment_appraisalyearid_quarter
ON "RatingComment" ("appraisalYearId", quarter);

