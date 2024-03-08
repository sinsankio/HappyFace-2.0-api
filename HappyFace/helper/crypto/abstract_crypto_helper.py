from abc import ABC, abstractmethod


class AbstractCryptoHelper(ABC):
    @abstractmethod
    def encrypt(self, content: str):
        pass

    @abstractmethod
    def decrypt(self, content: str):
        pass
