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

