# app.utils.crypto | Шифрование токенов пользователей | Rasvet Post Bot
from cryptography.fernet import Fernet
from app.config import Config


class Crypto:

    def __init__(self):
        self.cipher = Fernet(Config.ENCRYPTION_KEY.encode())

    def encrypt(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        return self.cipher.decrypt(value.encode()).decode()


crypto = Crypto()