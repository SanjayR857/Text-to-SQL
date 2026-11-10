-- ============================================================================
-- Consolidated Enterprise Text-to-SQL Database Schema
-- Generated from docs/Schema.md
-- Target: PostgreSQL with pgcrypto / pgvector
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- Section: create_vertical_and_role_assignment.sql
-- ============================================================================

-- Enums
CREATE TYPE "Area" AS ENUM (
    'CentralApplication',
    'IndividualModule'
);

CREATE TYPE "Role" AS ENUM (
    'ADMIN',
    'DEV',
    'EP',
    'ES',
    'CHIEF',
    'LEAD',
    'CON'
);

-- Table: Vertical
CREATE TABLE "Vertical" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(5) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    area "Area" NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT TRUE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vertical_area
ON "Vertical" (area);

-- Table: RoleAssignment
CREATE TABLE "RoleAssignment" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    "verticalCode" VARCHAR(5) NOT NULL,
    role "Role" NOT NULL,
    "assignedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "assignedBy" VARCHAR(255) NOT NULL,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_role_assignment_vertical
        FOREIGN KEY ("verticalCode")
        REFERENCES "Vertical"(code),

    CONSTRAINT uq_email_vertical
        UNIQUE (email, "verticalCode")
);

CREATE INDEX idx_role_assignment_email
ON "RoleAssignment" (email);

CREATE INDEX idx_role_assignment_vertical
ON "RoleAssignment" ("verticalCode");



-- ============================================================================
-- Section: create_projects_and_contracts.sql
-- ============================================================================

-- Table: ProjectName
CREATE TABLE "ProjectName" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "projectName" VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    "projectStartDate" DATE,
    "projectEndDate" DATE,
    "billingType" VARCHAR(30),
    "contractType" VARCHAR(20),
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    "ifaSplitBasis" VARCHAR(20),
    "germanyPercentage" DECIMAL(5, 2),
    "contractTeamSize" INTEGER,
    "engagementManagerMail" VARCHAR(255),
    "engagementPartnerMail" VARCHAR(255),
    "teamLeadMail" VARCHAR(255),
    "teamLeadMails" TEXT[] NOT NULL DEFAULT '{}',
    "engagementDirectorMail" VARCHAR(255),
    description TEXT,
    "sharepointLink" VARCHAR(500),
    "pmoMail" VARCHAR(100),
    "isBenchProject" BOOLEAN NOT NULL DEFAULT FALSE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255)
);

-- Table: ProjectDetail
CREATE TABLE "ProjectDetail" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "projectId" VARCHAR(255),
    "resourceMailID" VARCHAR(255),
    "reportingManager" VARCHAR(100),
    "projectJoiningDate" DATE,
    "projectReleaseDate" DATE,
    billability BOOLEAN NOT NULL DEFAULT TRUE,
    "billabilityStartDate" DATE,
    "eLevel" VARCHAR(20),
    "hiringType" VARCHAR(50),
    "ratePerHour" DECIMAL(10, 2),
    "projectLaptopSerialNo" VARCHAR(100),
    "equipmentNumber" VARCHAR(100),
    "rsaTokenDetails" VARCHAR(500),
    "rsaTokenExpiry" DATE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255),
    "indiaRatePerHour" DECIMAL(10, 2),
    "isActive" BOOLEAN NOT NULL DEFAULT TRUE
);

-- Table: ProjectDetailHistory
CREATE TABLE "ProjectDetailHistory" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "eLevel" VARCHAR(20),
    "hiringType" VARCHAR(50),
    billability BOOLEAN,
    "changedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "changedBy" VARCHAR(255),
    "billabilityStartDate" DATE,
    "indiaRatePerHour" DECIMAL(10, 2),
    "projectDetailId" VARCHAR(255) NOT NULL,
    "projectId" VARCHAR(255),
    "ratePerHour" DECIMAL(10, 2),
    "resourceMailID" VARCHAR(255)
);

CREATE INDEX idx_project_detail_history_project_detail_id
ON "ProjectDetailHistory" ("projectDetailId");

-- Table: Milestone
CREATE TABLE "Milestone" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "projectId" VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    amount DECIMAL(18, 2),
    "dueDate" DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255)
);

CREATE INDEX idx_milestone_project_id
ON "Milestone" ("projectId");

