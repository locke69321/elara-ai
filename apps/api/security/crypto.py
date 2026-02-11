import json
from dataclasses import dataclass

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover - dependency availability is runtime-specific
    Fernet = None  # type: ignore[assignment]
    InvalidToken = Exception  # type: ignore[assignment]


@dataclass(frozen=True)
class EncryptedEnvelope:
    key_id: str
    ciphertext: str


class EnvelopeCipher:
    """Field-level envelope encryption for sensitive payloads."""

    def __init__(self, *, key_id: str, key_material: str) -> None:
        if Fernet is None:
            raise RuntimeError("cryptography is required for EnvelopeCipher")

        self.key_id = key_id
        self._fernet = Fernet(key_material.encode("utf-8"))

    @staticmethod
    def generate_data_key() -> str:
        if Fernet is None:
            raise RuntimeError("cryptography is required for key generation")
        return Fernet.generate_key().decode("utf-8")

    def encrypt_payload(self, payload: dict[str, object]) -> EncryptedEnvelope:
        serialized = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        token = self._fernet.encrypt(serialized).decode("utf-8")
        return EncryptedEnvelope(key_id=self.key_id, ciphertext=token)

    def decrypt_payload(self, envelope: EncryptedEnvelope) -> dict[str, object]:
        if envelope.key_id != self.key_id:
            raise ValueError("key id mismatch")

        try:
            decrypted = self._fernet.decrypt(envelope.ciphertext.encode("utf-8"))
        except InvalidToken as exc:
            raise ValueError("unable to decrypt payload") from exc

        return json.loads(decrypted)
