-- =====================================================
--  Library Management System - Database Schema (MySQL)
--  Run:  mysql -u root -p < schema.sql
-- =====================================================

DROP DATABASE IF EXISTS library_db;
CREATE DATABASE library_db;
USE library_db;

-- 1. BOOKS : every book title the library owns
CREATE TABLE books (
    book_id     INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(150) NOT NULL,
    author      VARCHAR(100) NOT NULL,
    category    VARCHAR(50),
    quantity    INT NOT NULL DEFAULT 1,          -- total copies owned
    available   INT NOT NULL DEFAULT 1,          -- copies on the shelf right now
    CHECK (quantity >= 0),
    CHECK (available >= 0 AND available <= quantity)
);

-- 2. MEMBERS : people who can borrow books
CREATE TABLE members (
    member_id   INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    phone       VARCHAR(15),
    joined_on   DATE NOT NULL DEFAULT (CURRENT_DATE)
);

-- 3. ISSUES : which member borrowed which book, and when
--    (links BOOKS and MEMBERS -> many-to-many relationship)
CREATE TABLE issues (
    issue_id    INT AUTO_INCREMENT PRIMARY KEY,
    book_id     INT NOT NULL,
    member_id   INT NOT NULL,
    issue_date  DATE NOT NULL,
    due_date    DATE NOT NULL,
    return_date DATE NULL,                       -- NULL = not returned yet
    FOREIGN KEY (book_id)   REFERENCES books(book_id)     ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE
);

-- ---------- Sample data ----------
INSERT INTO books (title, author, category, quantity, available) VALUES
('Database System Concepts', 'Silberschatz, Korth, Sudarshan', 'Computer Science', 5, 4),
('Let Us C',                 'Yashavant Kanetkar',             'Programming',      3, 3),
('Python Crash Course',      'Eric Matthes',                   'Programming',      4, 3),
('The Alchemist',            'Paulo Coelho',                   'Fiction',          2, 2),
('Wings of Fire',            'A. P. J. Abdul Kalam',           'Biography',        3, 3);

INSERT INTO members (name, email, phone, joined_on) VALUES
('Rahul Sharma', 'rahul@example.com', '9876543210', '2026-07-01'),
('Priya Patel',  'priya@example.com', '9123456780', '2026-07-15'),
('Amit Kumar',   'amit@example.com',  '9988776655', '2026-08-02');

INSERT INTO issues (book_id, member_id, issue_date, due_date, return_date) VALUES
(1, 1, '2026-11-10', '2026-11-24', NULL),
(3, 2, '2026-11-15', '2026-11-29', NULL),
(2, 3, '2026-10-20', '2026-11-03', '2026-11-01');
