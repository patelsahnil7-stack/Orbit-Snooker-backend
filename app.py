from flask import Flask, request, jsonify
import os
import psycopg2
import bcrypt

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def create_tables():
    conn = get_connection()
    cur = conn.cursor()
    
with app.app_context():
    create_tables()
    
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

@app.route("/")
def home():
    return "Orbit Snooker Backend Running"

@app.route("/create-main-admin", methods=["POST"])
def create_main_admin():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO admins (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, hashed_pw.decode('utf-8'), "admin")
        )
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()
        conn.close()

    return jsonify({"message": "Main admin created successfully"})
@app.route("/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT id, username, password_hash, role FROM admins WHERE username=%s AND is_active=TRUE",
            (username,)
        )
        admin = cur.fetchone()

        if not admin:
            return jsonify({"error": "Invalid username or password"}), 401

        admin_id, db_username, db_password_hash, role = admin

        if not bcrypt.checkpw(password.encode("utf-8"), db_password_hash.encode("utf-8")):
            return jsonify({"error": "Invalid username or password"}), 401

        return jsonify({
            "message": "Login successful",
            "admin_id": admin_id,
            "username": db_username,
            "role": role
        })

    finally:
        cur.close()
        conn.close()
create_tables()

if __name__ == "__main__":
    app.run()
