-- Insert Verticals
INSERT INTO "Vertical" (code, name, area)
VALUES
('CA', 'Central Application', 'CentralApplication'),
('CHDLO', 'Chief Delivery Office', 'IndividualModule'),
('CHRCO', 'Chief Risk and Compliance Office', 'IndividualModule'),
('CHDMO', 'Chief Demand Office', 'IndividualModule'),
('CHTFO', 'Chief Transformation Office', 'IndividualModule'),
('CHFIO', 'Chief Finance Office', 'IndividualModule'),
('CHAIO', 'Chief AI Office', 'IndividualModule'),
('CHTCO', 'Chief Technology Office', 'IndividualModule'),
('CHTAO', 'Chief Talent Office', 'IndividualModule'),
('CHGRO', 'Chief Growth Office', 'IndividualModule'),
('CHHCO', 'Chief Happiness and Culture Office', 'IndividualModule'),
('CHENO', 'Chief Enablement Office', 'IndividualModule'),
('CHINO', 'Chief Innovation Office', 'IndividualModule')
ON CONFLICT (code) DO NOTHING;
