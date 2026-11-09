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
