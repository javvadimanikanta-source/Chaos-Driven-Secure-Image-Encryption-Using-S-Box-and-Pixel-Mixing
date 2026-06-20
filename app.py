from flask import Flask, render_template, request, redirect, session
from encryption import encrypt_image
from decryption import decrypt_image
from flask import send_from_directory
from werkzeug.utils import secure_filename
import cv2
import sqlite3
import os
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secure_image_project"

UPLOAD_FOLDER = "static/uploads"
ENCRYPTED_FOLDER = "static/encrypted"
DECRYPTED_FOLDER = "static/decrypted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)


# =========================
# DATABASE
# =========================

def init_db():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS images(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_username TEXT,
        receiver_username TEXT,
        filename TEXT,
        secret_key TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS image_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            sender TEXT NOT NULL,

            receiver TEXT NOT NULL,

            encrypted_filename TEXT NOT NULL,

            original_filename TEXT NOT NULL,

            secret_key TEXT NOT NULL,

            sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================
# HOME
# =========================

@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")

    sent_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM image_history
        WHERE sender=?
        """,
        (session["user"],)
    ).fetchone()[0]

    received_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM image_history
        WHERE receiver=?
        """,
        (session["user"],)
    ).fetchone()[0]

    total_users = conn.execute(
        """
        SELECT COUNT(*)
        FROM users
        """
    ).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        username=session["user"],
        sent_count=sent_count,
        received_count=received_count,
        total_users=total_users
    )

# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        hashed_password = generate_password_hash(password)

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match"
            )

        if not email.endswith("@gmail.com"):
            return render_template(
                "register.html",
                error="Please enter a valid Gmail address"
            )

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        try:

            cur.execute(
                """
                INSERT INTO users(username,email,password)
                VALUES(?,?,?)
                """,
                (username,email,hashed_password)
                    
            )

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "register.html",
                error="Username or Email already exists"
            )

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            """
            SELECT * FROM users
            WHERE email=?
            """,
            (email,)
        )

        user = cur.fetchone()

        conn.close()

        if user and check_password_hash(user[3],password):
   
            session["user"] = user[1]

            return redirect("/")

        else:

            return render_template(
                "login.html",
                error="Invalid Email or Password"
            )

    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================
# SENDER
# =========================

