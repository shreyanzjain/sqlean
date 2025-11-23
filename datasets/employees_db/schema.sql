-- Schema for the 'employees_db' dataset

CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    department TEXT,
    salary INTEGER
);

CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    project_name TEXT NOT NULL,
    manager_id INTEGER
);