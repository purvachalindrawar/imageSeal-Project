from flask import Blueprint, request, jsonify, send_file, render_template_string
from utils.db import get_db_connection
from utils.crypto import decrypt_image
from utils.emailer import send_email
import base64, uuid, os, random, string
from io import BytesIO

share_bp = Blueprint("share", __name__)

def generate_token():
    return str(uuid.uuid4())

def generate_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# 📤 Share Image
@share_bp.route("/share", methods=["POST"])
def share_image():
    data = request.json
    image_id = data.get("image_id")
    sender_name = data.get("sender_name")
    receiver_email = data.get("receiver_email")

    if not all([image_id, sender_name, receiver_email]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch image & encryption key
    cur.execute("""
        SELECT i.image_data, u.encryption_key 
        FROM images i 
        JOIN users u ON i.user_id = u.id 
        WHERE i.id = %s
    """, (image_id,))
    row = cur.fetchone()

    if not row:
        return jsonify({"error": "Image not found"}), 404

    encrypted_data, encryption_key = row
    decrypted_data = decrypt_image(encrypted_data, encryption_key)

    # Generate token & password
    token = generate_token()
    password = generate_password()

    # Save share entry
    cur.execute("INSERT INTO shared_links (token, image_id, password) VALUES (%s, %s, %s)", 
                (token, image_id, password))
    conn.commit()
    cur.close()
    conn.close()

    # Send email
    link = f"http://imageseal-securely-store-encrypt-and.onrender.com/shared/{token}"
    subject = "🔗 You've received a secure image from ImageVault"
    message = f"""
Hi,

You’ve received a secure image from {sender_name} via ImageVault.

🔗 Link: {link}
🔐 Password: {password}

Visit the link and enter the password to view and download the image.

Regards,  
ImageVault Team
"""

    send_email(receiver_email, subject, message)

    return jsonify({"message": "Link shared successfully!"}), 200

# 🔓 Page to input password for viewing shared image
@share_bp.route("/shared/<token>", methods=["GET"])
def shared_image_form(token):
    return render_template_string("""
    <html>
    <head>
        <title>Secure Image Access</title>
        <style>
            body {
                background: linear-gradient(to right, #1e3c72, #2a5298);
                font-family: Arial, sans-serif;
                color: white;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding-top: 50px;
            }
            input, button {
                padding: 10px;
                font-size: 16px;
                margin-top: 10px;
                border-radius: 5px;
            }
            img {
                margin-top: 20px;
                max-width: 90%;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(255,255,255,0.2);
            }
        </style>
    </head>
    <body>
        <h2>🔐 Enter Password to View Image</h2>
        <form id="passwordForm">
            <input type="password" id="password" placeholder="Enter password" required>
            <button type="submit">View Image</button>
        </form>
        <div id="imageContainer"></div>

        <script>
        document.getElementById('passwordForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const password = document.getElementById('password').value;
            const response = await fetch("", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ password })
            });

            const data = await response.json();
            const container = document.getElementById('imageContainer');
            container.innerHTML = "";

            if (response.ok) {
                const img = document.createElement("img");
                img.src = "data:image/png;base64," + data.image;
                container.appendChild(img);

                const download = document.createElement("a");
                download.href = img.src;
                download.download = "secure-image.png";
                download.innerText = "📥 Download Image";
                download.style.display = "block";
                download.style.marginTop = "10px";
                container.appendChild(download);
            } else {
                const msg = document.createElement("p");
                msg.innerText = data.error || "Invalid password";
                msg.style.color = "red";
                container.appendChild(msg);
            }
        });
        </script>
    </body>
    </html>
    """)

# 🔐 POST: View shared image using password
@share_bp.route("/shared/<token>", methods=["POST"])
def view_shared_image(token):
    password = request.json.get("password")

    conn = get_db_connection()
    cur = conn.cursor()

    # Validate token and password
    cur.execute("SELECT image_id FROM shared_links WHERE token = %s AND password = %s", (token, password))
    row = cur.fetchone()

    if not row:
        return jsonify({"error": "Invalid link or password"}), 403

    image_id = row[0]

    # Fetch image
    cur.execute("""
        SELECT i.image_data, u.encryption_key 
        FROM images i 
        JOIN users u ON i.user_id = u.id 
        WHERE i.id = %s
    """, (image_id,))
    img_row = cur.fetchone()
    cur.close()
    conn.close()

    if not img_row:
        return jsonify({"error": "Image not found"}), 404

    encrypted_data, encryption_key = img_row
    decrypted_data = decrypt_image(encrypted_data, encryption_key)
    encoded = base64.b64encode(decrypted_data).decode("utf-8")

    return jsonify({"image": encoded}), 200
