import unittest
from client.tools import Encryption


class TestEncryption(unittest.TestCase):

    def test_encryption(self):
        """Tests whether the Diffie-Hellman key exchange and the encryption works or not"""

        e1 = Encryption()
        e2 = Encryption()

        public_key_e1 = e1.get_diffie_hellman("e2")
        public_key_e2 = e2.get_diffie_hellman("e1")

        shared_key_1 = e1.receive_diffie_hellman("e2", public_key_e2)
        shared_key_2 = e2.receive_diffie_hellman("e1", public_key_e1)

        self.assertEqual(shared_key_1, shared_key_2)

        message = "test123"

        sent_message = Encryption.encrypt(message, shared_key_1)
        received_message = Encryption.decrypt(sent_message, shared_key_2)

        self.assertEqual(received_message, message)


if __name__ == "__main__":
    unittest.main()