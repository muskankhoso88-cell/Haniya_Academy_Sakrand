from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.models import db, Course, Faculty, Achiever, GalleryImage, Student, ContactMessage
from werkzeug.security import generate_password_hash

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    # Every list below is a simple SELECT ... ORDER BY query against MySQL,
    # replacing what used to be hardcoded HTML blocks.
    courses = Course.query.order_by(Course.display_order).all()
    faculty = Faculty.query.order_by(Faculty.display_order).all()
    achievers = Achiever.query.order_by(Achiever.display_order).all()
    gallery = GalleryImage.query.order_by(GalleryImage.display_order).all()

    return render_template(
        "index.html",
        courses=courses,
        faculty=faculty,
        achievers=achievers,
        gallery=gallery,
    )


@public_bp.route("/enroll", methods=["POST"])
def enroll():
    """Handles the 'Enroll or Register for Scholarship Test' form.
    Creates a Student row if the roll number is new, then writes the
    enrollment row linking student <-> course. Wrapped in a single
    transaction: if anything fails, nothing is committed (ACID)."""
    roll_number = request.form.get("roll_number", "").strip()
    full_name = request.form.get("full_name", "").strip()
    father_name = request.form.get("father_name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    course_id = request.form.get("course_id")
    password = request.form.get("password", "changeme123")

    if not roll_number or not full_name or not course_id:
        flash("Roll number, name and course are required.", "error")
        return redirect(url_for("public.home") + "#enroll")

    try:
        student = Student.query.filter_by(roll_number=roll_number).first()
        if not student:
            student = Student(
                roll_number=roll_number,
                full_name=full_name,
                father_name=father_name,
                phone=phone,
                email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(student)
            db.session.flush()  # get student.student_id before commit

        from app.models import Enrollment
        existing = Enrollment.query.filter_by(
            student_id=student.student_id, course_id=course_id
        ).first()
        if existing:
            flash("You are already registered for this course.", "error")
            db.session.rollback()
            return redirect(url_for("public.home") + "#enroll")

        enrollment = Enrollment(student_id=student.student_id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()  # commits student + enrollment together
        flash("Registration submitted successfully!", "success")
    except Exception as exc:
        db.session.rollback()  # ROLLBACK keeps the DB consistent on error
        flash(f"Something went wrong: {exc}", "error")

    return redirect(url_for("public.home") + "#enroll")


@public_bp.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not message:
        flash("Name and message are required.", "error")
        return redirect(url_for("public.home") + "#contact")

    db.session.add(ContactMessage(name=name, email=email, phone=phone, message=message))
    db.session.commit()
    flash("Message sent! We'll get back to you soon.", "success")
    return redirect(url_for("public.home") + "#contact")
