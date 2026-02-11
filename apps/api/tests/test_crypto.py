import unittest

from apps.api.security.crypto import EncryptedEnvelope, EnvelopeCipher


class EnvelopeCipherTest(unittest.TestCase):
    def test_encrypt_and_decrypt_round_trip(self) -> None:
        key = EnvelopeCipher.generate_data_key()
        cipher = EnvelopeCipher(key_id="k1", key_material=key)

        encrypted = cipher.encrypt_payload({"note": "secret", "count": 2})
        decrypted = cipher.decrypt_payload(encrypted)

        self.assertEqual(decrypted["note"], "secret")
        self.assertEqual(decrypted["count"], 2)

    def test_key_id_mismatch_raises(self) -> None:
        key = EnvelopeCipher.generate_data_key()
        cipher = EnvelopeCipher(key_id="k1", key_material=key)
        encrypted = cipher.encrypt_payload({"a": 1})

        wrong_envelope = EncryptedEnvelope(
            key_id="k2",
            ciphertext=encrypted.ciphertext,
        )

        with self.assertRaises(ValueError):
            cipher.decrypt_payload(wrong_envelope)

    def test_non_object_payload_raises(self) -> None:
        key = EnvelopeCipher.generate_data_key()
        cipher = EnvelopeCipher(key_id="k1", key_material=key)

        list_ciphertext = cipher._fernet.encrypt(b"[1,2,3]").decode("utf-8")
        envelope = EncryptedEnvelope(key_id="k1", ciphertext=list_ciphertext)

        with self.assertRaises(ValueError):
            cipher.decrypt_payload(envelope)


if __name__ == "__main__":
    unittest.main()
