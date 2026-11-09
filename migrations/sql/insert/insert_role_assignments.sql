-- Insert Seed Role Assignments (Synchronized with Project Staffing & Leadership)
-- Enums: 'ADMIN', 'DEV', 'EP', 'ES', 'CHIEF', 'LEAD', 'CON'
-- Verticals: 'CA', 'CHDLO', 'CHRCO', 'CHDMO', 'CHTFO', 'CHFIO', 'CHAIO', 'CHTCO', 'CHTAO', 'CHGRO', 'CHHCO', 'CHENO', 'CHINO'

INSERT INTO "RoleAssignment" (email, "verticalCode", role, "assignedBy")
VALUES
-- Central Application (CA)
('admin@enterprise.ai', 'CA', 'ADMIN', 'system'),
('dev.engineer@enterprise.ai', 'CA', 'DEV', 'admin@enterprise.ai'),
('dev.lead@enterprise.ai', 'CA', 'DEV', 'admin@enterprise.ai'),

-- Chief AI Office (CHAIO)
('chief.ai@enterprise.ai', 'CHAIO', 'CHIEF', 'admin@enterprise.ai'),
('tech.lead1@enterprise.ai', 'CHAIO', 'LEAD', 'chief.ai@enterprise.ai'),
('tech.lead2@enterprise.ai', 'CHAIO', 'LEAD', 'chief.ai@enterprise.ai'),
('ai.lead@enterprise.ai', 'CHAIO', 'LEAD', 'chief.ai@enterprise.ai'),
('ai.consultant@enterprise.ai', 'CHAIO', 'CON', 'chief.ai@enterprise.ai'),

-- Chief Delivery Office (CHDLO)
('director.eng@enterprise.ai', 'CHDLO', 'CHIEF', 'admin@enterprise.ai'),
('partner.lead@enterprise.ai', 'CHDLO', 'EP', 'admin@enterprise.ai'),
('manager.delivery@enterprise.ai', 'CHDLO', 'LEAD', 'partner.lead@enterprise.ai'),
('delivery.lead@enterprise.ai', 'CHDLO', 'LEAD', 'manager.delivery@enterprise.ai'),
('delivery.ep@enterprise.ai', 'CHDLO', 'EP', 'partner.lead@enterprise.ai'),
('chief.delivery@enterprise.ai', 'CHDLO', 'CHIEF', 'admin@enterprise.ai'),

-- Chief Technology Office (CHTCO)
('chief.tech@enterprise.ai', 'CHTCO', 'CHIEF', 'admin@enterprise.ai'),
('manager.cloud@enterprise.ai', 'CHTCO', 'LEAD', 'chief.tech@enterprise.ai'),
('cloud.architect@enterprise.ai', 'CHTCO', 'LEAD', 'manager.cloud@enterprise.ai'),
('tech.es@enterprise.ai', 'CHTCO', 'ES', 'chief.tech@enterprise.ai'),

-- Chief Talent Office (CHTAO)
('director.talent@enterprise.ai', 'CHTAO', 'CHIEF', 'admin@enterprise.ai'),
('manager.talent@enterprise.ai', 'CHTAO', 'LEAD', 'director.talent@enterprise.ai'),
('bench.coordinator@enterprise.ai', 'CHTAO', 'ES', 'manager.talent@enterprise.ai'),

-- Chief Risk and Compliance Office (CHRCO)
('chief.risk@enterprise.ai', 'CHRCO', 'CHIEF', 'admin@enterprise.ai'),
('compliance.lead@enterprise.ai', 'CHRCO', 'LEAD', 'chief.risk@enterprise.ai'),

-- Chief Finance Office (CHFIO)
('chief.finance@enterprise.ai', 'CHFIO', 'CHIEF', 'admin@enterprise.ai')
ON CONFLICT (email, "verticalCode") DO UPDATE
SET role = EXCLUDED.role,
    "assignedBy" = EXCLUDED."assignedBy",
    "updatedAt" = CURRENT_TIMESTAMP;
