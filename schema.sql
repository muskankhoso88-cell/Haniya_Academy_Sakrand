-- =====================================================================
-- HANIYA ACADEMY SAKRAND — DATABASE SCHEMA
-- =====================================================================
-- This file is written to double as a DBMS learning reference.
-- Every design choice below demonstrates a real DBMS concept:
--   - Normalization (1NF/2NF/3NF)
--   - Primary Keys / Foreign Keys / Referential Integrity
--   - Indexes for query performance
--   - Constraints (NOT NULL, UNIQUE, CHECK, DEFAULT)
--   - Appropriate data types
-- =====================================================================

CREATE DATABASE IF NOT EXISTS haniya_academy
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE haniya_academy;

-- ---------------------------------------------------------------------
-- 1. ADMINS
-- One admin account manages the whole backend (courses, faculty, etc.)
-- Passwords are NEVER stored in plain text — only a hash (see app code).
-- ---------------------------------------------------------------------
CREATE TABLE admins (
    admin_id      INT AUTO_INCREMENT PRIMARY KEY,   -- Primary Key: uniquely identifies a row
    username      VARCHAR(50)  NOT NULL UNIQUE,      -- UNIQUE constraint prevents duplicate logins
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- 2. COURSES
-- Represents "Our Programs" section of the site.
-- ---------------------------------------------------------------------
CREATE TABLE courses (
    course_id     INT AUTO_INCREMENT PRIMARY KEY,
    title         VARCHAR(150) NOT NULL,
    description   TEXT,
    duration      VARCHAR(50),
    fee           DECIMAL(10,2) DEFAULT 0.00,        -- DECIMAL for exact money values (never FLOAT)
    display_order INT DEFAULT 0,                      -- controls ordering on the public page
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- 3. FACULTY
-- Represents "Our Faculty" section.
-- ---------------------------------------------------------------------
CREATE TABLE faculty (
    faculty_id    INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(150) NOT NULL,
    designation   VARCHAR(150),
    subject       VARCHAR(100),
    photo_url     VARCHAR(255),
    bio           TEXT,
    display_order INT DEFAULT 0
);

-- ---------------------------------------------------------------------
-- 4. ACHIEVERS
-- "Top MDCAT Achievers" section.
-- ---------------------------------------------------------------------
CREATE TABLE achievers (
    achiever_id   INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(150) NOT NULL,
    score         VARCHAR(50),
    year          YEAR,
    photo_url     VARCHAR(255),
    display_order INT DEFAULT 0
);

-- ---------------------------------------------------------------------
-- 5. GALLERY
-- "Academy Gallery" section.
-- ---------------------------------------------------------------------
CREATE TABLE gallery (
    image_id      INT AUTO_INCREMENT PRIMARY KEY,
    image_url     VARCHAR(255) NOT NULL,
    caption       VARCHAR(200),
    display_order INT DEFAULT 0
);

-- ---------------------------------------------------------------------
-- 6. STUDENTS
-- Core entity for the Student Portal. Separated from "enrollments"
-- (a student may enroll in multiple courses over time — this avoids
-- repeating student data — a 2NF/3NF normalization decision).
-- ---------------------------------------------------------------------
CREATE TABLE students (
    student_id     INT AUTO_INCREMENT PRIMARY KEY,
    roll_number    VARCHAR(30) NOT NULL UNIQUE,       -- used as portal login ID
    full_name      VARCHAR(150) NOT NULL,
    father_name    VARCHAR(150),
    cnic_bform     VARCHAR(20),
    phone          VARCHAR(20),
    email          VARCHAR(150),
    password_hash  VARCHAR(255) NOT NULL,             -- for student portal login
    is_active      BOOLEAN DEFAULT TRUE,              -- SOFT DELETE flag: instead of
                                                       -- destroying a row (hard delete),
                                                       -- we flip this to FALSE. Data stays
                                                       -- safe for records/history, but the
                                                       -- student disappears from active lists.
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- 7. ENROLLMENTS
-- A junction/associative table implementing the Many-to-Many
-- relationship between STUDENTS and COURSES.
-- This is a textbook DBMS normalization example: instead of storing
-- course info repeatedly per student (redundant), we link via IDs.
-- ---------------------------------------------------------------------
CREATE TABLE enrollments (
    enrollment_id   INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT NOT NULL,
    course_id       INT NOT NULL,
    enrollment_date DATE DEFAULT (CURRENT_DATE),
    status          ENUM('pending','confirmed','rejected') DEFAULT 'pending',

    -- FOREIGN KEYS enforce referential integrity:
    -- you cannot enroll a student_id or course_id that doesn't exist,
    -- and ON DELETE CASCADE keeps data consistent if a parent row is removed.
    CONSTRAINT fk_enroll_student FOREIGN KEY (student_id)
        REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_enroll_course FOREIGN KEY (course_id)
        REFERENCES courses(course_id) ON DELETE CASCADE,

    UNIQUE KEY uq_student_course (student_id, course_id)  -- prevents duplicate enrollment in same course
);

-- ---------------------------------------------------------------------
-- 8. RESULTS
-- Linked to a student (and optionally a course) — viewed via the portal.
-- ---------------------------------------------------------------------
CREATE TABLE results (
    result_id     INT AUTO_INCREMENT PRIMARY KEY,
    student_id    INT NOT NULL,
    course_id     INT,
    test_name     VARCHAR(150) NOT NULL,
    marks_obtained DECIMAL(6,2),
    total_marks    DECIMAL(6,2),
    result_date    DATE,

    CONSTRAINT fk_result_student FOREIGN KEY (student_id)
        REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_result_course FOREIGN KEY (course_id)
        REFERENCES courses(course_id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- 9. CONTACT MESSAGES
-- "Contact Us" form submissions.
-- ---------------------------------------------------------------------
CREATE TABLE contact_messages (
    message_id  INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(150) NOT NULL,
    email       VARCHAR(150),
    phone       VARCHAR(20),
    message     TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read     BOOLEAN DEFAULT FALSE
);

-- ---------------------------------------------------------------------
-- 10. TEACHERS
-- Each teacher gets a login and is linked to the course(s) they teach
-- through the teacher_courses junction table (another M:N relationship,
-- same pattern as students<->courses via `enrollments`).
-- ---------------------------------------------------------------------
CREATE TABLE teachers (
    teacher_id    INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(150) NOT NULL,
    username      VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    subject       VARCHAR(100),
    phone         VARCHAR(20),
    email         VARCHAR(150),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- 11. TEACHER_COURSES
-- Junction table: which teacher teaches which course(s).
-- ---------------------------------------------------------------------
CREATE TABLE teacher_courses (
    teacher_course_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id        INT NOT NULL,
    course_id         INT NOT NULL,

    CONSTRAINT fk_tc_teacher FOREIGN KEY (teacher_id)
        REFERENCES teachers(teacher_id) ON DELETE CASCADE,
    CONSTRAINT fk_tc_course FOREIGN KEY (course_id)
        REFERENCES courses(course_id) ON DELETE CASCADE,

    UNIQUE KEY uq_teacher_course (teacher_id, course_id)
);

-- ---------------------------------------------------------------------
-- 12. MATERIALS
-- Notes/files a teacher uploads for a specific course. Students enrolled
-- in that course can see and download them from their dashboard.
-- ---------------------------------------------------------------------
CREATE TABLE materials (
    material_id   INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id    INT NOT NULL,
    course_id     INT NOT NULL,
    title         VARCHAR(200) NOT NULL,
    file_path     VARCHAR(255) NOT NULL,   -- where the uploaded file is stored on disk
    original_filename VARCHAR(255),
    uploaded_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_material_teacher FOREIGN KEY (teacher_id)
        REFERENCES teachers(teacher_id) ON DELETE CASCADE,
    CONSTRAINT fk_material_course FOREIGN KEY (course_id)
        REFERENCES courses(course_id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- 13. ATTENDANCE
-- One row per student, per course, per day. UNIQUE constraint stops a
-- teacher from accidentally marking the same student twice on one date.
-- ---------------------------------------------------------------------
CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id    INT NOT NULL,
    course_id     INT NOT NULL,
    teacher_id    INT NOT NULL,
    attendance_date DATE NOT NULL,
    status        ENUM('present','absent','leave') NOT NULL DEFAULT 'present',

    CONSTRAINT fk_att_student FOREIGN KEY (student_id)
        REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_att_course FOREIGN KEY (course_id)
        REFERENCES courses(course_id) ON DELETE CASCADE,
    CONSTRAINT fk_att_teacher FOREIGN KEY (teacher_id)
        REFERENCES teachers(teacher_id) ON DELETE CASCADE,

    UNIQUE KEY uq_student_course_date (student_id, course_id, attendance_date)
);

-- ---------------------------------------------------------------------
-- INDEXES
-- Added on columns we will frequently search/filter/join on.
-- Primary/Unique keys already create indexes automatically; these are
-- additional ones for common lookup patterns.
-- ---------------------------------------------------------------------
CREATE INDEX idx_enrollment_status ON enrollments(status);
CREATE INDEX idx_results_student   ON results(student_id);
CREATE INDEX idx_students_email    ON students(email);
CREATE INDEX idx_students_active   ON students(is_active);
CREATE INDEX idx_attendance_lookup ON attendance(student_id, course_id, attendance_date);
CREATE INDEX idx_materials_course  ON materials(course_id);

-- =====================================================================
-- WHY THIS DESIGN? (quick DBMS notes)
-- =====================================================================
-- 1NF: every column holds a single atomic value (no comma-separated lists).
-- 2NF: no partial dependency on part of a composite key (enrollments
--      depends on the whole student_id+course_id pair, not just one).
-- 3NF: non-key columns don't depend on other non-key columns
--      (e.g. student's course info isn't duplicated inside students table).
-- Referential integrity: FOREIGN KEY constraints stop "orphan" rows —
--      e.g. you cannot have an enrollment pointing to a deleted student.
-- Transactions (ACID): when the app enrolls a student AND creates a
--      result placeholder together, both operations will be wrapped in
--      a transaction so either both succeed or both roll back.
-- Soft delete: `students.is_active` and `teachers.is_active` let the app
--      "remove" a person from active use without ever running DELETE —
--      historical results, attendance, and enrollments stay intact and
--      queryable, which is usually what real institutions need.
