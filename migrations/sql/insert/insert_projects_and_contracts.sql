-- Insert Seed Data for Real Projects, Project Details, Milestones, and Contracts
-- Fully synchronized with Real Gmail personnel and role assignments

-- 1. ProjectName
INSERT INTO "ProjectName" (
    id, "projectName", status, "projectStartDate", "projectEndDate", "billingType",
    "contractType", currency, "ifaSplitBasis", "germanyPercentage", "contractTeamSize",
    "engagementManagerMail", "engagementPartnerMail", "teamLeadMail", "teamLeadMails",
    "engagementDirectorMail", description, "sharepointLink", "pmoMail", "isBenchProject",
    "createdBy", "modifiedBy"
) VALUES
(
    'proj_alpha_ai_001',
    'Alpha Enterprise AI & Text-to-SQL Platform',
    'Active',
    '2026-01-15',
    '2026-12-31',
    'TimeAndMaterial',
    'FixedFee',
    'USD',
    'Revenue',
    25.00,
    10,
    'david.k.delivery@gmail.com',
    'jordan.hayes.ep@gmail.com',
    'sanjayr9586@gmail.com',
    ARRAY['sanjayr9586@gmail.com', 'vikram.malhotra.lead@gmail.com'],
    'marcus.vance.cdo@gmail.com',
    'Enterprise-grade generative AI and Text-to-SQL data platform featuring autonomous agentic orchestration, streaming telemetry, and strict RBAC data governance.',
    'https://workspace.enterprise.ai/sites/alpha-ai-platform',
    'pmo.delivery.office@gmail.com',
    FALSE,
    'sanjayr9586@gmail.com',
    'sanjayr9586@gmail.com'
),
(
    'proj_fintech_copilot_002',
    'FinTech Wealth Advisory & SQL Copilot',
    'Active',
    '2026-02-01',
    '2026-11-30',
    'FixedPrice',
    'FixedFee',
    'USD',
    'Profit',
    35.00,
    8,
    'david.k.delivery@gmail.com',
    'elizabeth.taylor.ep@gmail.com',
    'sanjayr9586@gmail.com',
    ARRAY['sanjayr9586@gmail.com', 'marcus.vance.ai@gmail.com'],
    'marcus.vance.cdo@gmail.com',
    'Autonomous financial risk intelligence agent querying transactional data warehouses using natural language and strict row-level security.',
    'https://workspace.enterprise.ai/sites/fintech-copilot',
    'pmo.delivery.office@gmail.com',
    FALSE,
    'sanjayr9586@gmail.com',
    'sanjayr9586@gmail.com'
),
(
    'proj_cloud_mod_003',
    'Cloud Infrastructure Modernization & Zero-Trust Mesh',
    'Active',
    '2026-03-01',
    '2026-10-31',
    'FixedPrice',
    'IFA',
    'EUR',
    'Profit',
    50.00,
    12,
    'kevin.t.cloudmgr@gmail.com',
    'jordan.hayes.ep@gmail.com',
    'nathan.cross.arch@gmail.com',
    ARRAY['nathan.cross.arch@gmail.com', 'emily.watson.lead@gmail.com'],
    'robert.chen.cto@gmail.com',
    'Azure flexible server migration, multi-region Kubernetes microservices, containerization, and zero-trust service mesh overhaul.',
    'https://workspace.enterprise.ai/sites/cloud-modernization',
    'pmo.delivery.office@gmail.com',
    FALSE,
    'sanjayr9586@gmail.com',
    'sanjayr9586@gmail.com'
),
(
    'proj_health_omnichannel_004',
    'Healthcare Clinical Assistant & Patient Intelligence Hub',
    'Active',
    '2026-04-01',
    '2027-03-31',
    'TimeAndMaterial',
    'FixedFee',
    'USD',
    'Revenue',
    20.00,
    14,
    'david.k.delivery@gmail.com',
    'elizabeth.taylor.ep@gmail.com',
    'vikram.malhotra.lead@gmail.com',
    ARRAY['vikram.malhotra.lead@gmail.com', 'carlos.mendez.lead@gmail.com'],
    'marcus.vance.cdo@gmail.com',
    'HIPAA-compliant conversational AI and medical record search for physician diagnostic decision support and clinical trial matching.',
    'https://workspace.enterprise.ai/sites/health-intelligence',
    'pmo.delivery.office@gmail.com',
    FALSE,
    'sanjayr9586@gmail.com',
    'sanjayr9586@gmail.com'
),
(
    'proj_supply_chain_005',
    'Global Supply Chain Real-Time Analytics & Inventory Copilot',
    'Active',
    '2026-05-15',
    '2027-01-31',
    'TimeAndMaterial',
    'StatementOfWork',
    'USD',
    'Revenue',
    0.00,
    7,
    'david.k.delivery@gmail.com',
    'jordan.hayes.ep@gmail.com',
    'sanjayr9586@gmail.com',
    ARRAY['sanjayr9586@gmail.com', 'carlos.mendez.lead@gmail.com'],
    'marcus.vance.cdo@gmail.com',
    'Natural language SQL assistant querying SAP and PostgreSQL ERP data to identify supply shortages and route bottlenecks in real time.',
    'https://workspace.enterprise.ai/sites/supply-chain-analytics',
    'pmo.delivery.office@gmail.com',
    FALSE,
    'sanjayr9586@gmail.com',
    'sanjayr9586@gmail.com'
),
(
    'proj_bench_sentinel_006',
    'Delivery Bench & Talent Readiness Sentinel Pool',
    'Active',
    '2026-01-01',
    NULL,
    'NonBillable',
    'Internal',
    'USD',
    NULL,
    NULL,
    0,
    'brian.foster.talent@gmail.com',
    'jordan.hayes.ep@gmail.com',
    'chloe.zheng.bench@gmail.com',
    ARRAY['chloe.zheng.bench@gmail.com'],
    'laura.bennett.talent@gmail.com',
    'Sentinel operational pool tracking unassigned engineering consultants, readiness certifications, and internal AI platform upskilling.',
    NULL,
    'pmo.delivery.office@gmail.com',
    TRUE,
    'sanjayr9586@gmail.com',
    'sanjayr9586@gmail.com'
)
ON CONFLICT (id) DO UPDATE
SET "projectName" = EXCLUDED."projectName",
    status = EXCLUDED.status,
    "projectStartDate" = EXCLUDED."projectStartDate",
    "projectEndDate" = EXCLUDED."projectEndDate",
    "billingType" = EXCLUDED."billingType",
    "contractType" = EXCLUDED."contractType",
    currency = EXCLUDED.currency,
    "ifaSplitBasis" = EXCLUDED."ifaSplitBasis",
    "germanyPercentage" = EXCLUDED."germanyPercentage",
    "contractTeamSize" = EXCLUDED."contractTeamSize",
    "engagementManagerMail" = EXCLUDED."engagementManagerMail",
    "engagementPartnerMail" = EXCLUDED."engagementPartnerMail",
    "teamLeadMail" = EXCLUDED."teamLeadMail",
    "teamLeadMails" = EXCLUDED."teamLeadMails",
    "engagementDirectorMail" = EXCLUDED."engagementDirectorMail",
    description = EXCLUDED.description,
    "sharepointLink" = EXCLUDED."sharepointLink",
    "pmoMail" = EXCLUDED."pmoMail",
    "isBenchProject" = EXCLUDED."isBenchProject",
    "updatedAt" = CURRENT_TIMESTAMP;

