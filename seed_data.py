"""
Run this once after creating the database schema to add:
  - a default admin login
  - sample courses / faculty / achievers matching the original static site

Usage:
    python seed_data.py
"""
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, Admin, Course, Faculty, Achiever, Teacher, TeacherCourse, GalleryImage

app = create_app()

with app.app_context():
    # 1. Default admin account (change this password after first login!)
    if not Admin.query.filter_by(username="admin").first():
        db.session.add(Admin(
            username="admin",
            password_hash=generate_password_hash("admin123")
        ))

    # 2. Sample courses (from the original "Our Programs" section)
    if Course.query.count() == 0:
        db.session.add_all([
            Course(title="MDCAT Preparation", description="Complete MDCAT prep with test series.",
                   duration="1 Year", fee=15000, display_order=1),
            Course(title="ECAT Preparation", description="Engineering entrance test preparation.",
                   duration="1 Year", fee=15000, display_order=2),
        ])

    # 3. Real faculty, extracted from the academy's own "Meet Our Faculty" posters
    if Faculty.query.count() == 0:
        f = "/static/images/faculty/"
        db.session.add_all([
            Faculty(full_name="Prof. Ghullam Hussain Jalbani", designation="Director / Senior Faculty",
                    subject="Physics, Chemistry, Mathematics & Computer Science",
                    photo_url=f + "ghullam_hussain_jalbani.jpg", display_order=1),
            Faculty(full_name="Miss Rabia Arain", designation="Faculty Member", subject="Physics & Biology",
                    photo_url=f + "rabia_arain.jpg", display_order=2),
            Faculty(full_name="Miss Bilquees Abbasi", designation="Faculty Member", subject="Physics",
                    photo_url=f + "bilquees_abbasi.jpg", display_order=3),
            Faculty(full_name="Sir Waseem Mallah", designation="Faculty Member", subject="Chemistry",
                    photo_url=f + "waseem_mallah.jpg", display_order=4),
            Faculty(full_name="Naresh Kumar", designation="Faculty Member", subject="Chemistry",
                    photo_url=f + "naresh_kumar.jpg", display_order=5),
            Faculty(full_name="Prof. Niaz Hussain Jalbani", designation="Faculty Member", subject="Mathematics",
                    photo_url=f + "niaz_hussain_jalbani.jpg", display_order=6),
            Faculty(full_name="Miss Marium Arain", designation="Faculty Member", subject="Mathematics",
                    photo_url=f + "marium_arain.jpg", display_order=7),
            Faculty(full_name="Shahbaz Soomro", designation="Faculty Member", subject="Computer Science",
                    photo_url=f + "shahbaz_soomro.jpg", display_order=8),
            Faculty(full_name="Muskan Khoso", designation="Faculty Member", subject="Computer Science",
                    photo_url=f + "muskan_khoso.jpg", display_order=9),
            Faculty(full_name="Dr. Rovaida Arain", designation="Faculty Member", subject="Biology",
                    photo_url=f + "rovaida_arain.jpg", display_order=10),
            Faculty(full_name="Dr. Savera Khanzada", designation="Faculty Member", subject="Biology",
                    photo_url=f + "savera_khanzada.jpg", display_order=11),
        ])

    # 4. Gallery — real academy photos (classrooms, ceremonies, staff, faculty posters)
    if GalleryImage.query.count() == 0:
        g = "/static/images/gallery/"
        gallery_items = [
            ("classroom_1.jpg", "Students in class"),
            ("classroom_2.jpg", "Students in class"),
            ("event_ceremony.jpg", "Shield Distribution Ceremony"),
            ("staff_group.jpg", "Our academy staff"),
            ("faculty_physics.jpg", "Meet Our Physics Faculty"),
            ("faculty_chemistry.jpg", "Meet Our Chemistry Faculty"),
            ("faculty_math.jpg", "Meet Our Mathematics Faculty"),
            ("faculty_cs.jpg", "Meet Our Computer Science Faculty"),
            ("faculty_bio.jpg", "Meet Our Biology Faculty"),
            ("award_0103f8.jpg", "Award ceremony"),
            ("award_4fd0b2.jpg", "Award ceremony"),
            ("award_59b030.jpg", "Award ceremony"),
            ("award_75330d.jpg", "Award ceremony"),
            ("award_77d6ff.jpg", "Award ceremony"),
            ("award_8010d0.jpg", "Award ceremony"),
            ("award_9ebf5e.jpg", "Award ceremony"),
            ("award_a42143.jpg", "Award ceremony"),
            ("award_b54c25.jpg", "Award ceremony"),
            ("award_be52b3.jpg", "Award ceremony"),
            ("award_e5e48c.jpg", "Award ceremony"),
        ]
        for i, (filename, caption) in enumerate(gallery_items, start=1):
            db.session.add(GalleryImage(image_url=g + filename, caption=caption, display_order=i))

    db.session.commit()  # commit so courses get real IDs before assigning a teacher to them

    # 5. Sample teacher, assigned to the first course (login: teacher1 / teacher123)
    if not Teacher.query.filter_by(username="teacher1").first():
        teacher = Teacher(
            full_name="Ms. Ayesha Khan",
            username="teacher1",
            password_hash=generate_password_hash("teacher123"),
            subject="Biology",
        )
        db.session.add(teacher)
        db.session.flush()  # get teacher.teacher_id

        first_course = Course.query.order_by(Course.display_order).first()
        if first_course:
            db.session.add(TeacherCourse(teacher_id=teacher.teacher_id, course_id=first_course.course_id))

    db.session.commit()
    print("Seed data inserted successfully.")
