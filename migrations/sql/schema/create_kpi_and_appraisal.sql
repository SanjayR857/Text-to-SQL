-- ============================================================================
-- Schema: create_kpi_and_appraisal.sql
-- Models: KpiRole, AppraisalYear, QuarterlyRatingWindow, KpiGoal, KpiGoalRole, EmployeeGoalAssignment, QuarterlyRating, LevelWeightagePolicy
-- ============================================================================

-- Table: KpiRole
CREATE TABLE IF NOT EXISTS "KpiRole" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    label VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(50) NOT NULL UNIQUE,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255)
);


-- Table: AppraisalYear
CREATE TABLE IF NOT EXISTS "AppraisalYear" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "yearLabel" VARCHAR(20) NOT NULL UNIQUE,
    "startDate" TIMESTAMP NOT NULL,
    "endDate" TIMESTAMP NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT FALSE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255)
);


-- Table: QuarterlyRatingWindow
CREATE TABLE IF NOT EXISTS "QuarterlyRatingWindow" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    module VARCHAR(50) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    quarter VARCHAR(2) NOT NULL,
    "windowStartDate" TIMESTAMP NOT NULL,
    "windowEndDate" TIMESTAMP NOT NULL,
    "isPublished" BOOLEAN NOT NULL DEFAULT FALSE,
    "publishedAt" TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "modifiedBy" VARCHAR(255),
    CONSTRAINT uq_quarterlyratingwindow_module_appraisalyearid_quarter UNIQUE (module, "appraisalYearId", quarter),
    CONSTRAINT fk_quarterlyratingwindow_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);


-- Table: KpiGoal
CREATE TABLE IF NOT EXISTS "KpiGoal" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "projectId" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    weightage DECIMAL(5, 2) NOT NULL,
    "ownerType" VARCHAR(20) NOT NULL DEFAULT 'CHIEF_DELIVERY',
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "isFinalized" BOOLEAN NOT NULL DEFAULT FALSE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255),
    CONSTRAINT fk_kpigoal_projectid FOREIGN KEY ("projectId") REFERENCES "ProjectName"(id) ON DELETE CASCADE,
    CONSTRAINT fk_kpigoal_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_kpigoal_projectid_appraisalyearid
ON "KpiGoal" ("projectId", "appraisalYearId");


-- Table: KpiGoalRole
CREATE TABLE IF NOT EXISTS "KpiGoalRole" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "goalId" VARCHAR(255) NOT NULL,
    "roleId" VARCHAR(255) NOT NULL,
    CONSTRAINT uq_kpigoalrole_goalid_roleid UNIQUE ("goalId", "roleId"),
    CONSTRAINT fk_kpigoalrole_goalid FOREIGN KEY ("goalId") REFERENCES "KpiGoal"(id) ON DELETE CASCADE,
    CONSTRAINT fk_kpigoalrole_roleid FOREIGN KEY ("roleId") REFERENCES "KpiRole"(id) ON DELETE CASCADE
);


-- Table: EmployeeGoalAssignment
CREATE TABLE IF NOT EXISTS "EmployeeGoalAssignment" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "projectId" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    "selectedRoleId" VARCHAR(255) NOT NULL,
    "totalProjects" INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    "submittedAt" TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_employeegoalassignment_employeemailid_projectid_appraisalyea UNIQUE ("employeeMailId", "projectId", "appraisalYearId"),
    CONSTRAINT fk_employeegoalassignment_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE,
    CONSTRAINT fk_employeegoalassignment_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE,
    CONSTRAINT fk_employeegoalassignment_projectid FOREIGN KEY ("projectId") REFERENCES "ProjectName"(id) ON DELETE CASCADE,
    CONSTRAINT fk_employeegoalassignment_selectedroleid FOREIGN KEY ("selectedRoleId") REFERENCES "KpiRole"(id)
);

CREATE INDEX IF NOT EXISTS idx_employeegoalassignment_employeemailid_appraisalyearid
ON "EmployeeGoalAssignment" ("employeeMailId", "appraisalYearId");


-- Table: QuarterlyRating
CREATE TABLE IF NOT EXISTS "QuarterlyRating" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "goalId" VARCHAR(255) NOT NULL,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "projectId" VARCHAR(255) NOT NULL,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    quarter VARCHAR(2) NOT NULL,
    "starRating" INTEGER NOT NULL,
    "achievementPct" DECIMAL(5, 2) NOT NULL,
    "earnedScore" DECIMAL(8, 4) NOT NULL,
    "recalcWeightage" DECIMAL(8, 4) NOT NULL,
    "cumulativeScore" DECIMAL(8, 4),
    "publishedResults" BOOLEAN NOT NULL DEFAULT FALSE,
    "submittedBy" VARCHAR(255),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_quarterlyrating_goalid_employeemailid_appraisalyearid_quarte UNIQUE ("goalId", "employeeMailId", "appraisalYearId", quarter),
    CONSTRAINT fk_quarterlyrating_goalid FOREIGN KEY ("goalId") REFERENCES "KpiGoal"(id) ON DELETE CASCADE,
    CONSTRAINT fk_quarterlyrating_employeemailid FOREIGN KEY ("employeeMailId") REFERENCES "EmployeeInformation"("employeeMailId") ON DELETE CASCADE,
    CONSTRAINT fk_quarterlyrating_projectid FOREIGN KEY ("projectId") REFERENCES "ProjectName"(id) ON DELETE CASCADE,
    CONSTRAINT fk_quarterlyrating_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_quarterlyrating_employeemailid_appraisalyearid
ON "QuarterlyRating" ("employeeMailId", "appraisalYearId");

CREATE INDEX IF NOT EXISTS idx_quarterlyrating_projectid_appraisalyearid_quarter
ON "QuarterlyRating" ("projectId", "appraisalYearId", quarter);


-- Table: LevelWeightagePolicy
CREATE TABLE IF NOT EXISTS "LevelWeightagePolicy" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "appraisalYearId" VARCHAR(255) NOT NULL,
    "careerLevel" VARCHAR(30) NOT NULL,
    "deliveryPct" DECIMAL(5, 2) NOT NULL,
    "deliveryChiefPct" DECIMAL(5, 2) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "modifiedBy" VARCHAR(255),
    CONSTRAINT uq_levelweightagepolicy_appraisalyearid_careerlevel UNIQUE ("appraisalYearId", "careerLevel"),
    CONSTRAINT fk_levelweightagepolicy_appraisalyearid FOREIGN KEY ("appraisalYearId") REFERENCES "AppraisalYear"(id) ON DELETE CASCADE
);

