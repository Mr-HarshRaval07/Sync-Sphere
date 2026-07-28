from abc import ABC, abstractmethod

class SecretProvider(ABC):
    """Abstract interface defining encryption and decryption operations."""
    
    @abstractmethod
    def encrypt(self, plain_text: str, key_context: str) -> str:
        """Encrypts data string using contextual tenant encryption keys."""
        pass

    @abstractmethod
    def decrypt(self, cipher_text: str, key_context: str) -> str:
        """Decrypts data string using contextual tenant encryption keys."""
        pass