-- 2. ProjectDetail (Resource staffing with verified Gmail accounts and real billable rates)
INSERT INTO "ProjectDetail" (
    id, "projectId", "resourceMailID", "reportingManager", "projectJoiningDate",
    "projectReleaseDate", billability, "billabilityStartDate", "eLevel", "hiringType",
    "ratePerHour", "projectLaptopSerialNo", "equipmentNumber", "rsaTokenDetails",
    "rsaTokenExpiry", "createdBy", "modifiedBy", "indiaRatePerHour", "isActive"
) VALUES
-- Alpha Enterprise AI Platform Staffing
(
    'det_001_sanjay_lead', 'proj_alpha_ai_001', 'sanjayr9586@gmail.com', 'david.k.delivery@gmail.com', '2026-01-15',
    NULL, TRUE, '2026-01-15', 'E5', 'Permanent',
    150.00, 'LP-AZ-9921', 'EQ-8812', 'RSA-SW-88219', '2027-01-15', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 55.00, TRUE
),
(
    'det_002_alex_dev', 'proj_alpha_ai_001', 'alex.chen.eng@gmail.com', 'sanjayr9586@gmail.com', '2026-02-01',
    NULL, TRUE, '2026-02-01', 'E3', 'Permanent',
    95.00, 'LP-AZ-7743', 'EQ-5521', 'RSA-SW-77112', '2027-02-01', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 35.00, TRUE
),
(
    'det_003_priya_ui', 'proj_alpha_ai_001', 'priya.sharma.lead@gmail.com', 'sanjayr9586@gmail.com', '2026-01-20',
    NULL, TRUE, '2026-01-20', 'E3', 'Permanent',
    90.00, 'LP-AZ-6622', 'EQ-4418', 'RSA-SW-66220', '2027-01-20', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 32.00, TRUE
),
(
    'det_004_ananya_ml', 'proj_alpha_ai_001', 'ananya.patel.ml@gmail.com', 'sanjayr9586@gmail.com', '2026-02-10',
    NULL, TRUE, '2026-02-10', 'E4', 'Permanent',
    115.00, 'LP-AZ-8810', 'EQ-6620', 'RSA-SW-88120', '2027-02-10', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 42.00, TRUE
),
(
    'det_005_daniel_sql', 'proj_alpha_ai_001', 'daniel.kim.data@gmail.com', 'vikram.malhotra.lead@gmail.com', '2026-02-15',
    NULL, TRUE, '2026-02-15', 'E2', 'Permanent',
    80.00, 'LP-AZ-5511', 'EQ-3319', 'RSA-SW-55110', '2027-02-15', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 28.00, TRUE
),

