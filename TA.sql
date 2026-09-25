-- create and use db
CREATE DATABASE Internship_Management;
USE Internship_Management;

-- table definitions
CREATE TABLE Candidates (
    CandidateID INT PRIMARY KEY AUTO_INCREMENT,
    FullName VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Resume_Text TEXT,
    Experience_Yrs DECIMAL(4,2)
);

CREATE TABLE Job_Postings (
    JobID INT PRIMARY KEY AUTO_INCREMENT,
    Title VARCHAR(100) NOT NULL,
    Job_Description TEXT,
    Required_Skills TEXT,
    Min_Experience DECIMAL(4,2),
    Is_Active BOOLEAN DEFAULT 1
);

CREATE TABLE Applications (
    AppID INT PRIMARY KEY AUTO_INCREMENT,
    CandidateID INT,
    JobID INT,
    Application_Date DATE DEFAULT (CURRENT_DATE),
    Status VARCHAR(30) DEFAULT 'Applied',
    AI_Match_Score DECIMAL(5,2),
    FOREIGN KEY (CandidateID) REFERENCES Candidates(CandidateID),
    FOREIGN KEY (JobID) REFERENCES Job_Postings(JobID)
);

CREATE TABLE Interviews (
    InterviewID INT PRIMARY KEY AUTO_INCREMENT,
    AppID INT,
    Interviewer_Name VARCHAR(100),
    Interview_Date DATE,
    Score INT,
    Feedback TEXT,
    FOREIGN KEY (AppID) REFERENCES Applications(AppID)
);

-- inserting job postings
INSERT INTO Job_Postings (Title, Job_Description, Required_Skills, Min_Experience) VALUES
('Data Scientist', 'Looking for a data scientist to build predictive models and work with unstructured data.', 'Python, Machine Learning, NLP, SQL, TensorFlow', 2.0),
('Junior Web Developer', 'Seeking a passionate fresher for frontend and backend development.', 'JavaScript, React, Node.js, HTML, CSS', 0.0),
('DevOps Engineer', 'Manage cloud infrastructure, CI/CD pipelines, and server deployments.', 'AWS, Docker, Kubernetes, Jenkins, Linux', 3.0),
('UI/UX Designer', 'Design user-friendly interfaces and conduct user research for mobile apps.', 'Figma, Adobe XD, Wireframing, Prototyping, UI Design', 2.0),
('Backend Developer', 'Develop robust REST APIs and manage database architecture.', 'Python, Django, PostgreSQL, REST API, Microservices', 2.5),
('Data Analyst', 'Analyze business data, create dashboards, and report insights to stakeholders.', 'SQL, Excel, Tableau, PowerBI, Python', 1.0),
('Full Stack Developer', 'End-to-end web application development.', 'MERN Stack, MongoDB, Express, React, Node, TypeScript', 3.0),
('Machine Learning Intern', 'Assist in cleaning data and training basic classification models.', 'Python, Pandas, Scikit-Learn, Matplotlib', 0.0);

-- inserting candidates
INSERT INTO Candidates (FullName, Email, Resume_Text, Experience_Yrs) VALUES
('Aarav Sharma', 'aarav@email.com', 'Experienced Data Scientist with 4 years of experience. Expert in Python, SQL, Machine Learning, Deep Learning, and NLP. Built recommendation systems using TensorFlow.', 4.0),
('Priya Patel', 'priya@email.com', 'Recent graduate with a B.Tech in Computer Science. Strong skills in Java, C++, and basic SQL. Academic project on Web Development using React and Node.js.', 0.5),
('Rohan Gupta', 'rohan@email.com', 'Data Analyst with 2 years of experience. Proficient in Data Visualization using Tableau and PowerBI. Advanced SQL and Excel skills. Basic knowledge of Python for data cleaning.', 2.0),
('Neha Singh', 'neha@email.com', 'Senior Machine Learning Engineer. 6 years of experience in deploying ML models to production. Skills: Python, AWS, Docker, Kubernetes, Scikit-learn, PyTorch.', 6.0),
('Vikram Joshi', 'vikram@email.com', 'DevOps Specialist focusing on AWS and Kubernetes. 3 years managing CI/CD pipelines with Jenkins and GitLab. Strong Linux administration skills.', 3.5),
('Aditi Verma', 'aditi@email.com', 'Creative UI/UX Designer with 2 years of experience. Expert in Figma and Adobe XD. Built wireframes and interactive prototypes for e-commerce apps.', 2.0),
('Karan Desai', 'karan@email.com', 'Backend developer skilled in Python and Django. Experience with PostgreSQL databases and building scalable REST APIs.', 2.5),
('Simran Kaur', 'simran@email.com', 'Full stack developer passionate about the MERN stack. Proficient in MongoDB, Express, React, and Node.js. Typescript enthusiast.', 3.0),
('Rahul Iyer', 'rahul@email.com', 'Fresher looking for ML Internship. Completed courses in Python, Pandas, and Scikit-Learn. Good at data visualization using Matplotlib.', 0.0),
('Sneha Reddy', 'sneha@email.com', 'Graphic designer transitioning into UI/UX. Knows Photoshop, Illustrator, and basic Figma. Limited prototyping experience.', 1.0),
('Amit Kumar', 'amit@email.com', 'System Administrator with 5 years experience. Good with Linux and networking, but just started learning Docker and AWS.', 5.0),
('Pooja Das', 'pooja@email.com', 'Data Analyst expert in SQL and Excel. No programming experience. Strong business acumen and reporting skills.', 3.0),
('Sanjay Mishra', 'sanjay@email.com', 'Self-taught Web Developer. Knows HTML, CSS, JavaScript. Built personal portfolio and small vanilla JS projects.', 0.5),
('Kavita Rao', 'kavita@email.com', 'AI Researcher with 7 years academic experience. Published papers on NLP and Transformer models. Deep knowledge of TensorFlow and PyTorch.', 7.0),
('Manish Tiwari', 'manish@email.com', 'Software Engineer working mostly in C# and .NET. Looking to transition into Full Stack web development.', 4.0);