-- Table: ContractAmendment
CREATE TABLE "ContractAmendment" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "projectId" VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL,
    amount DECIMAL(18, 2) NOT NULL,
    "effectiveDate" DATE,
    description VARCHAR(500),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255)
);

CREATE INDEX idx_contract_amendment_project_id
ON "ContractAmendment" ("projectId");

-- Table: Contract
CREATE TABLE "Contract" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "projectId" VARCHAR(255),
    "contractName" VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Draft',
    "contractType" VARCHAR(20),
    "startDate" DATE,
    "endDate" DATE,
    value DECIMAL(18, 2),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);



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




-- ============================================================================
-- Schema: create_employee_and_firm.sql
-- Models: EmployeeInformation, FirmContribution
-- ============================================================================

-- Table: EmployeeInformation
CREATE TABLE IF NOT EXISTS "EmployeeInformation" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeName" VARCHAR(150) NOT NULL,
    "employeeMailId" VARCHAR(255) NOT NULL UNIQUE,
    "employeeCode" VARCHAR(20) NOT NULL UNIQUE,
    "mobileNumber" VARCHAR(20),
    "personalEmailId" VARCHAR(255),
    "dateOfBirth" DATE,
    "highestQualification" VARCHAR(100),
    "currentAddress" VARCHAR(500),
    "permanentAddress" VARCHAR(500),
    "currentAddressCity" VARCHAR(100),
    "currentAddressPincode" VARCHAR(20),
    "currentAddressState" VARCHAR(100),
    "landmarkLocation" VARCHAR(255),
    "permanentAddressCity" VARCHAR(100),
    "permanentAddressPincode" VARCHAR(20),
    "permanentAddressState" VARCHAR(100),
    "permanentLandmarkLocation" VARCHAR(255),
    "emergencyContactName" VARCHAR(150),
    "emergencyContactMobile" VARCHAR(20),
    "dateOfJoining" DATE,
    "baseLocation" VARCHAR(100),
    "currentDesignation" VARCHAR(100),
    "careerLevel" VARCHAR(30),
    "employmentType" VARCHAR(50),
    "totalYearsOfExperience" DECIMAL(5, 2),
    "deloitteExperience" DECIMAL(5, 2),
    "previousOrganization" VARCHAR(255),
    "lastPromotedYear" VARCHAR(10),
    "currentReportingManager" VARCHAR(150),
    "reportingPartner" VARCHAR(150),
    "projectUserId" VARCHAR(50),
    "projectEmailId" VARCHAR(255),
    "timesheetChargeCode" VARCHAR(200),
    "deloitteLaptopSerialNo" VARCHAR(100),
    "headsetSerialNo" VARCHAR(100),
    "projectLoginDetails" VARCHAR(50),
    "isActive" BOOLEAN NOT NULL DEFAULT TRUE,
    "deactivatedAt" TIMESTAMP,
    "deactivatedBy" VARCHAR(255),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_employeeinformation_employeemailid
ON "EmployeeInformation" ("employeeMailId");

CREATE INDEX IF NOT EXISTS idx_employeeinformation_employeecode
ON "EmployeeInformation" ("employeeCode");


-- Table: FirmContribution
CREATE TABLE IF NOT EXISTS "FirmContribution" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "activityName" VARCHAR(255) NOT NULL,
    "contributionType" VARCHAR(50),
    "startDate" DATE,
    "endDate" DATE,
    details VARCHAR(255),
    "numberOfHours" DECIMAL(10, 2),
    "numberOfPeople" INTEGER,
    "interviewCandidateName" VARCHAR(255),
    "interviewCandidateSkill" VARCHAR(255),
    "activityLead" VARCHAR(150),
    "activityLeadMail" VARCHAR(255),
    "trainingCoordinatorName" VARCHAR(150),
    "engagementManagerName" VARCHAR(150),
    "engagementManagerMail" VARCHAR(255),
    "resourceMailId" VARCHAR(255),
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdBy" VARCHAR(255),
    "modifiedBy" VARCHAR(255)
);




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




-- ============================================================================
-- Schema: create_office_attendance.sql
-- Models: OfficeAttendanceUpload, OfficeAttendance
-- ============================================================================