-- FinTech Wealth Advisory & SQL Copilot Staffing
(
    'det_006_sanjay_fintech', 'proj_fintech_copilot_002', 'sanjayr9586@gmail.com', 'david.k.delivery@gmail.com', '2026-02-01',
    NULL, TRUE, '2026-02-01', 'E5', 'Permanent',
    160.00, 'LP-AZ-9921', 'EQ-8812', 'RSA-SW-88219', '2027-01-15', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 60.00, TRUE
),
(
    'det_007_marcus_quant', 'proj_fintech_copilot_002', 'marcus.vance.ai@gmail.com', 'david.k.delivery@gmail.com', '2026-02-01',
    NULL, TRUE, '2026-02-01', 'E4', 'Permanent',
    135.00, 'LP-AZ-4490', 'EQ-2201', 'RSA-SW-44901', '2027-02-01', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 50.00, TRUE
),
(
    'det_008_tanya_sec', 'proj_fintech_copilot_002', 'tanya.petrov.tech@gmail.com', 'marcus.vance.ai@gmail.com', '2026-02-15',
    NULL, TRUE, '2026-02-15', 'E4', 'Contract',
    120.00, 'LP-AZ-3310', 'EQ-1190', 'RSA-SW-33102', '2026-12-15', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 45.00, TRUE
),