-- application records with mixed matches for testing
INSERT INTO Applications (CandidateID, JobID, Status) VALUES
-- good matches
(1, 1, 'Applied'),
(5, 3, 'Applied'),
(6, 4, 'Applied'),
(8, 7, 'Applied'),
(9, 8, 'Applied'),
(7, 5, 'Applied'),

-- average matches
(4, 1, 'Applied'),
(10, 4, 'Applied'),
(11, 3, 'Applied'),
(3, 6, 'Applied'),
(13, 2, 'Applied'),

-- bad matches
(15, 7, 'Applied'),
(12, 1, 'Applied'),
(2, 4, 'Applied'),
(14, 2, 'Applied'),
(6, 3, 'Applied');

-- trigger to update application status after interview
DELIMITER //
CREATE TRIGGER UpdateAppStatusAfterInterview
AFTER INSERT ON Interviews
FOR EACH ROW
BEGIN
    IF NEW.Score >= 80 THEN
        UPDATE Applications SET Status = 'Offer Extended' WHERE AppID = NEW.AppID;
    ELSEIF NEW.Score < 50 THEN
        UPDATE Applications SET Status = 'Rejected' WHERE AppID = NEW.AppID;
    ELSE 
        UPDATE Applications SET Status = 'Interviewing' WHERE AppID = NEW.AppID;
    END IF;
END //
DELIMITER ;

-- analytics and advanced sql queries

-- find jobs where average ai score is above 20
SELECT 
    j.Title AS Job_Role, 
    COUNT(a.AppID) AS Total_Applicants, 
    ROUND(AVG(a.AI_Match_Score), 2) AS Avg_AI_Score
FROM Applications a
JOIN Job_Postings j ON a.JobID = j.JobID
GROUP BY j.Title
HAVING AVG(a.AI_Match_Score) > 20.00
ORDER BY Avg_AI_Score DESC;

-- find highly experienced candidates
SELECT 
    FullName, 
    Experience_Yrs, 
    Resume_Text 
FROM Candidates 
WHERE Experience_Yrs > (SELECT AVG(Experience_Yrs) FROM Candidates);

-- candidate tracking view
SELECT 
    c.FullName, 
    c.Experience_Yrs, 
    j.Title AS Applied_For, 
    a.Status, 
    a.AI_Match_Score
FROM Candidates c
INNER JOIN Applications a ON c.CandidateID = a.CandidateID
INNER JOIN Job_Postings j ON a.JobID = j.JobID
WHERE a.Status = 'Applied' OR a.AI_Match_Score > 30.00
ORDER BY a.AI_Match_Score DESC;

-- procedure to fetch top candidates for a specific job
DELIMITER //
CREATE PROCEDURE GetTopCandidatesForJob(IN target_job_id INT, IN min_score DECIMAL(5,2))
BEGIN
    SELECT 
        c.FullName, 
        c.Email, 
        a.AI_Match_Score, 
        a.Status
    FROM Candidates c
    JOIN Applications a ON c.CandidateID = a.CandidateID
    WHERE a.JobID = target_job_id AND a.AI_Match_Score >= min_score
    ORDER BY a.AI_Match_Score DESC;
END //
DELIMITER ;

