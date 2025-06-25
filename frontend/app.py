import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="ImageVault", layout="wide")

# 🎨 Styling
st.markdown("""
    <style>
        .main {
            background: linear-gradient(to right, #1e3c72, #2a5298);
            color: white;
        }
        .profile-pic {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            border: 2px solid white;
            object-fit: cover;
        }
        .welcome-container {
            text-align: center;
            margin-bottom: 20px;
        }
        .stButton > button:hover {
            background-color: #ffffff22;
        }
    </style>
""", unsafe_allow_html=True)

# Session State
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "upload"

# Welcome UI
def show_welcome_ui():
    st.markdown(f"""
        <div class="welcome-container">
            <img class="profile-pic" src="https://cdn-icons-png.flaticon.com/512/921/921347.png" alt="profile">
            <h2 style="color:white;">🎉 Welcome to ImageSeal: Securely store, encrypt, and share images with controlled access!</h2>
            <p style="color:white;">Logged in as <b>{st.session_state.user_email}</b></p>
        </div>
    """, unsafe_allow_html=True)

# Toggle
mode = st.sidebar.radio("Choose Mode", ["Login", "Signup"])

# Signup
if mode == "Signup" and not st.session_state.user_email:
    st.title("🔐 Create Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Signup"):
        res = requests.post("http://imageseal-securely-store-encrypt-and.onrender.com/auth/signup", json={"email": email, "password": password})
        if res.status_code == 201:
            st.success("Signup successful! Please login.")
        else:
            st.error(res.json().get("error", "Signup failed"))

# Login
if mode == "Login" and not st.session_state.user_email:
    st.title("🔓 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        res = requests.post("http://imageseal-securely-store-encrypt-and.onrender.com/auth/login", json={"email": email, "password": password})
        if res.status_code == 200:
            st.session_state.user_email = email
            st.session_state.user_id = res.json()["user_id"]
            st.success("Login successful!")
        else:
            st.error(res.json().get("error", "Login failed"))

# Sidebar
if st.session_state.user_email:
    show_welcome_ui()
    st.sidebar.markdown("---")
    st.sidebar.subheader("Dashboard")
    if st.sidebar.button("Upload Image"):
        st.session_state.view_mode = "upload"
    if st.sidebar.button("My Images"):
        st.session_state.view_mode = "view"

# Upload Section
if st.session_state.user_email and st.session_state.view_mode == "upload":
    st.title("📤 Upload Your Image")

    upload_type = st.radio("Choose upload method", ["From File", "From URL", "Paste Image"])
    image_data = None

    if upload_type == "From File":
        uploaded_file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            image_data = uploaded_file.getvalue()
            st.image(image_data, caption="Preview")

    elif upload_type == "From URL":
        url = st.text_input("Paste image URL")
        if url and st.button("Fetch Image"):
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    image_data = resp.content
                    st.session_state.fetched_image = image_data
                    st.image(image_data, caption="Preview")
                else:
                    st.error("Failed to fetch image from URL")
            except:
                st.error("Invalid URL")

        if "fetched_image" in st.session_state:
            if st.button("Upload"):
                files = {"image": st.session_state.fetched_image}
                res = requests.post(f"http://imageseal-securely-store-encrypt-and.onrender.com/upload?user_id={st.session_state.user_id}", files=files)
                if res.status_code == 200:
                    st.success("Image uploaded successfully!")
                    del st.session_state.fetched_image
                    st.session_state.view_mode = "view"
                    st.rerun()
                else:
                    st.error(res.json().get("error", "Upload failed"))

    elif upload_type == "Paste Image":
        st.info("Paste your image here (Ctrl+V).")
        uploaded_file = st.camera_input("Paste or capture an image")
        if uploaded_file:
            image_data = uploaded_file.getvalue()
            st.image(image_data, caption="Preview")

    if image_data:
        if st.button("Upload"):
            files = {"image": image_data}
            res = requests.post(f"http://imageseal-securely-store-encrypt-and.onrender.com/upload?user_id={st.session_state.user_id}", files=files)
            if res.status_code == 200:
                st.success("Image uploaded successfully!")
                st.session_state.view_mode = "view"
                st.rerun()
            else:
                st.error(res.json().get("error", "Upload failed"))

# Gallery View
def show_images():
    st.title("🖼️ My Gallery")
    res = requests.get(f"http://imageseal-securely-store-encrypt-and.onrender.com/images?email={st.session_state.user_email}")
    if res.status_code == 200:
        images = res.json().get("images", [])
        if not images:
            st.info("No images uploaded yet.")
        else:
            cols = st.columns(3)
            for i, img_obj in enumerate(images):
                with cols[i % 3]:
                    st.image(base64.b64decode(img_obj["data"]), use_column_width=True)

                    # Delete button
                    if st.button("🗑️ Delete", key=f"delete_{img_obj['id']}_{i}"):
                        delete = requests.delete(f"http://imageseal-securely-store-encrypt-and.onrender.com/image/{img_obj['id']}")
                        if delete.status_code == 200:
                            st.success("Image deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete image")

                    # Share toggle
                    with st.expander("🔗 Share this image", expanded=False):
                        sender_name = st.text_input("Your name", key=f"sender_{img_obj['id']}_{i}")
                        receiver_email = st.text_input("Receiver's email", key=f"receiver_{img_obj['id']}_{i}")
                        if st.button("Send Secure Link", key=f"send_{img_obj['id']}_{i}"):
                            if sender_name and receiver_email:
                                payload = {
                                    "image_id": img_obj["id"],
                                    "sender_name": sender_name,
                                    "receiver_email": receiver_email
                                }
                                res = requests.post("http://imageseal-securely-store-encrypt-and.onrender.com/share", json=payload)
                                if res.status_code == 200:
                                    st.success("✅ Secure link shared via email!")
                                else:
                                    st.error("Failed to share image.")
                            else:
                                st.warning("Please fill in all fields.")
    else:
        st.error(res.json().get("error", "Could not fetch images"))

if st.session_state.user_email and st.session_state.view_mode == "view":
    show_images()
