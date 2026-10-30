from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import db, Admin, Course, Faculty, Achiever, GalleryImage, ContactMessage, Enrollment, Teacher, TeacherCourse, Student, Result

admin_bp = Blueprint("admin", __name__)


def admin_required(view):
    """Small guard so student logins can't reach admin pages, even
    though both use Flask-Login."""
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admin):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for("admin.dashboard"))
        flash("Invalid credentials.", "error")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "courses": Course.query.count(),
        "faculty": Faculty.query.count(),
        "achievers": Achiever.query.count(),
        "gallery": GalleryImage.query.count(),
        "pending_enrollments": Enrollment.query.filter_by(status="pending").count(),
        "unread_messages": ContactMessage.query.filter_by(is_read=False).count(),
        "active_students": Student.query.filter_by(is_active=True).count(),
        "teachers": Teacher.query.filter_by(is_active=True).count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


# ---------- Generic CRUD pattern reused for Courses / Faculty / Achievers / Gallery ----------

@admin_bp.route("/courses")
@admin_required
def courses_list():
    courses = Course.query.order_by(Course.display_order).all()
    return render_template("admin/courses.html", courses=courses)


@admin_bp.route("/courses/add", methods=["POST"])
@admin_required
def courses_add():
    db.session.add(Course(
        title=request.form["title"],
        description=request.form.get("description", ""),
        duration=request.form.get("duration", ""),
        fee=request.form.get("fee") or 0,
        display_order=request.form.get("display_order") or 0,
    ))
    db.session.commit()
    flash("Course added.", "success")
    return redirect(url_for("admin.courses_list"))


