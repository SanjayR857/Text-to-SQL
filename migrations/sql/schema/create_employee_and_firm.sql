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

