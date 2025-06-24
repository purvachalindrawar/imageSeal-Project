from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

def pad(data):
    return data + b"\0" * (AES.block_size - len(data) % AES.block_size)

def encrypt_image(data, key):
    data = pad(data)
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(data)
    return base64.b64encode(encrypted)

def decrypt_image(encrypted_data, key):
    encrypted_data = base64.b64decode(encrypted_data)
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.decrypt(encrypted_data).rstrip(b"\0")
