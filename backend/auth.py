from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
from utils.crypto import generate_encryption_key
import traceback

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/auth/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return jsonify({"error": "Email already registered"}), 400

        hashed_password = generate_password_hash(password)
        encryption_key = generate_encryption_key()

        cur.execute("""
            INSERT INTO users (email, hashed_password, encryption_key)
            VALUES (%s, %s, %s) RETURNING id
        """, (email, hashed_password, encryption_key))

        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Signup successful", "user_id": user_id}), 201

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Signup failed"}), 500

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, hashed_password FROM users WHERE email = %s", (email,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if not result:
            return jsonify({"error": "Invalid credentials"}), 401

        user_id, hashed_password = result

        if not check_password_hash(hashed_password, password):
            return jsonify({"error": "Invalid credentials"}), 401

        return jsonify({"message": "Login successful", "user_id": user_id}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Login failed"}), 500
