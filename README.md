# Haniya Academy Sakrand — Full-Stack Project (Flask + MySQL)

This project turns the original static `haniya_academy_complete.html` page into a
real full-stack application, backed by a MySQL database, so it can double as a
**hands-on DBMS learning project**.

## 1. Project Structure

```
haniya_academy_app/
├── schema.sql              # MySQL schema (heavily commented with DBMS concepts)
├── seed_data.py             # Inserts a default admin login + sample data
├── run.py                   # App entry point
├── config.py                # DB connection settings (reads from .env)
├── .env.example             # Copy to .env and fill in your MySQL credentials
├── requirements.txt
└── app/
    ├── __init__.py           # App factory + Flask-Login setup
    ├── models.py             # SQLAlchemy ORM models (mirrors schema.sql)
    ├── routes/
    │   ├── public.py         # Home page, enroll form, contact form
    │   ├── admin.py          # Admin login + CRUD for courses/faculty/etc.
    │   └── portal.py         # Student portal login + dashboard
    ├── templates/            # Jinja2 templates (converted from your HTML)
    └── static/css/style.css  # Extracted from your original file
```

## 2. Setup Instructions

### a) Install MySQL and create the database
```bash
sudo apt install mysql-server         # if not already installed
sudo mysql -u root -p < schema.sql    # creates the `haniya_academy` database + tables
```

### b) Python environment
```bash
cd haniya_academy_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### c) Configure database credentials
```bash
cp .env.example .env
# edit .env and set DB_USER / DB_PASSWORD to your MySQL login
```

### d) Seed initial data (admin login + sample content)
```bash
python seed_data.py
```
Default logins:
- **Admin** — username: `admin` / password: `admin123`
- **Teacher** — username: `teacher1` / password: `teacher123`

Change these immediately in production.

### e) Run the app
```bash
python run.py
```
Visit `http://localhost:5000` for the public site, `/admin/login` for the admin
panel, `/portal/login` for the student portal, and `/teacher/login` for the
teacher dashboard.

## 3.5 New Features (Teacher/Student portals, Attendance, Soft Delete)

- **Teacher dashboard** (`/teacher/login`) — a teacher only sees the courses
  assigned to them (via `teacher_courses`), can upload any file type as
  course material, and marks daily attendance for enrolled students.
- **Student dashboard** now also shows attendance percentage per course,
  a list of teacher-shared materials (downloadable), and a downloadable
  result slip per test.
- **Soft delete** — Admin → Manage Students → "Mark Inactive" flips
  `students.is_active` to `FALSE` instead of running `DELETE`. The student's
  results, attendance, and enrollment history all stay in the database;
  they just lose portal login access and disappear from active lists.
  "Reactivate" flips it back.
- **File downloads are access-controlled** — a student can only download
  materials for courses they're enrolled in; a teacher can only manage
  their own uploads. This is enforced in `app/routes/teacher.py`, not just
  by hiding the link in the UI.

## 3. DBMS Concepts Applied (your learning reference)

This project was built specifically to demonstrate these concepts in a real app:

| Concept | Where it's used |
|---|---|
| **Primary Keys** | Every table has an auto-incrementing PK (`course_id`, `student_id`, etc.) |
| **Foreign Keys / Referential Integrity** | `enrollments` and `results` reference `students` and `courses`; deleting a student cascades to their enrollments |
| **Many-to-Many via Junction Table** | `enrollments` resolves the M:N relationship between `students` and `courses` — a classic normalization pattern |
| **Normalization (1NF/2NF/3NF)** | Student info isn't duplicated per-course; course info isn't duplicated per-student — each fact lives in exactly one place |
| **Constraints** | `UNIQUE` on `roll_number` and `username`; `NOT NULL` on required fields; `UNIQUE(student_id, course_id)` prevents duplicate enrollment |
| **Indexes** | Added on `enrollments.status`, `results.student_id`, `students.email` for faster lookups |
| **Transactions (ACID)** | The enrollment route (`app/routes/public.py`) wraps student-creation + enrollment-creation in one transaction — either both succeed or both roll back |
| **Data types** | `DECIMAL` for money (never `FLOAT`, which loses precision), `ENUM` for a fixed set of statuses, `TIMESTAMP` for audit fields |
| **Application-level access control** | The student portal filters `Result.query.filter_by(student_id=current_user.student_id)` so a student can only ever see their own data — security enforced both by the query and by the login system |
| **A second Many-to-Many relationship** | `teacher_courses` links teachers to courses, exactly like `enrollments` links students to courses — same normalization pattern reused |
| **Composite UNIQUE constraint** | `attendance` has `UNIQUE(student_id, course_id, attendance_date)` so a teacher can't accidentally create two attendance rows for the same student on the same day |
| **Soft delete pattern** | `students.is_active` / `teachers.is_active` "remove" someone from active use without ever running `DELETE`, preserving all historical foreign-key relationships |

