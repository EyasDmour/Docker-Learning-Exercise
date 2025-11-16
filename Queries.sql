
CREATE VIEW Project_Investments
AS
    SELECT p.Project_Name, (y.first_name + ' ' + y.last_name) as Project_Leader, (i.first_name + ' ' + i.last_name) as Investor, inv.Amount
    FROM Projects p
        JOIN Young_People y ON p.Leader_ID = y.Youth_ID
        JOIN Investments inv ON p.Project_ID = inv.Project_ID
        JOIN Investors i ON inv.investor_id = i.investor_id



SELECT *
FROM Project_Investments; --admin and investor


CREATE VIEW Project_Members
AS
    SELECT p.Project_Name, COUNT(y.Youth_ID) as Number_of_Members
    FROM Projects p
        JOIN participate pm ON p.Project_ID = pm.Project_ID
        JOIN Young_People y ON pm.Youth_ID = y.Youth_ID
    GROUP BY p.Project_Name;



SELECT *
FROM Project_Members
ORDER BY Number_of_Members DESC; --user


CREATE VIEW Investment_Stats
AS
    SELECT COUNT(inv.Project_ID) as Number_of_Investments,
        SUM(inv.Amount)       as Total_Investment,
        AVG(inv.Amount)       as Average_Investment
    FROM Investments inv;

SELECT *
FROM Investment_Stats;  -- admin

CREATE VIEW Investors_Stats -- This view shows the sum of money from each investor
    AS
        SELECT (i.first_name + ' ' + i.last_name) as Investor,
            COUNT(inv.Amount) as Count, 
            SUM(inv.Amount) as Total_Investments
        FROM Investments inv
            JOIN Investors i ON inv.Investor_ID = i.Investor_ID
        GROUP BY i.first_name, i.last_name;

SELECT * FROM Investors_Stats;     -- admin




-- _____________________________________PROCEDURES________________________________________

--Procedure to show who is involved in project X

CREATE PROCEDURE Project_Participants(@Project_Name varchar(30))
AS
BEGIN
    SELECT (y.first_name + ' ' + y.last_name) as Project_Member
    FROM Projects p
        JOIN participate pm ON p.Project_ID = pm.Project_ID
        JOIN Young_People y ON pm.Youth_ID = y.Youth_ID
    WHERE p.Project_Name = @Project_Name;
END



EXECUTE Project_Participants 'Medicine Tracker'; -- projectLeader


--Procedure to get all projects the investor X is involved in

CREATE PROCEDURE Investor_Projects(@Investor varchar(30))
AS
BEGIN
    SELECT p.Project_Name, (y.first_name + ' ' + y.last_name) as Project_Leader, inv.Amount
    FROM Projects p
        JOIN Investments inv ON p.Project_ID = inv.Project_ID
        JOIN Investors i ON inv.Investor_ID = i.Investor_ID
        JOIN Young_People y ON p.Leader_ID = y.Youth_ID
    WHERE i.Investor_ID = @Investor;
END



EXECUTE Investor_Projects '1'; -- investor


--procedure to insert a new project
CREATE PROCEDURE Insert_Project(@Leader_ID int,
    @Project_Name varchar(30),
    @Description text)
AS
BEGIN
    INSERT INTO Projects
        (Leader_ID, Project_Name, Description)
    VALUES
        (@Leader_ID, @Project_Name, @Description);
END



EXECUTE Insert_Project 11, 'New Project', 'Under Development!!!'; -- user




-- Procedure to insert a new youth
CREATE PROCEDURE Insert_Youth(@FName varchar(12),
    @LName varchar(12),
    @Youth_PNumber int,
    @Youth_Email varchar(22))
AS
BEGIN
    INSERT INTO Young_People
        (first_name, last_name, Youth_PNumber, Youth_Email)
    VALUES
        (@first_name, @last_name, @Youth_PNumber, @Youth_Email);
END



EXECUTE Insert_Youth 'Ayham', 'Shokairat', 0772882898, 'ayhamshok@gmail.com'; -- user




