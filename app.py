from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'supersecretkey'

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Create admin table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL
);
""")
conn.commit()


@app.route('/')
def home():
    return "Orbit Snooker Backend Running"


# Create Main Admin
@app.route('/create-main-admin', methods=['POST'])
def create_admin():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    cur.execute("SELECT * FROM admin WHERE username=%s", (username,))
    if cur.fetchone():
        return jsonify({"message": "Admin already exists"}), 400

    cur.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()

    return jsonify({"message": "Main admin created successfully"})


# Admin Login
@app.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
    admin = cur.fetchone()

    if not admin:
        return jsonify({"error": "Invalid username or password"}), 401

    token = jwt.encode({
        'admin_id': admin[0],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        "message": "Login successful",
        "token": token
    })


# Token Required Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_admin = data['admin_id']
        except:
            return jsonify({'error': 'Token is invalid'}), 401

        return f(current_admin, *args, **kwargs)

    return decorated


# Admin Dashboard Route
@app.route('/admin-dashboard', methods=['GET'])
@token_required
def admin_dashboard(current_admin):
    cur.execute("SELECT COUNT(*) FROM admin")
    total_admins = cur.fetchone()[0]

    return jsonify({
        "message": "Welcome to Admin Dashboard",
        "admin_id": current_admin,
        "total_admins": total_admins
    })


if __name__ == '__main__':
    app.run(debug=True)
