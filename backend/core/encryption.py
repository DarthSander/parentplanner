from cryptography.fernet import Fernet

from core.config import settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        if not settings.TOKEN_ENCRYPTION_KEY:
            raise RuntimeError(
                "TOKEN_ENCRYPTION_KEY is niet geconfigureerd. "
                "Genereer met: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        _fernet = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
    return _fernet


def encrypt_token(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