CREATE PROCEDURE Add_Member(@Project_ID int,
    @Youth_ID int)
AS
BEGIN
    INSERT INTO participate
        (Project_ID, Youth_ID)
    VALUES
        (@Project_ID, @Youth_ID);
END

EXECUTE Add_Member 7, 23;   -- projectLeader

-- _____________________________________TRIGGERS________________________________________

CREATE TRIGGER LeaderMember -- This automatically adds a leader as a member, for every new project.
ON Projects
AFTER INSERT
AS
BEGIN
    INSERT INTO participate
        (Project_ID, Youth_ID)
    SELECT Project_ID, Leader_ID
    FROM inserted;
END;


-- _____________________________________BACKUP________________________________________


BACKUP DATABASE YouthInnovation     -- Full backup
TO DISK = 'C:\BACK\YouthInnovation.bak'
WITH INIT,
NAME = 'Full backup';

BACKUP LOG YouthInnovation            -- Transactional log backup
TO DISK = 'C:\BACK\YouthInnovation.bak'
WITH NAME = 'Log backup';

RESTORE headeronly FROM DISK = 'C:\BACK\YouthInnovation.bak';

RESTORE DATABASE YouthInnovation
FROM  DISK = N'D:\BACK\YouthInnovation.bak'
WITH FILE = <n>, NORECOVERY;

RESTORE LOG YouthInnovation
FROM  DISK = N'D:\BACK\YouthInnovation.bak'
WITH FILE =<n+x>, RECOVERY;
-- _____________________________________ USERS ________________________________________


CREATE LOGIN admin WITH PASSWORD = 'admin123';

CREATE USER admin
FOR LOGIN admin;

GRANT SELECT ON 
    Investors_Stats 
TO admin;

GRANT SELECT ON 
    Investment_Stats
TO admin;

GRANT SELECT ON 
    Project_Investments
TO admin;

GRANT SELECT, INSERT, DELETE, UPDATE ON 
    Projects
TO admin;

GRANT SELECT, INSERT, DELETE, UPDATE ON
    Young_People
TO admin;

GRANT SELECT, INSERT, DELETE, UPDATE ON
    participate
TO admin;

GRANT SELECT, INSERT, DELETE, UPDATE ON 
    Investors
TO admin;

GRANT SELECT, INSERT, DELETE, UPDATE ON 
    Investments
TO admin;





CREATE LOGIN users WITH PASSWORD = 'users123';

CREATE USER users
FOR LOGIN users;

GRANT SELECT ON 
    Project_Members
TO users;

GRANT EXECUTE ON 
    Insert_Project
TO users;

GRANT EXECUTE ON 
    Insert_Youth
TO users;




CREATE LOGIN leader WITH PASSWORD = 'leader123';

CREATE USER leader
FOR LOGIN leader;

GRANT EXECUTE ON 
    Add_Member
TO leader;

GRANT EXECUTE ON 
    Project_Participants
TO leader;

DROP LOGIN investor;
DROP USER Khaled;


CREATE LOGIN investor WITH PASSWORD = 'investor123';

CREATE USER investor
FOR LOGIN investor;

GRANT EXECUTE ON 
    Investor_Projects
TO investor;

GRANT SELECT ON 
    Project_Investments
TO investor;

SELECT * FROM Project_Investments;

-- _____________________________________ QUERIES ________________________________________

-- A 'Select' query with a 'Where' condition. 
Select * FROM Young_People WHERE Youth_ID > 5;


-- Operations for 'Insert', 'Update', and 'Delete'.
 Update Young_People SET phone = '0779788644' WHERE Youth_ID = 1;
Select * FROM Young_People WHERE Youth_ID = 1;


-- Use of an aggregation function along with 'Group By'.
SELECT p.Project_Name, COUNT(y.Youth_ID) as Number_of_Members
    FROM Projects p
        JOIN participate pm ON p.Project_ID = pm.Project_ID
        JOIN Young_People y ON pm.Youth_ID = y.Youth_ID
    GROUP BY p.Project_Name;

--______________________________________Extra________________________________________

Select * FROM Investors;