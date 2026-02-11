import json
from dataclasses import dataclass
from typing import cast

from cryptography.fernet import Fernet, InvalidToken


@dataclass(frozen=True)
class EncryptedEnvelope:
    key_id: str
    ciphertext: str


class EnvelopeCipher:
    """Field-level envelope encryption for sensitive payloads."""

    def __init__(self, *, key_id: str, key_material: str) -> None:
        self.key_id = key_id
        self._fernet = Fernet(key_material.encode("utf-8"))

    @staticmethod
    def generate_data_key() -> str:
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

        decoded = json.loads(decrypted)
        if not isinstance(decoded, dict):
            raise ValueError("encrypted payload must decode to a JSON object")
        return cast(dict[str, object], decoded)