-- adding more jobs
INSERT INTO Job_Postings (Title, Job_Description, Required_Skills, Min_Experience) VALUES
('Cloud Architect', 'Design and implement enterprise cloud solutions and migration strategies.', 'AWS, Azure, GCP, Terraform, Kubernetes', 7.0),
('Product Manager', 'Lead cross-functional teams to deliver software products from ideation to launch.', 'Agile, Scrum, Jira, Product Roadmap, Communication', 5.0),
('Cybersecurity Analyst', 'Monitor network traffic for security breaches and investigate violations.', 'Network Security, CEH, Penetration Testing, Firewalls', 3.0),
('Android Developer', 'Build native Android applications using Kotlin and Android SDK.', 'Kotlin, Java, Android Studio, REST APIs', 2.0),
('iOS Developer', 'Develop high-performance iOS applications for iPhone and iPad.', 'Swift, Objective-C, Xcode, CoreData', 2.0),
('Data Engineer', 'Build and maintain scalable ETL pipelines and data warehouses.', 'Apache Spark, Hadoop, SQL, Python, AWS Redshift', 4.0),
('QA Automation Engineer', 'Write automated testing scripts for web and mobile applications.', 'Selenium, Cypress, Java, Python, Appium', 3.0),
('Blockchain Developer', 'Develop smart contracts and decentralized applications (dApps).', 'Solidity, Ethereum, Web3.js, Cryptography', 2.5),
('Marketing Analyst', 'Analyze campaign performance and customer acquisition metrics.', 'Google Analytics, Excel, SQL, Tableau', 1.5),
('Technical Support Specialist', 'Provide L2 support for SaaS enterprise customers.', 'Linux, SQL, Troubleshooting, Ticketing Systems', 1.0);

-- adding more candidates
INSERT INTO Candidates (FullName, Email, Resume_Text, Experience_Yrs) VALUES
('Rajesh Kumar', 'rajesh.k@email.com', 'Senior Cloud Architect with 8 years experience in AWS and Azure. Expert in Terraform and Kubernetes deployments.', 8.0),
('Anjali Desai', 'anjali.d@email.com', 'Product Manager managing Agile teams. Certified Scrum Master. Skilled in Jira and strategic product roadmaps.', 6.0),
('Suresh Menon', 'suresh.m@email.com', 'Ethical hacker and Cybersecurity Analyst. Proficient in penetration testing and configuring enterprise firewalls.', 4.0),
('Pritam Singh', 'pritam.s@email.com', 'Android app developer with 3 years of Kotlin and Java experience. Built scalable e-commerce mobile apps.', 3.0),
('Meghna Patil', 'meghna.p@email.com', 'iOS Swift Developer. Expert in Xcode, UI/UX implementation, and CoreData for offline storage.', 2.5),
('Karthik Iyer', 'karthik.i@email.com', 'Data Engineer specialized in big data. Strong skills in Apache Spark, Python, SQL, and Hadoop clusters.', 5.0),
('Nidhi Sharma', 'nidhi.s@email.com', 'QA Engineer with 4 years in automation testing using Selenium and Cypress. Good Python scripting skills.', 4.0),
('Arjun Nair', 'arjun.n@email.com', 'Blockchain enthusiast and Solidity developer. Built multiple smart contracts on the Ethereum network.', 2.0),
('Sunita Verma', 'sunita.v@email.com', 'Marketing Data Analyst. Expert in Google Analytics, SQL queries, and Tableau visualizations.', 2.0),
('Deepak Chahar', 'deepak.c@email.com', 'Tech support engineer. Resolves L2 customer issues. Good knowledge of Linux commands and basic SQL.', 1.5),
('Ravi Teja', 'ravi.t@email.com', 'Fresher with knowledge of Java and Python. Looking for QA or Dev roles.', 0.0),
('Snehal Kadam', 'snehal.k@email.com', 'AWS Certified Solutions Architect. 5 years of cloud migration experience.', 5.0),
('Varun Dhawan', 'varun.d@email.com', 'Android and iOS developer using Flutter. Good knowledge of Dart and Firebase.', 3.0),
('Pooja Hegde', 'pooja.h@email.com', 'Big Data Engineer. Worked heavily on AWS Redshift and Apache Spark.', 4.5),
('Aman Gupta', 'aman.g@email.com', 'Cybersecurity expert focusing on network security and threat modeling.', 6.0),
('Neha Kakkar', 'neha.k@email.com', 'Scrum Master and Product Owner. Leads 3 different dev teams.', 5.5),
('Kabir Singh', 'kabir.s@email.com', 'Blockchain developer creating Web3.js dApps and DeFi protocols.', 3.5),
('Alia Bhatt', 'alia.b@email.com', 'Automation tester using Java and Selenium. Integrated tests with Jenkins.', 3.0),
('Tiger Shroff', 'tiger.s@email.com', 'IT Support guy. Fixes hardware and software issues. Handles ticketing.', 2.0),
('Shraddha Kapoor', 'shraddha.k@email.com', 'Marketing associate. Uses Excel and basic SQL for reporting.', 1.0),
('Gaurav Taneja', 'gaurav.t@email.com', 'Cloud Engineer with GCP and Azure experience. Knows Kubernetes.', 4.0),
('Bhuvan Bam', 'bhuvan.b@email.com', 'Mobile developer doing native Android with Kotlin.', 2.0),
('Ashish Chanchlani', 'ashish.c@email.com', 'Data Analyst shifting to Data Engineering. Knows Python and SQL well.', 3.0),
('Prajakta Koli', 'prajakta.k@email.com', 'Product management intern. Familiar with Jira and Agile.', 0.5),
('Carry Minati', 'carry.m@email.com', 'Ethical Hacker. CEH certified. Finds bugs and vulnerabilities.', 2.0),
('Amit Bhadana', 'amit.b@email.com', 'Backend developer looking to learn Blockchain. Knows Python.', 2.5),
('Harsh Beniwal', 'harsh.b@email.com', 'QA Manual tester. Trying to learn Selenium automation.', 1.5),
('Zakir Khan', 'zakir.k@email.com', 'Customer Support executive handling L1 tickets.', 1.0),
('Kunal Kamra', 'kunal.k@email.com', 'iOS Dev expert in Objective-C and Swift.', 4.0),
('Munawar Faruqui', 'munawar.f@email.com', 'Digital Marketing Analyst. Great with Tableau and GA.', 3.0);

