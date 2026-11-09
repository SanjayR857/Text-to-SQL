-- Insert Seed Data for Projects, ProjectDetails, Milestones, and Contracts

-- 1. ProjectName
INSERT INTO "ProjectName" (
    id, "projectName", status, "projectStartDate", "projectEndDate", "billingType",
    "contractType", currency, "ifaSplitBasis", "germanyPercentage", "contractTeamSize",
    "engagementManagerMail", "engagementPartnerMail", "teamLeadMails", "engagementDirectorMail",
    description, "sharepointLink", "pmoMail", "isBenchProject", "createdBy", "modifiedBy"
) VALUES
(
    'proj_alpha_ai_001', 'Alpha Enterprise AI Platform', 'Active', '2026-01-15', '2026-12-31', 'TimeAndMaterial',
    'FixedFee', 'USD', 'Revenue', 30.00, 8,
    'manager.delivery@enterprise.ai', 'partner.lead@enterprise.ai', ARRAY['tech.lead1@enterprise.ai', 'tech.lead2@enterprise.ai'], 'director.eng@enterprise.ai',
    'Enterprise-grade generative AI and Text-to-SQL data platform', 'https://sharepoint.enterprise.ai/sites/alpha-ai', 'pmo.delivery@enterprise.ai', FALSE, 'admin@enterprise.ai', 'admin@enterprise.ai'
),
(
    'proj_cloud_mod_002', 'Cloud Infrastructure Modernization', 'Active', '2026-03-01', '2026-10-31', 'FixedPrice',
    'IFA', 'EUR', 'Profit', 50.00, 12,
    'manager.cloud@enterprise.ai', 'partner.lead@enterprise.ai', ARRAY['cloud.architect@enterprise.ai'], 'director.eng@enterprise.ai',
    'Azure flexible server migration, containerization, and networking overhaul', 'https://sharepoint.enterprise.ai/sites/cloud-mod', 'pmo.delivery@enterprise.ai', FALSE, 'admin@enterprise.ai', 'admin@enterprise.ai'
),
(
    'proj_bench_sentinel_003', 'Delivery Bench & Readiness Pool', 'Active', '2026-01-01', NULL, 'NonBillable',
    'Internal', 'USD', NULL, NULL, 0,
    'manager.talent@enterprise.ai', 'partner.lead@enterprise.ai', ARRAY['bench.coordinator@enterprise.ai'], 'director.talent@enterprise.ai',
    'Sentinel project for unstaffed delivery talent tracking and readiness KPIs', NULL, 'pmo.delivery@enterprise.ai', TRUE, 'admin@enterprise.ai', 'admin@enterprise.ai'
)
ON CONFLICT (id) DO UPDATE
SET "projectName" = EXCLUDED."projectName",
    status = EXCLUDED.status,
    "teamLeadMails" = EXCLUDED."teamLeadMails",
    "updatedAt" = CURRENT_TIMESTAMP;

