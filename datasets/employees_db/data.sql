-- Data for the 'employees_db' dataset

INSERT INTO employees (id, first_name, last_name, department, salary) VALUES
(1, 'Alice', 'Smith', 'Engineering', 120000),
(2, 'Bob', 'Johnson', 'Sales', 80000),
(3, 'Charlie', 'Brown', 'Engineering', 110000),
(4, 'David', 'Lee', 'Marketing', 75000),
(5, 'Eve', 'Davis', 'Sales', 82000);

INSERT INTO projects (id, project_name, manager_id) VALUES
(101, 'Apollo Launch', 1),
(102, 'Sales Portal', 2),
(103, 'Data Pipeline', 3);