### Suggested next steps to deepen your DBMS mastery
1. Open a MySQL client and run raw `SELECT`, `JOIN`, and `GROUP BY` queries directly
   against the tables Flask created — e.g. "how many students enrolled per course?"
2. Try breaking a foreign key constraint on purpose (delete a course while students
   are enrolled in it) and observe the error — that's referential integrity working.
3. Add an index, run `EXPLAIN` on a slow query, and see how the query plan changes.
4. Extend `results` with a `GROUP BY course_id` report showing average marks per course.

## 4. This has been tested end-to-end (not just written — actually run)
Before packaging, this exact codebase was run with a real MySQL database and verified:
- Home page renders courses/faculty pulled live from the database
- Admin login → dashboard → adding a course → course appears on the public site
- Public enrollment form → creates a student row + enrollment row in the database
- Student portal login (with the just-created account) → shows their enrollment
All of the above returned correct results against a real MySQL instance.

## 5. Deployment

### Option A — Docker (recommended, easiest, works on any VPS)
This starts MySQL + the app together with one command:
```bash
docker compose up --build
```
Visit `http://your-server-ip:5000`. Change `DB_PASSWORD` and `SECRET_KEY` in a
`.env` file next to `docker-compose.yml` before going live.

### Option B — Render.com (free tier, no server management)
1. Push this project to a GitHub repo.
2. On Render: New → Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT run:app` (already in `Procfile`, Render auto-detects it)
5. Add a Render **MySQL** or **PostgreSQL** add-on (if Postgres, swap `PyMySQL` for `psycopg2-binary`
   and update `SQLALCHEMY_DATABASE_URI` in `config.py` accordingly), or point `DB_HOST` etc.
   at an external MySQL host (e.g. PlanetScale, Railway, Aiven — all have free MySQL tiers).
6. Set environment variables `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `SECRET_KEY` in Render's dashboard.
7. Run `schema.sql` against that database once, then run `python seed_data.py` from Render's shell.

### Option C — Railway.app
1. Push to GitHub, then New Project → Deploy from repo.
2. Add a MySQL plugin (Railway provisions one with connection env vars automatically).
3. Map Railway's provided `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLHOST`, `MYSQLPORT`, `MYSQLDATABASE`
   to this app's `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` in the service's Variables tab.
4. Railway auto-detects `Procfile` and runs it.
5. Open the MySQL plugin's console, paste in `schema.sql`, then run `python seed_data.py` via Railway's shell.

### Option D — PythonAnywhere (simple, good for students/free tier)
1. Upload the project (or `git clone` it) in a Bash console.
2. Create a MySQL database from the "Databases" tab (PythonAnywhere gives you the host/user already).
3. `pip install -r requirements.txt` inside a virtualenv.
4. Fill in `.env` with the DB details PythonAnywhere gave you, then run `schema.sql` and `seed_data.py`.
5. In the "Web" tab, create a new Flask web app pointing at `run.py` / the `app` object.

**Whichever option you pick:** change the default admin password (`admin123`) and set a real
random `SECRET_KEY` before making the site public.

## 6. What's still a placeholder
- `app/static/images/logo.jpg` and `placeholder.jpg` are solid-color placeholders —
  replace them with your real photos (the originals were huge inline base64 images
  not practical to re-embed here).
- Add more admin templates/routes as needed (edit forms currently only support add/delete).
