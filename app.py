from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import jwt
import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'supersecretkey'

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# =========================
# TABLE CREATION
# =========================

cur.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);
""")

conn.commit()

# =========================
# TOKEN DECORATOR
# =========================

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
            current_user = data['user_id']
        except:
            return jsonify({'error': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# =========================
# USER REGISTER
# =========================

@app.route('/user-register', methods=['POST'])
def user_register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        return jsonify({"error": "User already exists"}), 400

    hashed_password = generate_password_hash(password)

    cur.execute(
        "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
        (name, email, hashed_password)
    )
    conn.commit()

    return jsonify({"message": "User registered successfully"})

# =========================
# USER LOGIN
# =========================

@app.route('/user-login', methods=['POST'])
def user_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not check_password_hash(user[3], password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = jwt.encode({
        'user_id': user[0],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        "message": "Login successful",
        "token": token
    })

# =========================
# USER PROFILE (PROTECTED)
# =========================

@app.route('/user-profile', methods=['GET'])
@token_required
def user_profile(current_user):
    cur.execute("SELECT id, name, email FROM users WHERE id=%s", (current_user,))
    user = cur.fetchone()

    return jsonify({
        "id": user[0],
        "name": user[1],
        "email": user[2]
    })

# =========================
# SERVER RUN
# =========================

@app.route('/')
def home():
    return "Orbit Snooker Backend Running"

if __name__ == '__main__':
    app.run(debug=True)
