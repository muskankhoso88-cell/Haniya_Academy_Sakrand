import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # DBMS connection settings.
    # PyMySQL is used as the driver, SQLAlchemy as the ORM layer on top of MySQL.
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "haniya_academy")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")

    # Where teacher-uploaded materials are stored on disk.
    # Kept OUTSIDE the public "static" folder on purpose — files are only
    # served through a route that checks the student is actually enrolled
    # in that course before sending the file.
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "materials"),
    )
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB max per uploaded file