@admin_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@admin_required
def courses_delete(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course removed.", "success")
    return redirect(url_for("admin.courses_list"))


@admin_bp.route("/faculty")
@admin_required
def faculty_list():
    faculty = Faculty.query.order_by(Faculty.display_order).all()
    return render_template("admin/faculty.html", faculty=faculty)


@admin_bp.route("/faculty/add", methods=["POST"])
@admin_required
def faculty_add():
    db.session.add(Faculty(
        full_name=request.form["full_name"],
        designation=request.form.get("designation", ""),
        subject=request.form.get("subject", ""),
        photo_url=request.form.get("photo_url", ""),
        bio=request.form.get("bio", ""),
        display_order=request.form.get("display_order") or 0,
    ))
    db.session.commit()
    flash("Faculty member added.", "success")
    return redirect(url_for("admin.faculty_list"))


@admin_bp.route("/faculty/<int:faculty_id>/delete", methods=["POST"])
@admin_required
def faculty_delete(faculty_id):
    member = Faculty.query.get_or_404(faculty_id)
    db.session.delete(member)
    db.session.commit()
    flash("Faculty member removed.", "success")
    return redirect(url_for("admin.faculty_list"))


@admin_bp.route("/achievers")
@admin_required
def achievers_list():
    achievers = Achiever.query.order_by(Achiever.display_order).all()
    return render_template("admin/achievers.html", achievers=achievers)


@admin_bp.route("/achievers/add", methods=["POST"])
@admin_required
def achievers_add():
    db.session.add(Achiever(
        full_name=request.form["full_name"],
        score=request.form.get("score", ""),
        year=request.form.get("year") or None,
        photo_url=request.form.get("photo_url", ""),
        display_order=request.form.get("display_order") or 0,
    ))
    db.session.commit()
    flash("Achiever added.", "success")
    return redirect(url_for("admin.achievers_list"))


@admin_bp.route("/achievers/<int:achiever_id>/delete", methods=["POST"])
@admin_required
def achievers_delete(achiever_id):
    achiever = Achiever.query.get_or_404(achiever_id)
    db.session.delete(achiever)
    db.session.commit()
    flash("Achiever removed.", "success")
    return redirect(url_for("admin.achievers_list"))


@admin_bp.route("/gallery")
@admin_required
def gallery_list():
    images = GalleryImage.query.order_by(GalleryImage.display_order).all()
    return render_template("admin/gallery.html", images=images)


@admin_bp.route("/gallery/add", methods=["POST"])
@admin_required
def gallery_add():
    db.session.add(GalleryImage(
        image_url=request.form["image_url"],
        caption=request.form.get("caption", ""),
        display_order=request.form.get("display_order") or 0,
    ))
    db.session.commit()
    flash("Image added.", "success")
    return redirect(url_for("admin.gallery_list"))


@admin_bp.route("/gallery/<int:image_id>/delete", methods=["POST"])
@admin_required
def gallery_delete(image_id):
    image = GalleryImage.query.get_or_404(image_id)
    db.session.delete(image)
    db.session.commit()
    flash("Image removed.", "success")
    return redirect(url_for("admin.gallery_list"))


@admin_bp.route("/enrollments")
@admin_required
def enrollments_list():
    enrollments = Enrollment.query.order_by(Enrollment.enrollment_date.desc()).all()
    return render_template("admin/enrollments.html", enrollments=enrollments)


@admin_bp.route("/enrollments/<int:enrollment_id>/status", methods=["POST"])
@admin_required
def enrollments_update_status(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    enrollment.status = request.form["status"]
    db.session.commit()
    flash("Enrollment status updated.", "success")
    return redirect(url_for("admin.enrollments_list"))


@admin_bp.route("/messages")
@admin_required
def messages_list():
    messages = ContactMessage.query.order_by(ContactMessage.submitted_at.desc()).all()
    return render_template("admin/messages.html", messages=messages)


# ---------- Student management (soft delete / reactivate) ----------

@admin_bp.route("/students")
@admin_required
def students_list():
    students = Student.query.order_by(Student.is_active.desc(), Student.full_name).all()
    return render_template("admin/students.html", students=students)


@admin_bp.route("/students/<int:student_id>/deactivate", methods=["POST"])
@admin_required
def students_deactivate(student_id):
    # SOFT DELETE: we never run DELETE FROM students here. Flipping
    # is_active to False keeps all their results/attendance/enrollment
    # history intact and queryable, while removing their portal access
    # and hiding them from active lists.
    student = Student.query.get_or_404(student_id)
    student.is_active = False
    db.session.commit()
    flash(f"{student.full_name} marked inactive. Their data is preserved.", "success")
    return redirect(url_for("admin.students_list"))


@admin_bp.route("/students/<int:student_id>/reactivate", methods=["POST"])
@admin_required
def students_reactivate(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_active = True
    db.session.commit()
    flash(f"{student.full_name} reactivated.", "success")
    return redirect(url_for("admin.students_list"))


# ---------- Teacher management ----------

@admin_bp.route("/teachers")
@admin_required
def teachers_list():
    teachers = Teacher.query.order_by(Teacher.is_active.desc(), Teacher.full_name).all()
    all_courses = Course.query.order_by(Course.title).all()
    return render_template("admin/teachers.html", teachers=teachers, all_courses=all_courses)


@admin_bp.route("/teachers/add", methods=["POST"])
@admin_required
def teachers_add():
    username = request.form["username"].strip()
    if Teacher.query.filter_by(username=username).first():
        flash("That username is already taken.", "error")
        return redirect(url_for("admin.teachers_list"))

    teacher = Teacher(
        full_name=request.form["full_name"],
        username=username,
        password_hash=generate_password_hash(request.form.get("password") or "teacher123"),
        subject=request.form.get("subject", ""),
        phone=request.form.get("phone", ""),
        email=request.form.get("email", ""),
    )
    db.session.add(teacher)
    db.session.commit()
    flash("Teacher added.", "success")
    return redirect(url_for("admin.teachers_list"))


@admin_bp.route("/teachers/<int:teacher_id>/assign-course", methods=["POST"])
@admin_required
def teachers_assign_course(teacher_id):
    course_id = request.form.get("course_id")
    existing = TeacherCourse.query.filter_by(teacher_id=teacher_id, course_id=course_id).first()
    if not existing:
        db.session.add(TeacherCourse(teacher_id=teacher_id, course_id=course_id))
        db.session.commit()
        flash("Course assigned to teacher.", "success")
    else:
        flash("Teacher already assigned to that course.", "error")
    return redirect(url_for("admin.teachers_list"))


@admin_bp.route("/teachers/<int:teacher_id>/deactivate", methods=["POST"])
@admin_required
def teachers_deactivate(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    teacher.is_active = False
    db.session.commit()
    flash(f"{teacher.full_name} marked inactive.", "success")
    return redirect(url_for("admin.teachers_list"))


@admin_bp.route("/teachers/<int:teacher_id>/reactivate", methods=["POST"])
@admin_required
def teachers_reactivate(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    teacher.is_active = True
    db.session.commit()
    flash(f"{teacher.full_name} reactivated.", "success")
    return redirect(url_for("admin.teachers_list"))


# ---------- Results management ----------

@admin_bp.route("/results")
@admin_required
def results_list():
    results = Result.query.order_by(Result.result_date.desc()).all()
    active_students = Student.query.filter_by(is_active=True).order_by(Student.full_name).all()
    courses = Course.query.order_by(Course.title).all()
    return render_template("admin/results.html", results=results, students=active_students, courses=courses)


@admin_bp.route("/results/add", methods=["POST"])
@admin_required
def results_add():
    db.session.add(Result(
        student_id=request.form["student_id"],
        course_id=request.form.get("course_id") or None,
        test_name=request.form["test_name"],
        marks_obtained=request.form.get("marks_obtained") or 0,
        total_marks=request.form.get("total_marks") or 0,
        result_date=request.form.get("result_date") or None,
    ))
    db.session.commit()
    flash("Result added.", "success")
    return redirect(url_for("admin.results_list"))


@admin_bp.route("/results/<int:result_id>/delete", methods=["POST"])
@admin_required
def results_delete(result_id):
    result = Result.query.get_or_404(result_id)
    db.session.delete(result)
    db.session.commit()
    flash("Result removed.", "success")
    return redirect(url_for("admin.results_list"))
