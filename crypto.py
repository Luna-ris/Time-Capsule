import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from config import ENCRYPTION_KEY_BYTES

def encrypt_data_aes(data: str) -> str:
    """Шифрование данных с помощью AES."""
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY_BYTES), modes.CBC(iv), backend=default_backend())
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data.encode('utf-8')) + padder.finalize()
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return (iv + encrypted).hex()

def decrypt_data_aes(encrypted_hex: str) -> str:
    """Дешифрование данных с помощью AES."""
    data = bytes.fromhex(encrypted_hex)
    iv, encrypted = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY_BYTES), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    unpadded = unpadder.update(decrypted) + unpadder.finalize()
    return unpadded.decode('utf-8')
