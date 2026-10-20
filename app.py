import os
import sqlite3
import secrets
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("VIDEO_DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "videos"
DB_PATH = DATA_DIR / "school.db"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_MB", "500")) * 1024 * 1024

CLASSES = ["Class 9", "Class 10", "Class 11", "Class 12"]
SUBJECTS = ["Physics", "Chemistry", "Biology", "Maths"]
ALLOWED_EXTENSIONS = {"mp4", "m4v", "webm", "mov", "mkv", "avi"}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(class_name, subject, name)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

init_db()

def admin_password_hash():
    password = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")
    return generate_password_hash(password)

# Password hash is stored in a local config file after first launch.
AUTH_FILE = DATA_DIR / "admin_hash.txt"
if not AUTH_FILE.exists():
    AUTH_FILE.write_text(admin_password_hash(), encoding="utf-8")

def check_admin_password(password):
    try:
        stored_hash = AUTH_FILE.read_text(encoding="utf-8").strip()
        return check_password_hash(stored_hash, password)
    except Exception:
        return False

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            flash("Please log in to access the admin panel.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def common_values():
    return {"school_name": "Naga Nirankari Vidya Niketan", "classes": CLASSES, "subjects": SUBJECTS}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/class/<class_name>")
def class_page(class_name):
    if class_name not in CLASSES:
        abort(404)
    conn = db()
    chapters = conn.execute(
        "SELECT c.*, COUNT(v.id) AS video_count FROM chapters c LEFT JOIN videos v ON v.chapter_id=c.id WHERE c.class_name=? GROUP BY c.id ORDER BY c.subject, c.id",
        (class_name,)
    ).fetchall()
    conn.close()
    return render_template("class.html", class_name=class_name, chapters=chapters)

@app.route("/subject/<class_name>/<subject>")
def subject_page(class_name, subject):
    if class_name not in CLASSES or subject not in SUBJECTS:
        abort(404)
    conn = db()
    chapters = conn.execute(
        "SELECT c.*, COUNT(v.id) AS video_count FROM chapters c LEFT JOIN videos v ON v.chapter_id=c.id WHERE c.class_name=? AND c.subject=? GROUP BY c.id ORDER BY c.id",
        (class_name, subject)
    ).fetchall()
    conn.close()
    return render_template("subject.html", class_name=class_name, subject=subject, chapters=chapters)

@app.route("/chapter/<int:chapter_id>")
def chapter_page(chapter_id):
    conn = db()
    chapter = conn.execute("SELECT * FROM chapters WHERE id=?", (chapter_id,)).fetchone()
    videos = conn.execute("SELECT * FROM videos WHERE chapter_id=? ORDER BY id", (chapter_id,)).fetchall()
    conn.close()
    if not chapter:
        abort(404)
    return render_template("chapter.html", chapter=chapter, videos=videos)

@app.route("/video/<int:video_id>/file")
def video_file(video_id):
    conn = db()
    video = conn.execute("SELECT filename FROM videos WHERE id=?", (video_id,)).fetchone()
    conn.close()
    if not video:
        abort(404)
    response = send_from_directory(UPLOAD_DIR, video["filename"], as_attachment=False, conditional=True)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@app.route("/admin")
@admin_required
def admin():
    conn = db()
    chapters = conn.execute(
        "SELECT c.*, COUNT(v.id) AS video_count FROM chapters c LEFT JOIN videos v ON v.chapter_id=c.id GROUP BY c.id ORDER BY c.class_name, c.subject, c.id"
    ).fetchall()
    videos = conn.execute(
        "SELECT v.*, c.name AS chapter_name, c.class_name, c.subject FROM videos v JOIN chapters c ON c.id=v.chapter_id ORDER BY v.id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return render_template("admin.html", chapters=chapters, videos=videos)

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if session.get("admin"):
        return redirect(url_for("admin"))
    if request.method == "POST":
        password = request.form.get("password", "")
        if check_admin_password(password):
            session.clear()
            session["admin"] = True
            session.permanent = True
            flash("Login successful.", "success")
            return redirect(url_for("admin"))
        flash("Incorrect password. Please try again.", "danger")
    return render_template("login.html")

@app.route("/admin/logout", methods=["POST"])
@admin_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/admin/chapter", methods=["POST"])
@admin_required
def add_chapter():
    class_name = request.form.get("class_name", "")
    subject = request.form.get("subject", "")
    name = request.form.get("name", "").strip()
    if class_name not in CLASSES or subject not in SUBJECTS or not name:
        flash("Please enter a valid class, subject, and chapter name.", "danger")
        return redirect(url_for("admin"))
    try:
        with db() as conn:
            conn.execute("INSERT INTO chapters (class_name, subject, name) VALUES (?, ?, ?)", (class_name, subject, name))
        flash("Chapter added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("This chapter already exists in this subject.", "warning")
    return redirect(url_for("admin"))

@app.route("/admin/video", methods=["POST"])
@admin_required
def add_video():
    chapter_id = request.form.get("chapter_id", type=int)
    title = request.form.get("title", "").strip()
    file = request.files.get("video")
    if not chapter_id or not title or not file or not file.filename:
        flash("Please select a chapter, video title, and video file.", "danger")
        return redirect(url_for("admin"))
    if not allowed_file(file.filename):
        flash("Supported formats: MP4, M4V, WEBM, MOV, MKV, AVI.", "danger")
        return redirect(url_for("admin"))
    conn = db()
    chapter = conn.execute("SELECT id FROM chapters WHERE id=?", (chapter_id,)).fetchone()
    conn.close()
    if not chapter:
        flash("Chapter not found. Please add a chapter first.", "danger")
        return redirect(url_for("admin"))
    original = secure_filename(file.filename) or "video"
    ext = original.rsplit(".", 1)[1].lower()
    stored = secrets.token_hex(16) + "." + ext
    try:
        file.save(UPLOAD_DIR / stored)
        with db() as conn:
            conn.execute("INSERT INTO videos (chapter_id, title, filename, original_name) VALUES (?, ?, ?, ?)",
                         (chapter_id, title, stored, original))
        flash("Video uploaded successfully.", "success")
    except Exception:
        (UPLOAD_DIR / stored).unlink(missing_ok=True)
        flash("Upload failed. Check storage availability and file size.", "danger")
    return redirect(url_for("admin"))

@app.route("/admin/video/<int:video_id>/delete", methods=["POST"])
@admin_required
def delete_video(video_id):
    conn = db()
    video = conn.execute("SELECT filename FROM videos WHERE id=?", (video_id,)).fetchone()
    if video:
        conn.execute("DELETE FROM videos WHERE id=?", (video_id,))
        conn.commit()
        (UPLOAD_DIR / video["filename"]).unlink(missing_ok=True)
        flash("Video deleted successfully.", "success")
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin/chapter/<int:chapter_id>/delete", methods=["POST"])
@admin_required
def delete_chapter(chapter_id):
    conn = db()
    videos = conn.execute("SELECT filename FROM videos WHERE chapter_id=?", (chapter_id,)).fetchall()
    chapter = conn.execute("SELECT id FROM chapters WHERE id=?", (chapter_id,)).fetchone()
    if chapter:
        conn.execute("DELETE FROM chapters WHERE id=?", (chapter_id,))
        conn.commit()
        for v in videos:
            (UPLOAD_DIR / v["filename"]).unlink(missing_ok=True)
        flash("The chapter and its videos have been deleted.", "success")
    conn.close()
    return redirect(url_for("admin"))

@app.errorhandler(413)
def too_large(_error):
    return render_template("error.html", message="Video file exceeds the upload limit. The default limit is 500 MB. You can change the MAX_UPLOAD_MB setting."), 413

if __name__ == "__main__":
    # Local-only by default. Use 0.0.0.0 only when you intentionally want LAN access.
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")), debug=False)