-- Cloud Infrastructure Modernization Staffing
(
    'det_009_nathan_arch', 'proj_cloud_mod_003', 'nathan.cross.arch@gmail.com', 'kevin.t.cloudmgr@gmail.com', '2026-03-01',
    NULL, TRUE, '2026-03-01', 'E5', 'Contract',
    155.00, 'LP-AZ-4412', 'EQ-9910', 'RSA-SW-44100', '2026-11-01', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 58.00, TRUE
),
(
    'det_010_emily_devops', 'proj_cloud_mod_003', 'emily.watson.lead@gmail.com', 'kevin.t.cloudmgr@gmail.com', '2026-03-01',
    NULL, TRUE, '2026-03-01', 'E4', 'Permanent',
    125.00, 'LP-AZ-2210', 'EQ-8819', 'RSA-SW-22190', '2027-03-01', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 46.00, TRUE
),
(
    'det_011_tanya_k8s', 'proj_cloud_mod_003', 'tanya.petrov.tech@gmail.com', 'nathan.cross.arch@gmail.com', '2026-03-15',
    NULL, TRUE, '2026-03-15', 'E4', 'Permanent',
    115.00, 'LP-AZ-3321', 'EQ-7714', 'RSA-SW-33210', '2027-03-15', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 42.00, TRUE
),

-- Healthcare Clinical Assistant Staffing
(
    'det_012_vikram_health', 'proj_health_omnichannel_004', 'vikram.malhotra.lead@gmail.com', 'david.k.delivery@gmail.com', '2026-04-01',
    NULL, TRUE, '2026-04-01', 'E4', 'Permanent',
    135.00, 'LP-AZ-5588', 'EQ-6677', 'RSA-SW-55881', '2027-04-01', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 48.00, TRUE
),
(
    'det_013_carlos_hipaa', 'proj_health_omnichannel_004', 'carlos.mendez.lead@gmail.com', 'david.k.delivery@gmail.com', '2026-04-01',
    NULL, TRUE, '2026-04-01', 'E4', 'Permanent',
    125.00, 'LP-AZ-6699', 'EQ-7788', 'RSA-SW-66992', '2027-04-01', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 45.00, TRUE
),
(
    'det_014_ananya_clinical', 'proj_health_omnichannel_004', 'ananya.patel.ml@gmail.com', 'vikram.malhotra.lead@gmail.com', '2026-04-15',
    NULL, TRUE, '2026-04-15', 'E4', 'Permanent',
    115.00, 'LP-AZ-8810', 'EQ-6620', 'RSA-SW-88120', '2027-02-10', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 42.00, TRUE
),

-- Supply Chain Real-Time Analytics Staffing
(
    'det_015_sanjay_sc', 'proj_supply_chain_005', 'sanjayr9586@gmail.com', 'david.k.delivery@gmail.com', '2026-05-15',
    NULL, TRUE, '2026-05-15', 'E5', 'Permanent',
    155.00, 'LP-AZ-9921', 'EQ-8812', 'RSA-SW-88219', '2027-01-15', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 56.00, TRUE
),
(
    'det_016_carlos_sc', 'proj_supply_chain_005', 'carlos.mendez.lead@gmail.com', 'sanjayr9586@gmail.com', '2026-05-15',
    NULL, TRUE, '2026-05-15', 'E4', 'Permanent',
    120.00, 'LP-AZ-6699', 'EQ-7788', 'RSA-SW-66992', '2027-04-01', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 44.00, TRUE
),

-- Delivery Bench & Sentinel Staffing
(
    'det_017_chloe_bench', 'proj_bench_sentinel_006', 'chloe.zheng.bench@gmail.com', 'brian.foster.talent@gmail.com', '2026-01-01',
    NULL, FALSE, '2026-01-01', 'E3', 'Permanent',
    0.00, 'LP-AZ-1122', 'EQ-3344', 'RSA-SW-11223', '2027-01-01', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com', 0.00, TRUE
)
ON CONFLICT (id) DO UPDATE
SET "projectId" = EXCLUDED."projectId",
    "resourceMailID" = EXCLUDED."resourceMailID",
    "reportingManager" = EXCLUDED."reportingManager",
    "projectJoiningDate" = EXCLUDED."projectJoiningDate",
    "projectReleaseDate" = EXCLUDED."projectReleaseDate",
    billability = EXCLUDED.billability,
    "billabilityStartDate" = EXCLUDED."billabilityStartDate",
    "eLevel" = EXCLUDED."eLevel",
    "hiringType" = EXCLUDED."hiringType",
    "ratePerHour" = EXCLUDED."ratePerHour",
    "indiaRatePerHour" = EXCLUDED."indiaRatePerHour",
    "isActive" = EXCLUDED."isActive",
    "updatedAt" = CURRENT_TIMESTAMP;

