from cryptography.fernet import Fernet

def encrypt_image(image_data, key):
    fernet = Fernet(key)
    return fernet.encrypt(image_data)

def decrypt_image(encrypted_data, key):
    fernet = Fernet(key)

    # ✅ Ensure the encrypted_data is of type `bytes`
    if isinstance(encrypted_data, memoryview):
        encrypted_data = encrypted_data.tobytes()

    return fernet.decrypt(encrypted_data)

def generate_encryption_key():
    return Fernet.generate_key().decode()
