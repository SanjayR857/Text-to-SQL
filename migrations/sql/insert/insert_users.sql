-- Insert Seed Platform Users (Synchronized with Role Assignments & Project Staffing)
-- Pre-existing platform principal identity table (`users`)

INSERT INTO users (id, email, created_at)
VALUES
-- Core Leadership & Test Principals (Consistent UUIDs for deterministic testing)
('e85c0a56-ceb8-4a4f-b449-f481f4018343', 'sanjayr9586@gmail.com', CURRENT_TIMESTAMP),
('1f833c6d-19e3-478d-b0aa-0797beffeb44', 'elena.rostova.ai@gmail.com', CURRENT_TIMESTAMP),
('00000000-0000-0000-0000-000000000001', 'alex.chen.eng@gmail.com', CURRENT_TIMESTAMP),
('00000000-0000-0000-0000-000000000002', 'dev.unassigned@gmail.com', CURRENT_TIMESTAMP),

-- Central & AI Office Personnel
('a1b2c3d4-0001-4000-8000-000000000001', 'priya.sharma.lead@gmail.com', CURRENT_TIMESTAMP),
('a1b2c3d4-0001-4000-8000-000000000002', 'vikram.malhotra.lead@gmail.com', CURRENT_TIMESTAMP),
('a1b2c3d4-0001-4000-8000-000000000003', 'marcus.vance.ai@gmail.com', CURRENT_TIMESTAMP),
('a1b2c3d4-0001-4000-8000-000000000004', 'ananya.patel.ml@gmail.com', CURRENT_TIMESTAMP),
('a1b2c3d4-0001-4000-8000-000000000005', 'daniel.kim.data@gmail.com', CURRENT_TIMESTAMP),

-- Delivery & Technology Personnel
('b2c3d4e5-0002-4000-8000-000000000001', 'marcus.vance.cdo@gmail.com', CURRENT_TIMESTAMP),
('b2c3d4e5-0002-4000-8000-000000000002', 'jordan.hayes.ep@gmail.com', CURRENT_TIMESTAMP),
('b2c3d4e5-0002-4000-8000-000000000003', 'elizabeth.taylor.ep@gmail.com', CURRENT_TIMESTAMP),
('b2c3d4e5-0002-4000-8000-000000000004', 'david.k.delivery@gmail.com', CURRENT_TIMESTAMP),
('b2c3d4e5-0002-4000-8000-000000000005', 'emily.watson.lead@gmail.com', CURRENT_TIMESTAMP),
('b2c3d4e5-0002-4000-8000-000000000006', 'carlos.mendez.lead@gmail.com', CURRENT_TIMESTAMP),
('b2c3d4e5-0002-4000-8000-000000000007', 'pmo.delivery.office@gmail.com', CURRENT_TIMESTAMP),
('b2c3d4e5-0002-4000-8000-000000000008', 'robert.chen.cto@gmail.com', CURRENT_TIMESTAMP),
('b2c3d4e5-0002-4000-8000-000000000009', 'kevin.t.cloudmgr@gmail.com', CURRENT_TIMESTAMP),
('b2c3d4e5-0002-4000-8000-000000000010', 'nathan.cross.arch@gmail.com', CURRENT_TIMESTAMP),
('b2c3d4e5-0002-4000-8000-000000000011', 'tanya.petrov.tech@gmail.com', CURRENT_TIMESTAMP),

-- Talent, Risk, Finance, Demand & Other Offices
('c3d4e5f6-0003-4000-8000-000000000001', 'laura.bennett.talent@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000002', 'brian.foster.talent@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000003', 'chloe.zheng.bench@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000004', 'arthur.pendelton.risk@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000005', 'hannah.abbott.compliance@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000006', 'richard.sterling.cfo@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000007', 'clara.oswald.finance@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000008', 'victoria.sterling.demand@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000009', 'liam.o.connor.sales@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000010', 'samira.khan.growth@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000011', 'xavier.dupont.innov@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000012', 'maya.lin.rnd@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000013', 'olivia.williams.culture@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000014', 'gordon.freeman.enable@gmail.com', CURRENT_TIMESTAMP),
('c3d4e5f6-0003-4000-8000-000000000015', 'alicia.torres.transform@gmail.com', CURRENT_TIMESTAMP)
ON CONFLICT (id) DO UPDATE
SET email = EXCLUDED.email;
