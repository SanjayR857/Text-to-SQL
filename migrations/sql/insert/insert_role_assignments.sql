-- Insert Seed Role Assignments (Synchronized with Project Staffing & Leadership)
-- Enums: 'ADMIN', 'DEV', 'EP', 'ES', 'CHIEF', 'LEAD', 'CON'
-- Verticals: 'CA', 'CHDLO', 'CHRCO', 'CHDMO', 'CHTFO', 'CHFIO', 'CHAIO', 'CHTCO', 'CHTAO', 'CHGRO', 'CHHCO', 'CHENO', 'CHINO'

INSERT INTO "RoleAssignment" (email, "verticalCode", role, "assignedBy")
VALUES
-- Central Application (CA)
('sanjayr9586@gmail.com', 'CA', 'ADMIN', 'system'),
('alex.chen.eng@gmail.com', 'CA', 'DEV', 'sanjayr9586@gmail.com'),
('priya.sharma.lead@gmail.com', 'CA', 'DEV', 'sanjayr9586@gmail.com'),

-- Chief AI Office (CHAIO)
('elena.rostova.ai@gmail.com', 'CHAIO', 'CHIEF', 'sanjayr9586@gmail.com'),
('sanjayr9586@gmail.com', 'CHAIO', 'LEAD', 'elena.rostova.ai@gmail.com'),
('vikram.malhotra.lead@gmail.com', 'CHAIO', 'LEAD', 'elena.rostova.ai@gmail.com'),
('marcus.vance.ai@gmail.com', 'CHAIO', 'LEAD', 'elena.rostova.ai@gmail.com'),
('ananya.patel.ml@gmail.com', 'CHAIO', 'CON', 'sanjayr9586@gmail.com'),
('daniel.kim.data@gmail.com', 'CHAIO', 'CON', 'vikram.malhotra.lead@gmail.com'),

-- Chief Delivery Office (CHDLO)
('marcus.vance.cdo@gmail.com', 'CHDLO', 'CHIEF', 'sanjayr9586@gmail.com'),
('jordan.hayes.ep@gmail.com', 'CHDLO', 'EP', 'marcus.vance.cdo@gmail.com'),
('elizabeth.taylor.ep@gmail.com', 'CHDLO', 'EP', 'marcus.vance.cdo@gmail.com'),
('david.k.delivery@gmail.com', 'CHDLO', 'LEAD', 'jordan.hayes.ep@gmail.com'),
('emily.watson.lead@gmail.com', 'CHDLO', 'LEAD', 'david.k.delivery@gmail.com'),
('carlos.mendez.lead@gmail.com', 'CHDLO', 'LEAD', 'david.k.delivery@gmail.com'),

-- Chief Technology Office (CHTCO)
('robert.chen.cto@gmail.com', 'CHTCO', 'CHIEF', 'sanjayr9586@gmail.com'),
('kevin.t.cloudmgr@gmail.com', 'CHTCO', 'LEAD', 'robert.chen.cto@gmail.com'),
('nathan.cross.arch@gmail.com', 'CHTCO', 'LEAD', 'kevin.t.cloudmgr@gmail.com'),
('tanya.petrov.tech@gmail.com', 'CHTCO', 'ES', 'robert.chen.cto@gmail.com'),

-- Chief Talent Office (CHTAO)
('laura.bennett.talent@gmail.com', 'CHTAO', 'CHIEF', 'sanjayr9586@gmail.com'),
('brian.foster.talent@gmail.com', 'CHTAO', 'LEAD', 'laura.bennett.talent@gmail.com'),
('chloe.zheng.bench@gmail.com', 'CHTAO', 'ES', 'brian.foster.talent@gmail.com'),

-- Chief Risk and Compliance Office (CHRCO)
('arthur.pendelton.risk@gmail.com', 'CHRCO', 'CHIEF', 'sanjayr9586@gmail.com'),
('hannah.abbott.compliance@gmail.com', 'CHRCO', 'LEAD', 'arthur.pendelton.risk@gmail.com'),

-- Chief Finance Office (CHFIO)
('richard.sterling.cfo@gmail.com', 'CHFIO', 'CHIEF', 'sanjayr9586@gmail.com'),
('clara.oswald.finance@gmail.com', 'CHFIO', 'LEAD', 'richard.sterling.cfo@gmail.com'),

-- Chief Demand Office (CHDMO)
('victoria.sterling.demand@gmail.com', 'CHDMO', 'CHIEF', 'sanjayr9586@gmail.com'),
('liam.o.connor.sales@gmail.com', 'CHDMO', 'LEAD', 'victoria.sterling.demand@gmail.com'),

-- Chief Growth Office (CHGRO)
('samira.khan.growth@gmail.com', 'CHGRO', 'CHIEF', 'sanjayr9586@gmail.com'),

-- Chief Innovation Office (CHINO)
('xavier.dupont.innov@gmail.com', 'CHINO', 'CHIEF', 'sanjayr9586@gmail.com'),
('maya.lin.rnd@gmail.com', 'CHINO', 'LEAD', 'xavier.dupont.innov@gmail.com'),

-- Chief Happiness and Culture Office (CHHCO)
('olivia.williams.culture@gmail.com', 'CHHCO', 'CHIEF', 'sanjayr9586@gmail.com'),

-- Chief Enablement Office (CHENO)
('gordon.freeman.enable@gmail.com', 'CHENO', 'CHIEF', 'sanjayr9586@gmail.com'),

-- Chief Transformation Office (CHTFO)
('alicia.torres.transform@gmail.com', 'CHTFO', 'CHIEF', 'sanjayr9586@gmail.com')
ON CONFLICT (email, "verticalCode") DO UPDATE
SET role = EXCLUDED.role,
    "assignedBy" = EXCLUDED."assignedBy",
    "updatedAt" = CURRENT_TIMESTAMP;
