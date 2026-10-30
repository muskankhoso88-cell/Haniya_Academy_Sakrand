from datetime import date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    """One row = one admin login. UserMixin gives Flask-Login the
    is_authenticated / get_id() behaviour it needs."""
    __tablename__ = "admins"

    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def get_id(self):
        # Flask-Login needs a unique string id; we prefix so it never
        # collides with a Student id in the same login session system.
        return f"admin-{self.admin_id}"


class Course(db.Model):
    __tablename__ = "courses"

    course_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.String(50))
    fee = db.Column(db.Numeric(10, 2), default=0)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    enrollments = db.relationship("Enrollment", backref="course", cascade="all, delete-orphan")


class Faculty(db.Model):
    __tablename__ = "faculty"

    faculty_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    designation = db.Column(db.String(150))
    subject = db.Column(db.String(100))
    photo_url = db.Column(db.String(255))
    bio = db.Column(db.Text)
    display_order = db.Column(db.Integer, default=0)


class Achiever(db.Model):
    __tablename__ = "achievers"

    achiever_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    score = db.Column(db.String(50))
    year = db.Column(db.Integer)
    photo_url = db.Column(db.String(255))
    display_order = db.Column(db.Integer, default=0)


class GalleryImage(db.Model):
    __tablename__ = "gallery"

    image_id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(200))
    display_order = db.Column(db.Integer, default=0)


class Student(UserMixin, db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(30), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    father_name = db.Column(db.String(150))
    cnic_bform = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    enrollments = db.relationship("Enrollment", backref="student", cascade="all, delete-orphan")
    results = db.relationship("Result", backref="student", cascade="all, delete-orphan")

    def get_id(self):
        return f"student-{self.student_id}"


class Enrollment(db.Model):
    """Junction table implementing the many-to-many relationship
    between Student and Course. This is the classic DBMS example of
    resolving an M:N relationship with an associative entity."""
    __tablename__ = "enrollments"

    enrollment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    enrollment_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.Enum("pending", "confirmed", "rejected", name="enrollment_status"), default="pending")

    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", name="uq_student_course"),
    )


class Result(db.Model):
    __tablename__ = "results"

    result_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id", ondelete="SET NULL"))
    test_name = db.Column(db.String(150), nullable=False)
    marks_obtained = db.Column(db.Numeric(6, 2))
    total_marks = db.Column(db.Numeric(6, 2))
    result_date = db.Column(db.Date)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    message_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, server_default=db.func.now())
    is_read = db.Column(db.Boolean, default=False)


class Teacher(UserMixin, db.Model):
    __tablename__ = "teachers"

    teacher_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    courses = db.relationship("TeacherCourse", backref="teacher", cascade="all, delete-orphan")
    materials = db.relationship("Material", backref="teacher", cascade="all, delete-orphan")

    def get_id(self):
        return f"teacher-{self.teacher_id}"


class TeacherCourse(db.Model):
    """Junction table: which teacher teaches which course. Same M:N
    pattern as Enrollment (students<->courses)."""
    __tablename__ = "teacher_courses"

    teacher_course_id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.teacher_id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)

    course = db.relationship("Course")

    __table_args__ = (
        db.UniqueConstraint("teacher_id", "course_id", name="uq_teacher_course"),
    )


class Material(db.Model):
    """A file a teacher uploads for a course. Any enrolled student can
    see + download it from their dashboard."""
    __tablename__ = "materials"

    material_id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.teacher_id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())

    course = db.relationship("Course")


class Attendance(db.Model):
    """One row per student, per course, per day."""
    __tablename__ = "attendance"

    attendance_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.teacher_id", ondelete="CASCADE"), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum("present", "absent", "leave", name="attendance_status"), default="present")

    course = db.relationship("Course")

    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", "attendance_date", name="uq_student_course_date"),
    )