@app.route("/sender", methods=["GET", "POST"])
def sender():

    if "user" not in session:
        return redirect("/login")
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT username
        FROM users
        WHERE username != ?
        """,
        (session["user"],)
    )

    users = cur.fetchall()

    conn.close()

    if request.method == "POST":

        if "image" not in request.files:
            return render_template(
                "sender.html",
                error="Please select an image"
            )

        image = request.files["image"]

        receiver = request.form["receiver_username"]

        secret_key = request.form["secret_key"]

        allowed_extensions = {
            "jpg",
            "jpeg",
            "png",
            "bmp",
            "tiff",
            "webp"
        }

        if "." not in image.filename:
            return render_template(
                "sender.html",
                error="Please select an image file"
            )

        ext = image.filename.rsplit(".", 1)[1].lower()

        if ext not in allowed_extensions:
            return render_template(
                "sender.html",
                error="Unsupported image format"
            )
        # Check receiver exists
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=?",
            (receiver,)
        )

        user = cur.fetchone()

        if not user:
            conn.close()

            return render_template(
                "sender.html",
                error="Receiver username not found"
            )

        # Check image extension
        allowed_extensions = ["png", "jpg", "jpeg"]

        ext = image.filename.rsplit(".", 1)[-1].lower()

        if ext not in allowed_extensions:
            conn.close()

            return render_template(
                "sender.html",
                error="Only PNG, JPG and JPEG images are allowed"
            )

        # Safe filename
        from werkzeug.utils import secure_filename

        filename = secure_filename(image.filename)

        original_filename = secure_filename(
            image.filename
        )

        filepath = os.path.join(
            UPLOAD_FOLDER,
            original_filename
        )

        image.save(filepath)
        encrypted = encrypt_image(
            filepath,
            secret_key
        )

        filename_without_ext = os.path.splitext(
            original_filename
        )[0]

        encrypted_name = (
            "enc_" +
            filename_without_ext +
            ".png"
        )
        encrypted_path = os.path.join(
            ENCRYPTED_FOLDER,
            encrypted_name
        )

        cv2.imwrite(
            encrypted_path,
            cv2.cvtColor(
                encrypted,
                cv2.COLOR_RGB2BGR
            )
        )

        cur.execute(
            """
            INSERT INTO images(
                sender_username,
                receiver_username,
                filename,
                secret_key
            )
            VALUES(?,?,?,?)
            """,
            (
                session["user"],
                receiver,
                encrypted_name,
                secret_key
            )
        )
        
        current_user = session["user"]

        sent_time = datetime.now().strftime(
            "%d/%m/%Y %H:%M"
        )

        conn.execute("""
        INSERT INTO image_history
        (
        sender,
        receiver,
        encrypted_filename,
        original_filename,
        secret_key,
        sent_time
        )
        VALUES (?,?,?,?,?,?)
        """,
        (
            current_user,
            receiver,
            encrypted_name,
            original_filename,
            secret_key,
            sent_time
        ))

        cur.execute("""
        SELECT
            sender,
            receiver,
            encrypted_filename,
            sent_time
        FROM image_history
        ORDER BY id DESC
        LIMIT 5
        """)

        print("\n===== IMAGE HISTORY =====")

        for row in cur.fetchall():
            print(row)

        print("=========================\n")

        cur.execute("SELECT * FROM image_history")
        print("History Records:", cur.fetchall())
        

        conn.commit()
        conn.close()

        return render_template(
            "result.html",
            message="Image Sent Successfully",
            image_name=encrypted_name,
            image_path="encrypted/" + encrypted_name
        )
       
    return render_template(
        "sender.html",
        users=users
    )
# =========================
# RECEIVER
# =========================

@app.route("/receiver", methods=["GET", "POST"])
def receiver():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            encrypted_filename,
            sender,
            sent_time
        FROM image_history
        WHERE receiver=?
        ORDER BY id DESC
        """,
        (session["user"],)
    )

    images = cur.fetchall()

    print("\n===== RECEIVER DATA =====")
    print("Logged User:", session["user"])

    for img in images:
        print(img)

    print("=========================\n")

    conn.close()

    if request.method == "POST":

        image_name = request.form["image_name"]

        secret_key = request.form["secret_key"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM images
            WHERE filename=?
            AND secret_key=?
            AND receiver_username=?
            """,
            (
                image_name,
                secret_key,
                session["user"]
            )
        )

        data = cur.fetchone()

        conn.close()

        if not data:

            return render_template(
                "receiver.html",
                images=images,
                error="Invalid Secret Key"
            )

        encrypted_path = os.path.join(
            ENCRYPTED_FOLDER,
            image_name
        )
        print("Opening:", encrypted_path)
        print("Exists:", os.path.exists(encrypted_path))

        decrypted = decrypt_image(
            encrypted_path,
            secret_key
        )

        output_name = (
            "dec_" +
            os.path.splitext(image_name)[0] +
            ".png"
        )

        output_path = os.path.join(
            DECRYPTED_FOLDER,
            output_name
        )

        cv2.imwrite(
            output_path,
            cv2.cvtColor(
                decrypted,
                cv2.COLOR_RGB2BGR
            )
        )

        return render_template(
            "result.html",
            message="Image Decrypted Successfully",
            image_name=output_name,
            image_path="decrypted/" + output_name
        )
    return render_template(
        "receiver.html",
        images=images
    )


# =========================
# RUN
# =========================

@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/login")

    search = request.args.get("search", "")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    history = conn.execute("""
    SELECT *
    FROM image_history
    WHERE
    (sender=? OR receiver=?)
    AND
    (
        sender LIKE ?
        OR receiver LIKE ?
        OR original_filename LIKE ?
    )
    ORDER BY sent_time DESC
    """,
    (
        session["user"],
        session["user"],
        f"%{search}%",
        f"%{search}%",
        f"%{search}%"
    )).fetchall()

    conn.close()

    return render_template(
        "history.html",
        history=history,
        search=search
    )

@app.route("/view_history/<int:image_id>")
def view_history(image_id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    image = conn.execute(
        "SELECT * FROM image_history WHERE id=?",
        (image_id,)
    ).fetchone()

    conn.close()

    if image is None:
        return "Image not found"

    if image["sender"] == session["user"]:
        return render_template(
            "view_sent.html",
            image=image
        )

    return render_template(
        "verify_key.html",
        image=image
    )    

@app.route(
"/decrypt_history/<int:image_id>",
methods=["POST"]
)
def decrypt_history(image_id):

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    image = conn.execute(
        """
        SELECT *
        FROM image_history
        WHERE id=?
        """,
        (image_id,)
    ).fetchone()

    conn.close()

    entered_key = request.form["secret_key"]

    if entered_key != image["secret_key"]:

        return render_template(
            "verify_key.html",
            image=image,
            error="❌ Wrong Secret Key"
        )

    decrypted_file = "dec_" + image["encrypted_filename"]

    return render_template(
        "view_received.html",
        image=image,
        decrypted_file=decrypted_file
    )

@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE username=?
        """,
        (session["user"],)
    ).fetchone()

    sent_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM image_history
        WHERE sender=?
        """,
        (session["user"],)
    ).fetchone()[0]

    received_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM image_history
        WHERE receiver=?
        """,
        (session["user"],)
    ).fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        username=user["username"],
        email=user["email"],
        sent_count=sent_count,
        received_count=received_count
    )

@app.route("/stats")
def stats():

    conn = sqlite3.connect(
        "database.db"
    )

    cur = conn.cursor()

    cur.execute(
    "SELECT COUNT(*) FROM users"
    )
    users = cur.fetchone()[0]

    cur.execute(
    "SELECT COUNT(*) FROM images"
    )
    images = cur.fetchone()[0]

    conn.close()

    return render_template(
        "stats.html",
        users=users,
        images=images
    )

@app.route("/delete_history/<int:image_id>")
def delete_history(image_id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")

    conn.execute(
        """
        DELETE FROM image_history
        WHERE id=?
        AND (
            sender=?
            OR receiver=?
        )
        """,
        (
            image_id,
            session["user"],
            session["user"]
        )
    )

    conn.commit()
    conn.close()

    return redirect("/history")

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        'static',
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@app.route("/check_history")
def check_history():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM image_history
    ORDER BY id DESC
    """)

    rows = cur.fetchall()

    conn.close()

    return str(rows)

if __name__ == "__main__":
    app.run(debug=True)