-- Table: OfficeAttendanceUpload
CREATE TABLE IF NOT EXISTS "OfficeAttendanceUpload" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "fileName" VARCHAR(255) NOT NULL,
    "uploadedBy" VARCHAR(255) NOT NULL,
    "rowCount" INTEGER NOT NULL,
    "skippedCount" INTEGER NOT NULL DEFAULT 0,
    "dateFrom" DATE NOT NULL,
    "dateTo" DATE NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Table: OfficeAttendance
CREATE TABLE IF NOT EXISTS "OfficeAttendance" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeMailId" VARCHAR(255) NOT NULL,
    "employeeCode" VARCHAR(50),
    "employeeName" VARCHAR(255),
    "visitDate" DATE NOT NULL,
    "firstIn" VARCHAR(20),
    "lastOut" VARCHAR(20),
    "durationMinutes" INTEGER NOT NULL,
    "singleSwipe" BOOLEAN NOT NULL DEFAULT FALSE,
    city VARCHAR(100),
    location VARCHAR(150),
    "uploadId" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_officeattendance_employeemailid_visitdate UNIQUE ("employeeMailId", "visitDate"),
    CONSTRAINT fk_officeattendance_uploadid FOREIGN KEY ("uploadId") REFERENCES "OfficeAttendanceUpload"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_officeattendance_visitdate
ON "OfficeAttendance" ("visitDate");




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




-- ============================================================================
-- Schema: create_xable.sql
-- Models: XableCommunity, XableCommunityMember, XableEvent, XableEventRegistration, XableAnnouncement, XableAnnouncementRead, XablePost, XablePostReport, XableCardToggle, XableGalleryAlbum, XableGalleryMedia, XableSkill, XableProfile, XableProfileSkill, XableSwipe
-- ============================================================================