-- more applications with some bad matches to test ai filtering
INSERT INTO Applications (CandidateID, JobID, Status) VALUES
(16, 9, 'Applied'), (27, 9, 'Applied'), (36, 9, 'Applied'),
(17, 10, 'Applied'), (31, 10, 'Applied'), (39, 10, 'Applied'),
(18, 11, 'Applied'), (30, 11, 'Applied'), (40, 11, 'Applied'),
(19, 12, 'Applied'), (28, 12, 'Applied'), (37, 12, 'Applied'),
(20, 13, 'Applied'), (44, 13, 'Applied'), (28, 13, 'Applied'),
(21, 14, 'Applied'), (29, 14, 'Applied'), (38, 14, 'Applied'),
(22, 15, 'Applied'), (33, 15, 'Applied'), (42, 15, 'Applied'),
(23, 16, 'Applied'), (32, 16, 'Applied'), (41, 16, 'Applied'),
(24, 17, 'Applied'), (35, 17, 'Applied'), (45, 17, 'Applied'),
(25, 18, 'Applied'), (34, 18, 'Applied'), (43, 18, 'Applied'),

-- intentional bad matches
(16, 17, 'Applied'),
(24, 11, 'Applied'),
(34, 12, 'Applied'),
(45, 14, 'Applied'),
(17, 15, 'Applied'),
(33, 10, 'Applied'),
(20, 18, 'Applied'),
(42, 16, 'Applied'),

-- random applications
(26, 15, 'Applied'), (27, 12, 'Applied'), (28, 10, 'Applied'),
(29, 9, 'Applied'), (30, 14, 'Applied'), (31, 11, 'Applied'),
(32, 17, 'Applied'), (33, 9, 'Applied'), (34, 16, 'Applied'),
(35, 13, 'Applied'), (36, 18, 'Applied'), (37, 15, 'Applied');

SELECT * FROM Candidates;

-- dcl: naya user banakar permission dena
CREATE USER 'recruiter_demo'@'localhost' IDENTIFIED BY 'password123';
GRANT SELECT, INSERT, UPDATE ON Internship_Management.Applications TO 'recruiter_demo'@'localhost';
-- REVOKE UPDATE ON Internship_Management.Applications FROM 'recruiter_demo'@'localhost'; 

-- tcl: safe data entry ke liye transaction
START TRANSACTION;

INSERT INTO Candidates (FullName, Email, Resume_Text, Experience_Yrs) 
VALUES ('Test User', 'test@demo.com', 'Testing TCL transaction', 1.0);

-- backup point
SAVEPOINT BeforeApplication;

INSERT INTO Applications (CandidateID, JobID, Status) 
VALUES (LAST_INSERT_ID(), 1, 'Applied');

-- data permanently save karna
COMMIT; 
-- ROLLBACK; -- agar error aaye toh ye run karna