-- 3. ProjectDetailHistory (Audit trail of merit rate adjustments and promotions)
INSERT INTO "ProjectDetailHistory" (
    id, "eLevel", "hiringType", billability, "changedAt", "changedBy",
    "billabilityStartDate", "indiaRatePerHour", "projectDetailId", "projectId",
    "ratePerHour", "resourceMailID"
) VALUES
(
    'hist_001_sanjay_lead_bump', 'E5', 'Permanent', TRUE, '2026-02-01 09:00:00', 'sanjayr9586@gmail.com',
    '2026-01-15', 55.00, 'det_001_sanjay_lead', 'proj_alpha_ai_001',
    150.00, 'sanjayr9586@gmail.com'
),
(
    'hist_002_alex_merit_increase', 'E3', 'Permanent', TRUE, '2026-03-01 10:30:00', 'sanjayr9586@gmail.com',
    '2026-02-01', 35.00, 'det_002_alex_dev', 'proj_alpha_ai_001',
    95.00, 'alex.chen.eng@gmail.com'
),
(
    'hist_003_ananya_rate_adjustment', 'E4', 'Permanent', TRUE, '2026-03-15 14:00:00', 'sanjayr9586@gmail.com',
    '2026-02-10', 42.00, 'det_004_ananya_ml', 'proj_alpha_ai_001',
    115.00, 'ananya.patel.ml@gmail.com'
),
(
    'hist_004_nathan_contract_renew', 'E5', 'Contract', TRUE, '2026-04-01 11:00:00', 'sanjayr9586@gmail.com',
    '2026-03-01', 58.00, 'det_009_nathan_arch', 'proj_cloud_mod_003',
    155.00, 'nathan.cross.arch@gmail.com'
)
ON CONFLICT (id) DO NOTHING;

-- 4. Milestone (Key delivery commitments with real-world financial valuations)
INSERT INTO "Milestone" (
    id, "projectId", name, amount, "dueDate", status, "createdBy", "modifiedBy"
) VALUES
-- Alpha AI Platform Milestones
(
    'mile_001_alpha_arch', 'proj_alpha_ai_001', 'DDL Schema & Semantic Layer Design Sign-Off', 50000.00, '2026-02-28', 'Completed', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'mile_002_alpha_rag', 'proj_alpha_ai_001', 'Azure OpenAI & Embedding Retrieval Pipeline', 75000.00, '2026-04-30', 'Completed', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'mile_003_alpha_sql_agent', 'proj_alpha_ai_001', 'LangGraph Text-to-SQL Multi-Turn Agent with Guardrails', 95000.00, '2026-07-31', 'In Progress', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'mile_004_alpha_prod_streaming', 'proj_alpha_ai_001', 'Production SSE Streaming & OpenTelemetry Rollout', 60000.00, '2026-10-31', 'Pending', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),

-- FinTech Copilot Milestones
(
    'mile_005_fintech_connectors', 'proj_fintech_copilot_002', 'Quantitative Market Connectors & Data Lakehouse Ingestion', 85000.00, '2026-04-15', 'Completed', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'mile_006_fintech_risk_engine', 'proj_fintech_copilot_002', 'Real-Time Portfolio Risk Assessment & SQL Copilot', 110000.00, '2026-08-31', 'In Progress', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'mile_007_fintech_compliance', 'proj_fintech_copilot_002', 'Regulatory Audit Trail & MiFID II Enforcement Gateway', 65000.00, '2026-11-15', 'Pending', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),

-- Cloud Modernization Milestones
(
    'mile_008_cloud_vpc', 'proj_cloud_mod_003', 'Multi-Region Azure Kubernetes (AKS) & VNet Peering', 95000.00, '2026-05-30', 'Completed', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'mile_009_cloud_db_cutover', 'proj_cloud_mod_003', 'PostgreSQL Flexible Server Migration & Cutover Sign-Off', 85000.00, '2026-09-30', 'Pending', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),