-- Enums
DO $$ BEGIN
    CREATE TYPE "XableMembershipStatus" AS ENUM (
    'PENDING',
    'MEMBER'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableMemberRole" AS ENUM (
    'MEMBER',
    'MODERATOR',
    'ADMIN'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableAnnouncementCategory" AS ENUM (
    'INFO',
    'ALERT',
    'EVENT',
    'COMMUNITY'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableAnnouncementPriority" AS ENUM (
    'NORMAL',
    'HIGH',
    'URGENT'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XablePostKind" AS ENUM (
    'POST',
    'REQUEST'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XablePostStatus" AS ENUM (
    'VISIBLE',
    'REMOVED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableReportStatus" AS ENUM (
    'OPEN',
    'KEPT',
    'REMOVED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableSkillType" AS ENUM (
    'TEACH',
    'LEARN'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


DO $$ BEGIN
    CREATE TYPE "XableSwipeDirection" AS ENUM (
    'LIKE',
    'PASS'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;


-- Table: XableCommunity
CREATE TABLE IF NOT EXISTS "XableCommunity" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    slug VARCHAR(60) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500) NOT NULL,
    category VARCHAR(30) NOT NULL,
    "iconEmoji" VARCHAR(16),
    "isPublic" BOOLEAN NOT NULL DEFAULT TRUE,
    "isFeatured" BOOLEAN NOT NULL DEFAULT TRUE,
    "allowMemberPosts" BOOLEAN NOT NULL DEFAULT TRUE,
    "bannerBlobName" VARCHAR(500),
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Table: XableCommunityMember
CREATE TABLE IF NOT EXISTS "XableCommunityMember" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "communityId" VARCHAR(255) NOT NULL,
    "employeeId" VARCHAR(255) NOT NULL,
    status "XableMembershipStatus" NOT NULL DEFAULT 'MEMBER',
    role "XableMemberRole" NOT NULL DEFAULT 'MEMBER',
    "requestNote" VARCHAR(300),
    "mutedUntil" TIMESTAMP,
    "isBanned" BOOLEAN NOT NULL DEFAULT FALSE,
    "joinedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "decidedAt" TIMESTAMP,
    "decidedByEmail" VARCHAR(255),
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_xablecommunitymember_communityid_employeeid UNIQUE ("communityId", "employeeId"),
    CONSTRAINT fk_xablecommunitymember_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xablecommunitymember_employeeid FOREIGN KEY ("employeeId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xablecommunitymember_communityid_status
ON "XableCommunityMember" ("communityId", status);

CREATE INDEX IF NOT EXISTS idx_xablecommunitymember_employeeid
ON "XableCommunityMember" ("employeeId");


-- Table: XableEvent
CREATE TABLE IF NOT EXISTS "XableEvent" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "communityId" VARCHAR(255),
    title VARCHAR(150) NOT NULL,
    description VARCHAR(1000),
    "startsAt" TIMESTAMP NOT NULL,
    "endsAt" TIMESTAMP NOT NULL,
    "isOnline" BOOLEAN NOT NULL DEFAULT FALSE,
    venue VARCHAR(255),
    "meetingLink" VARCHAR(500),
    capacity INTEGER,
    "createdByEmail" VARCHAR(255) NOT NULL,
    "cancelledAt" TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_xableevent_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_xableevent_startsat
ON "XableEvent" ("startsAt");

CREATE INDEX IF NOT EXISTS idx_xableevent_communityid
ON "XableEvent" ("communityId");


-- Table: XableEventRegistration
CREATE TABLE IF NOT EXISTS "XableEventRegistration" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "eventId" VARCHAR(255) NOT NULL,
    "employeeId" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_xableeventregistration_eventid_employeeid UNIQUE ("eventId", "employeeId"),
    CONSTRAINT fk_xableeventregistration_eventid FOREIGN KEY ("eventId") REFERENCES "XableEvent"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xableeventregistration_employeeid FOREIGN KEY ("employeeId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xableeventregistration_employeeid
ON "XableEventRegistration" ("employeeId");


-- Table: XableAnnouncement
CREATE TABLE IF NOT EXISTS "XableAnnouncement" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "communityId" VARCHAR(255),
    title VARCHAR(150) NOT NULL,
    content VARCHAR(2000) NOT NULL,
    category "XableAnnouncementCategory" NOT NULL DEFAULT 'COMMUNITY',
    priority "XableAnnouncementPriority" NOT NULL DEFAULT 'NORMAL',
    "publishedByName" VARCHAR(150) NOT NULL,
    "publishedByEmail" VARCHAR(255) NOT NULL,
    "publishedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expiresAt" TIMESTAMP,
    CONSTRAINT fk_xableannouncement_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xableannouncement_publishedat
ON "XableAnnouncement" ("publishedAt");

CREATE INDEX IF NOT EXISTS idx_xableannouncement_communityid
ON "XableAnnouncement" ("communityId");


-- Table: XableAnnouncementRead
CREATE TABLE IF NOT EXISTS "XableAnnouncementRead" (
    "announcementId" VARCHAR(255) NOT NULL,
    "readerEmail" VARCHAR(255) NOT NULL,
    "readAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("announcementId", "readerEmail"),
    CONSTRAINT fk_xableannouncementread_announcementid FOREIGN KEY ("announcementId") REFERENCES "XableAnnouncement"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xableannouncementread_readeremail
ON "XableAnnouncementRead" ("readerEmail");


-- Table: XablePost
CREATE TABLE IF NOT EXISTS "XablePost" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "communityId" VARCHAR(255) NOT NULL,
    card VARCHAR(80) NOT NULL,
    kind "XablePostKind" NOT NULL DEFAULT 'POST',
    "authorId" VARCHAR(255) NOT NULL,
    title VARCHAR(150),
    body VARCHAR(2000),
    "imageBlobName" VARCHAR(500),
    status "XablePostStatus" NOT NULL DEFAULT 'VISIBLE',
    "removedByEmail" VARCHAR(255),
    "removedAt" TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_xablepost_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xablepost_authorid FOREIGN KEY ("authorId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xablepost_communityid_card_createdat
ON "XablePost" ("communityId", card, "createdAt");

CREATE INDEX IF NOT EXISTS idx_xablepost_authorid
ON "XablePost" ("authorId");


-- Table: XablePostReport
CREATE TABLE IF NOT EXISTS "XablePostReport" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "postId" VARCHAR(255) NOT NULL,
    "reporterEmail" VARCHAR(255) NOT NULL,
    reason VARCHAR(300) NOT NULL,
    status "XableReportStatus" NOT NULL DEFAULT 'OPEN',
    "resolvedByEmail" VARCHAR(255),
    "resolvedAt" TIMESTAMP,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_xablepostreport_postid_reporteremail UNIQUE ("postId", "reporterEmail"),
    CONSTRAINT fk_xablepostreport_postid FOREIGN KEY ("postId") REFERENCES "XablePost"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xablepostreport_status
ON "XablePostReport" (status);


-- Table: XableCardToggle
CREATE TABLE IF NOT EXISTS "XableCardToggle" (
    "communityId" VARCHAR(255) NOT NULL,
    card VARCHAR(80) NOT NULL,
    action VARCHAR(60) NOT NULL,
    "employeeId" VARCHAR(255) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("communityId", card, action, "employeeId"),
    CONSTRAINT fk_xablecardtoggle_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xablecardtoggle_employeeid FOREIGN KEY ("employeeId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);


-- Table: XableGalleryAlbum
CREATE TABLE IF NOT EXISTS "XableGalleryAlbum" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    title VARCHAR(150) NOT NULL,
    description VARCHAR(500),
    "communityId" VARCHAR(255),
    "eventId" VARCHAR(255),
    "createdByEmail" VARCHAR(255) NOT NULL,
    "createdByName" VARCHAR(150) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_xablegalleryalbum_communityid FOREIGN KEY ("communityId") REFERENCES "XableCommunity"(id) ON DELETE SET NULL,
    CONSTRAINT fk_xablegalleryalbum_eventid FOREIGN KEY ("eventId") REFERENCES "XableEvent"(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_xablegalleryalbum_createdat
ON "XableGalleryAlbum" ("createdAt");


-- Table: XableGalleryMedia
CREATE TABLE IF NOT EXISTS "XableGalleryMedia" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "albumId" VARCHAR(255) NOT NULL,
    "blobName" VARCHAR(500) NOT NULL,
    "fileName" VARCHAR(255) NOT NULL,
    caption VARCHAR(300),
    "uploadedByEmail" VARCHAR(255) NOT NULL,
    "uploadedByName" VARCHAR(150) NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_xablegallerymedia_albumid FOREIGN KEY ("albumId") REFERENCES "XableGalleryAlbum"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xablegallerymedia_albumid_createdat
ON "XableGalleryMedia" ("albumId", "createdAt");


-- Table: XableSkill
CREATE TABLE IF NOT EXISTS "XableSkill" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(60) NOT NULL UNIQUE,
    category VARCHAR(40) NOT NULL DEFAULT 'Other',
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Table: XableProfile
CREATE TABLE IF NOT EXISTS "XableProfile" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "employeeId" VARCHAR(255) NOT NULL UNIQUE,
    "jobTitle" VARCHAR(100),
    location VARCHAR(100),
    bio VARCHAR(300),
    theme VARCHAR(40),
    "avatarUrl" VARCHAR(500),
    "avatarBlobName" VARCHAR(500),
    "isActive" BOOLEAN NOT NULL DEFAULT TRUE,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_xableprofile_employeeid FOREIGN KEY ("employeeId") REFERENCES "EmployeeInformation"(id) ON DELETE CASCADE
);


-- Table: XableProfileSkill
CREATE TABLE IF NOT EXISTS "XableProfileSkill" (
    "profileId" VARCHAR(255) NOT NULL,
    "skillId" VARCHAR(255) NOT NULL,
    type "XableSkillType" NOT NULL,
    PRIMARY KEY ("profileId", "skillId", type),
    CONSTRAINT fk_xableprofileskill_profileid FOREIGN KEY ("profileId") REFERENCES "XableProfile"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xableprofileskill_skillid FOREIGN KEY ("skillId") REFERENCES "XableSkill"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xableprofileskill_skillid
ON "XableProfileSkill" ("skillId");


-- Table: XableSwipe
CREATE TABLE IF NOT EXISTS "XableSwipe" (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    "swiperId" VARCHAR(255) NOT NULL,
    "targetId" VARCHAR(255) NOT NULL,
    direction "XableSwipeDirection" NOT NULL,
    "createdAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_xableswipe_swiperid_targetid UNIQUE ("swiperId", "targetId"),
    CONSTRAINT fk_xableswipe_swiperid FOREIGN KEY ("swiperId") REFERENCES "XableProfile"(id) ON DELETE CASCADE,
    CONSTRAINT fk_xableswipe_targetid FOREIGN KEY ("targetId") REFERENCES "XableProfile"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_xableswipe_targetid_direction
ON "XableSwipe" ("targetId", direction);



