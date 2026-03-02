from flask import Flask, request, jsonify
import os
import psycopg2
import bcrypt

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")


# ---------------- DATABASE CONNECTION ---------------- #

def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ---------------- CREATE TABLE ---------------- #

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'admin',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


# ---------------- HOME ROUTE ---------------- #

@app.route("/")
def home():
    return "Orbit Snooker Backend Running"


# ---------------- CREATE MAIN ADMIN ---------------- #

@app.route("/create-main-admin", methods=["POST"])
def create_main_admin():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO admins (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, hashed_pw.decode("utf-8"), "admin")
        )
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        conn.close()

    return jsonify({"message": "Main admin created successfully"})


# ---------------- ADMIN LOGIN ---------------- #

@app.route("/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, password_hash FROM admins WHERE username = %s", (username,))
    admin = cur.fetchone()

    cur.close()
    conn.close()

    if not admin:
        return jsonify({"error": "Invalid username or password"}), 401

    admin_id, stored_hash = admin

    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({
        "message": "Login successful",
        "admin_id": admin_id
    })


# ---------------- START APP ---------------- #

if __name__ == "__main__":
    create_tables()
    app.run()
