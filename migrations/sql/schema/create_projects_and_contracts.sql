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