-- 2. ProjectDetail (Fully synchronized with RoleAssignment personnel)
INSERT INTO "ProjectDetail" (
    id, "projectId", "resourceMailID", "reportingManager", "projectJoiningDate",
    "projectReleaseDate", billability, "billabilityStartDate", "eLevel", "hiringType",
    "ratePerHour", "projectLaptopSerialNo", "equipmentNumber", "rsaTokenDetails",
    "rsaTokenExpiry", "createdBy", "modifiedBy", "indiaRatePerHour", "isActive"
) VALUES
-- Alpha Enterprise AI Platform Staffing
(
    'det_001_lead', 'proj_alpha_ai_001', 'tech.lead1@enterprise.ai', 'manager.delivery@enterprise.ai', '2026-01-15',
    NULL, TRUE, '2026-01-15', 'E4', 'Permanent',
    120.00, 'LP-AZ-9921', 'EQ-8812', 'RSA-SW-88219', '2027-01-15', 'admin@enterprise.ai', 'admin@enterprise.ai', 45.00, TRUE
),
(
    'det_002_dev', 'proj_alpha_ai_001', 'dev.engineer@enterprise.ai', 'tech.lead1@enterprise.ai', '2026-02-01',
    NULL, TRUE, '2026-02-01', 'E2', 'Permanent',
    85.00, 'LP-AZ-7743', 'EQ-5521', 'RSA-SW-77112', '2027-02-01', 'admin@enterprise.ai', 'admin@enterprise.ai', 30.00, TRUE
),
(
    'det_003_ailead', 'proj_alpha_ai_001', 'ai.lead@enterprise.ai', 'manager.delivery@enterprise.ai', '2026-01-20',
    NULL, TRUE, '2026-01-20', 'E4', 'Permanent',
    125.00, 'LP-AZ-8810', 'EQ-6620', 'RSA-SW-88120', '2027-01-20', 'admin@enterprise.ai', 'admin@enterprise.ai', 48.00, TRUE
),
(
    'det_004_aicon', 'proj_alpha_ai_001', 'ai.consultant@enterprise.ai', 'ai.lead@enterprise.ai', '2026-02-15',
    NULL, TRUE, '2026-02-15', 'E3', 'Permanent',
    95.00, 'LP-AZ-6612', 'EQ-4419', 'RSA-SW-66190', '2027-02-15', 'admin@enterprise.ai', 'admin@enterprise.ai', 35.00, TRUE
),
-- Cloud Infrastructure Modernization Staffing
(
    'det_005_cloud', 'proj_cloud_mod_002', 'cloud.architect@enterprise.ai', 'manager.cloud@enterprise.ai', '2026-03-01',
    NULL, TRUE, '2026-03-01', 'E5', 'Contract',
    150.00, 'LP-AZ-4412', 'EQ-9910', 'RSA-SW-44100', '2026-11-01', 'admin@enterprise.ai', 'admin@enterprise.ai', 60.00, TRUE
),
(
    'det_006_teches', 'proj_cloud_mod_002', 'tech.es@enterprise.ai', 'cloud.architect@enterprise.ai', '2026-03-15',
    NULL, TRUE, '2026-03-15', 'E4', 'Permanent',
    115.00, 'LP-AZ-3321', 'EQ-7714', 'RSA-SW-33210', '2027-03-15', 'admin@enterprise.ai', 'admin@enterprise.ai', 42.00, TRUE
),
(
    'det_007_delivlead', 'proj_cloud_mod_002', 'delivery.lead@enterprise.ai', 'manager.cloud@enterprise.ai', '2026-03-01',
    NULL, TRUE, '2026-03-01', 'E4', 'Permanent',
    120.00, 'LP-AZ-2210', 'EQ-8819', 'RSA-SW-22190', '2027-03-01', 'admin@enterprise.ai', 'admin@enterprise.ai', 44.00, TRUE
)
ON CONFLICT (id) DO UPDATE
SET "resourceMailID" = EXCLUDED."resourceMailID",
    "reportingManager" = EXCLUDED."reportingManager",
    "ratePerHour" = EXCLUDED."ratePerHour",
    "updatedAt" = CURRENT_TIMESTAMP;

-- 3. ProjectDetailHistory
INSERT INTO "ProjectDetailHistory" (
    id, "eLevel", "hiringType", billability, "changedAt", "changedBy",
    "billabilityStartDate", "indiaRatePerHour", "projectDetailId", "projectId",
    "ratePerHour", "resourceMailID"
) VALUES
(
    'hist_001_rate_change', 'E2', 'Permanent', TRUE, '2026-03-01 10:00:00', 'admin@enterprise.ai',
    '2026-02-01', 30.00, 'det_002_dev', 'proj_alpha_ai_001',
    85.00, 'dev.engineer@enterprise.ai'
)
ON CONFLICT (id) DO NOTHING;

-- 4. Milestone
INSERT INTO "Milestone" (
    id, "projectId", name, amount, "dueDate", status, "createdBy", "modifiedBy"
) VALUES
(
    'mile_001_alpha_arch', 'proj_alpha_ai_001', 'Architecture & DDL Baseline Sign-Off', 45000.00, '2026-03-15', 'Completed', 'admin@enterprise.ai', 'admin@enterprise.ai'
),
(
    'mile_002_alpha_stream', 'proj_alpha_ai_001', 'Streaming Orchestrator & SSE Engine', 65000.00, '2026-05-30', 'Pending', 'admin@enterprise.ai', 'admin@enterprise.ai'
),
(
    'mile_003_cloud_infra', 'proj_cloud_mod_002', 'Core VPC & Managed DB Cluster Deployment', 80000.00, '2026-06-30', 'Pending', 'admin@enterprise.ai', 'admin@enterprise.ai'
)
ON CONFLICT (id) DO NOTHING;

-- 5. ContractAmendment
INSERT INTO "ContractAmendment" (
    id, "projectId", type, amount, "effectiveDate", description, "createdBy", "modifiedBy"
) VALUES
(
    'amend_001_scope', 'proj_alpha_ai_001', 'ScopeExtension', 25000.00, '2026-04-01', 'Addition of multi-tenant row-level access control module', 'admin@enterprise.ai', 'admin@enterprise.ai'
)
ON CONFLICT (id) DO NOTHING;

-- 6. Contract
INSERT INTO "Contract" (
    id, "projectId", "contractName", status, "contractType", "startDate", "endDate", value
) VALUES
(
    'cntr_001_alpha_master', 'proj_alpha_ai_001', 'MSA - Enterprise Generative AI Implementation', 'Active', 'MasterService', '2026-01-15', '2026-12-31', 350000.00
),
(
    'cntr_002_cloud_sow', 'proj_cloud_mod_002', 'SOW-01 - Cloud Infrastructure & Migration', 'Active', 'StatementOfWork', '2026-03-01', '2026-10-31', 200000.00
)
ON CONFLICT (id) DO NOTHING;
