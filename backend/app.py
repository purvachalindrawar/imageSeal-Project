# 📁 backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from auth import auth_bp
from utils.db import get_db_connection
from utils.crypto import encrypt_image, decrypt_image
import base64
from share import share_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)
app.register_blueprint(share_bp)

# 📤 Upload Image
@app.route("/upload", methods=["POST"])
def upload_image():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user ID"}), 400

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files["image"]
    image_data = file.read()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT encryption_key FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()

    if not row:
        return jsonify({"error": "User not found"}), 404

    encryption_key = row[0]
    encrypted = encrypt_image(image_data, encryption_key)

    cur.execute(
        "INSERT INTO images (user_id, image_data) VALUES (%s, %s) RETURNING id",
        (user_id, encrypted)
    )
    image_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Image uploaded securely", "image_id": image_id}), 200

# 📥 View Images using Email
@app.route("/images", methods=["GET"])
def view_images():
    email = request.args.get("email")

    if not email:
        return jsonify({"error": "Missing email"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, encryption_key FROM users WHERE email = %s", (email,))
    result = cur.fetchone()

    if not result:
        return jsonify({"error": "User not found"}), 404

    user_id, encryption_key = result

    cur.execute("SELECT id, image_data FROM images WHERE user_id = %s", (user_id,))
    image_rows = cur.fetchall()

    images = []
    for image_id, encrypted_data in image_rows:
        try:
            decrypted = decrypt_image(encrypted_data, encryption_key)
            base64_image = base64.b64encode(decrypted).decode("utf-8")
            images.append({"id": image_id, "data": base64_image})
        except Exception as e:
            print("Decryption failed:", e)

    cur.close()
    conn.close()

    return jsonify({"images": images}), 200

# ❌ Delete Image by ID
@app.route("/image/<int:image_id>", methods=["DELETE"])
def delete_image(image_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM images WHERE id = %s", (image_id,))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Image deleted successfully"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