-- Healthcare Clinical Hub Milestones
(
    'mile_010_health_hipaa', 'proj_health_omnichannel_004', 'HIPAA Security BAA & Medical De-identification Gateway', 70000.00, '2026-05-31', 'Completed', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'mile_011_health_fhir_rag', 'proj_health_omnichannel_004', 'FHIR / HL7 Ingestion & Clinical Guidelines Knowledge Base', 120000.00, '2026-09-30', 'In Progress', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),

-- Supply Chain Milestones
(
    'mile_012_sc_erp_sync', 'proj_supply_chain_005', 'ERP Connectors & Real-Time Warehouse Telemetry', 60000.00, '2026-07-31', 'In Progress', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'mile_013_sc_route_agent', 'proj_supply_chain_005', 'Predictive Delay Reasoning Agent & Freight Rerouting', 75000.00, '2026-11-30', 'Pending', 'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
)
ON CONFLICT (id) DO NOTHING;

-- 5. ContractAmendment (Legitimate change requests and scope expansions)
INSERT INTO "ContractAmendment" (
    id, "projectId", type, amount, "effectiveDate", description, "createdBy", "modifiedBy"
) VALUES
(
    'amend_001_scope_rbac', 'proj_alpha_ai_001', 'ScopeExtension', 35000.00, '2026-04-01',
    'Addition of multi-tenant row-level access control module with automated Entra ID claim mapping.',
    'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'amend_002_fintech_mifid', 'proj_fintech_copilot_002', 'ComplianceEnhance', 40000.00, '2026-05-15',
    'Expansion of query redaction rules to meet stringent SEC Rule 17a-4 and European MiFID II requirements.',
    'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'amend_003_cloud_dr', 'proj_cloud_mod_003', 'ArchitectureScope', 50000.00, '2026-06-01',
    'Inclusion of secondary disaster recovery zone with automated cross-region failover automation.',
    'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
),
(
    'amend_004_health_trials', 'proj_health_omnichannel_004', 'ScopeExtension', 45000.00, '2026-07-01',
    'Integration with ClinicalTrials.gov and PubMed REST endpoints for dynamic oncological trial matching.',
    'sanjayr9586@gmail.com', 'sanjayr9586@gmail.com'
)
ON CONFLICT (id) DO NOTHING;

-- 6. Contract (Formal master agreements and statements of work)
INSERT INTO "Contract" (
    id, "projectId", "contractName", status, "contractType", "startDate", "endDate", value
) VALUES
(
    'cntr_001_alpha_master', 'proj_alpha_ai_001',
    'MSA-2026-AI-01 - Global Enterprise GenAI & Text-to-SQL Platform',
    'Active', 'MasterService', '2026-01-15', '2026-12-31', 450000.00
),
(
    'cntr_002_fintech_sow', 'proj_fintech_copilot_002',
    'SOW-FIN-01 - Financial Risk Analytics & Natural Language Copilot',
    'Active', 'StatementOfWork', '2026-02-01', '2026-11-30', 320000.00
),
(
    'cntr_003_cloud_sow', 'proj_cloud_mod_003',
    'SOW-CLOUD-02 - Multi-Region Azure Foundation & Zero-Trust Mesh',
    'Active', 'StatementOfWork', '2026-03-01', '2026-10-31', 240000.00
),
(
    'cntr_004_health_msa', 'proj_health_omnichannel_004',
    'MSA-2026-HEALTH-03 - Clinical Intelligence & Patient Hub Implementation',
    'Active', 'MasterService', '2026-04-01', '2027-03-31', 520000.00
),
(
    'cntr_005_supply_sow', 'proj_supply_chain_005',
    'SOW-LOG-01 - Autonomous Supply Chain Inventory Copilot',
    'Active', 'StatementOfWork', '2026-05-15', '2027-01-31', 280000.00
)
ON CONFLICT (id) DO NOTHING;
