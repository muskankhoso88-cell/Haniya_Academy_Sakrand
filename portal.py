from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from app.models import Student, Result, Enrollment, Attendance, Material

portal_bp = Blueprint("portal", __name__)


def student_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Student):
            return redirect(url_for("portal.login"))
        return view(*args, **kwargs)

    return wrapped


@portal_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        roll_number = request.form.get("roll_number", "").strip()
        password = request.form.get("password", "")
        student = Student.query.filter_by(roll_number=roll_number).first()
        if not student or not check_password_hash(student.password_hash, password):
            flash("Invalid roll number or password.", "error")
        elif not student.is_active:
            # Soft-deleted students can no longer log in, but their
            # historical data (results, attendance) is untouched in the DB.
            flash("This account has been marked inactive. Contact the academy office.", "error")
        else:
            login_user(student)
            return redirect(url_for("portal.dashboard"))
    return render_template("portal/login.html")


@portal_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("portal.login"))


@portal_bp.route("/")
@student_required
def dashboard():
    # A student only ever sees their OWN rows — filtered by student_id —
    # this is the application-level access control layered on top of the DB.
    results = Result.query.filter_by(student_id=current_user.student_id).order_by(Result.result_date.desc()).all()
    enrollments = Enrollment.query.filter_by(student_id=current_user.student_id).all()

    # Attendance summary per enrolled course: count present vs total marked days.
    attendance_summary = []
    for e in enrollments:
        records = Attendance.query.filter_by(student_id=current_user.student_id, course_id=e.course_id).all()
        total = len(records)
        present = len([r for r in records if r.status == "present"])
        percentage = round((present / total) * 100, 1) if total else None
        attendance_summary.append({
            "course": e.course,
            "total": total,
            "present": present,
            "percentage": percentage,
        })

    # Materials shared by teachers, for every course this student is enrolled in.
    course_ids = [e.course_id for e in enrollments]
    materials = Material.query.filter(Material.course_id.in_(course_ids)).order_by(Material.uploaded_at.desc()).all() if course_ids else []

    return render_template(
        "portal/dashboard.html",
        results=results,
        enrollments=enrollments,
        attendance_summary=attendance_summary,
        materials=materials,
    )


@portal_bp.route("/results/<int:result_id>/download")
@student_required
def download_result(result_id):
    """Generates a simple text summary of one result the student can save.
    Only the owning student can download their own result — checked below."""
    result = Result.query.get_or_404(result_id)
    if result.student_id != current_user.student_id:
        flash("You can only download your own results.", "error")
        return redirect(url_for("portal.dashboard"))

    content = (
        f"Haniya Academy Sakrand — Result Slip\n"
        f"{'-'*40}\n"
        f"Student Name : {current_user.full_name}\n"
        f"Roll Number  : {current_user.roll_number}\n"
        f"Test Name    : {result.test_name}\n"
        f"Marks Obtained: {result.marks_obtained}\n"
        f"Total Marks  : {result.total_marks}\n"
        f"Date         : {result.result_date}\n"
    )
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename=result_{result.result_id}.txt"},
    )
