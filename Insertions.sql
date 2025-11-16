INSERT INTO young_people -- Insert into young_people
    (first_name, last_name, phone, email)
VALUES
    ('John',    'Doe',      0770004451, 'john.doe1@gmail.com'),
    ('Jane',    'Doe',      0770000002, 'jane.doe2@gmail.com'),
    ('Jim',     'Smith',    0770000003, 'jim.smith3@gmail.com'),
    ('Jill',    'Smith',    0770000004, 'jill.smith4@gmail.com'),
    ('Eyas',    'Dmour',    0779788841, '22220004@htu.edu.jo'),
    ('Sanad',   'Toghoj',   0779788842, '22220003@htu.edu.jo'),
    ('Mohammad','Al-Masri', 0779788843, 'mohmasri@gmail.com'),
    ('Ahmad',   'Al-Masri', 0779788844, 'ahmadmasri@gmail.com'),
    ('Sally',   'Batal',    0799825564, 'sally.f65@gmail.com'),
    ('Zuhair',  'Dmour',    0788778860, 'zuhairdmour@gmail.com');

-- SELECT * FROM young_people;



INSERT INTO projects    -- Insert into projects
    (leader_id, project_name, project_description)
VALUES
    (5, 'Open Delivery App',       'The open take on the huge wave of delivery apps. 100% Jordanian, 100% open source.'),
    (6, 'Jordanian Social Media',  'Local social media platfor for the Local people of Jordan, with relavant news and content.'),
    (10, 'Medicine Tracker',        'All inclusive app for delivering tracking and taking medicine.'),
    (7, 'Arabic AI',               'A usefull arabic LLM that understands the advanced concepts of the arabic language.'),
    (8, 'E-Commerce',              'A local e-commerce website, compete with opensooq.'),
    (9, 'Jordanian News',          'news platform run by the Jordanian students.'),
    (1, 'New Project 1',           'Under Development!!!'),
    (2, 'New Project 2',           'Under Development!!!'),
    (3, 'New Project 3',           'Under Development!!!'),
    (4, 'New Project 4',           'Under Development!!!');


-- SELECT * FROM projects;



INSERT INTO participate  -- Insert into participate
    (project_id, youth_id)
VALUES
    (1, 7),
    (1, 8),
    (2, 1),
    (2, 2),
    (2, 8),
    (3, 7),
    (3, 3),
    (3, 2),
    (3, 8),
    (3, 9),
    (4, 1),
    (4, 4),
    (4, 6),
    (4, 10),
    (5, 5),
    (6, 8);

-- SELECT * FROM participate;

INSERT INTO investors   -- Insert into investors
    (first_name, last_name, phone, email)
VALUES
    ('Khaled', 'Sameer', 0770000005, 'Khaled@gmail.com'),
    ('Tamer', 'Khaled', 0770000006, 'Tamer@gmail.com'),
    ('Jafer', 'Dmour', 0770000007, 'Jafer@gmail.com'),
    ('Ahmad', 'Saleh', 0770000008, 'Ahmad@gmail.com');

-- SELECT * FROM investors;



INSERT INTO investments -- Insert into investments
    (investor_id, project_id, amount)
VALUES
    (1, 1, 750),
    (1, 2, 5000),
    (1, 3, 3500),
    (1, 4, 500),

    (2, 5,  1000),
    (2, 6,  1000),
    (2, 7,  100),

    (3, 8, 3000),
    (3, 9, 300),

    (4, 10, 200);

-- DELETE FROM investments;
-- SELECT * FROM investments;
