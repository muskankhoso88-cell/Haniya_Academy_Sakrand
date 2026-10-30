import os
from datetime import date
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app, send_from_directory, abort
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from app.models import (
    db, Teacher, TeacherCourse, Course, Material, Attendance,
    Student, Enrollment
)

teacher_bp = Blueprint("teacher", __name__)


def teacher_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Teacher):
            return redirect(url_for("teacher.login"))
        return view(*args, **kwargs)

    return wrapped


@teacher_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        teacher = Teacher.query.filter_by(username=username, is_active=True).first()
        if teacher and check_password_hash(teacher.password_hash, password):
            login_user(teacher)
            return redirect(url_for("teacher.dashboard"))
        flash("Invalid credentials.", "error")
    return render_template("teacher/login.html")


@teacher_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("teacher.login"))


@teacher_bp.route("/")
@teacher_required
def dashboard():
    # A teacher only ever manages the courses assigned to them via the
    # teacher_courses junction table — this is application-level access
    # control layered on top of the M:N relationship in the database.
    assigned = TeacherCourse.query.filter_by(teacher_id=current_user.teacher_id).all()
    courses = [tc.course for tc in assigned]
    materials = Material.query.filter_by(teacher_id=current_user.teacher_id).order_by(Material.uploaded_at.desc()).all()
    return render_template("teacher/dashboard.html", courses=courses, materials=materials)


@teacher_bp.route("/materials/upload", methods=["POST"])
@teacher_required
def upload_material():
    course_id = request.form.get("course_id")
    title = request.form.get("title", "").strip()
    file = request.files.get("file")

    # Confirm this teacher is actually assigned to the course they're
    # uploading for (prevents uploading into someone else's course).
    assigned = TeacherCourse.query.filter_by(teacher_id=current_user.teacher_id, course_id=course_id).first()
    if not assigned:
        flash("You are not assigned to that course.", "error")
        return redirect(url_for("teacher.dashboard"))

    if not title or not file or file.filename == "":
        flash("Title and a file are required.", "error")
        return redirect(url_for("teacher.dashboard"))

    filename = secure_filename(file.filename)
    # Prefix with teacher id + timestamp-ish counter to avoid filename collisions
    stored_name = f"{current_user.teacher_id}_{int(date.today().strftime('%Y%m%d'))}_{filename}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
    file.save(save_path)

    db.session.add(Material(
        teacher_id=current_user.teacher_id,
        course_id=course_id,
        title=title,
        file_path=stored_name,
        original_filename=filename,
    ))
    db.session.commit()
    flash("Material uploaded.", "success")
    return redirect(url_for("teacher.dashboard"))


@teacher_bp.route("/materials/<int:material_id>/delete", methods=["POST"])
@teacher_required
def delete_material(material_id):
    material = Material.query.filter_by(material_id=material_id, teacher_id=current_user.teacher_id).first_or_404()
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], material.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)
    db.session.delete(material)
    db.session.commit()
    flash("Material removed.", "success")
    return redirect(url_for("teacher.dashboard"))


@teacher_bp.route("/attendance/<int:course_id>", methods=["GET", "POST"])
@teacher_required
def attendance(course_id):
    assigned = TeacherCourse.query.filter_by(teacher_id=current_user.teacher_id, course_id=course_id).first()
    if not assigned:
        abort(403)

    course = Course.query.get_or_404(course_id)

    if request.method == "POST":
        attendance_date = request.form.get("attendance_date") or date.today().isoformat()
        student_ids = request.form.getlist("student_id")
        for sid in student_ids:
            status = request.form.get(f"status_{sid}", "present")
            existing = Attendance.query.filter_by(
                student_id=sid, course_id=course_id, attendance_date=attendance_date
            ).first()
            if existing:
                existing.status = status  # update if already marked for that date
            else:
                db.session.add(Attendance(
                    student_id=sid, course_id=course_id,
                    teacher_id=current_user.teacher_id,
                    attendance_date=attendance_date, status=status,
                ))
        db.session.commit()
        flash("Attendance saved.", "success")
        return redirect(url_for("teacher.attendance", course_id=course_id))

    # Only active, confirmed students enrolled in this course are shown —
    # inactive (soft-deleted) students are automatically excluded.
    enrollments = (
        Enrollment.query.join(Student)
        .filter(Enrollment.course_id == course_id, Student.is_active == True)
        .all()
    )
    return render_template("teacher/attendance.html", course=course, enrollments=enrollments, today=date.today().isoformat())


@teacher_bp.route("/materials/<int:material_id>/download")
@login_required
def download_material(material_id):
    """Serves the actual file. Works for the uploading teacher AND for
    any student enrolled in that course — checked below rather than
    trusting the URL alone."""
    material = Material.query.get_or_404(material_id)

    allowed = False
    if isinstance(current_user, Teacher) and material.teacher_id == current_user.teacher_id:
        allowed = True
    elif isinstance(current_user, Student):
        enrolled = Enrollment.query.filter_by(
            student_id=current_user.student_id, course_id=material.course_id
        ).first()
        if enrolled:
            allowed = True

    if not allowed:
        abort(403)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        material.file_path,
        as_attachment=True,
        download_name=material.original_filename or material.file_path,
    )
