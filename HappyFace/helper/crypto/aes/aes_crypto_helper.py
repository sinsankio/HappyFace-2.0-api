from cryptography.fernet import Fernet, InvalidToken

from helper.crypto.abstract_crypto_helper import AbstractCryptoHelper


class AesCryptoHelper(AbstractCryptoHelper):
    def __init__(self, key_str: str):
        byte_key = key_str.encode("utf-8")
        self.__key = Fernet(byte_key)

    @property
    def key(self) -> Fernet:
        return self.__key

    def encrypt(self, content: str) -> str:
        encrypted_content = self.key.encrypt(content.encode())
        return encrypted_content.decode()

    def decrypt(self, content: str) -> str:
        try:
            encrypted_content = content.encode("utf-8")
            decrypted_content = self.key.decrypt(encrypted_content)
            return decrypted_content.decode()
        except InvalidToken:
            return ""
