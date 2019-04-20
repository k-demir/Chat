"""
Contains tools for the server to use.
"""

import sys
import random
import base64
import hashlib
import binascii
from os import urandom
from cryptography.fernet import Fernet
import sqlite3


class Encryption:
    """Methods for Diffie-Hellman key exchange, message encrypting and password hashing."""

    # 1536-bit prime for Diffie-Hellman key exchange
    p_s = int("FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
              "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
              "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
              "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
              "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
              "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
              "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
              "670C354E4ABC9804F1746C08CA237327FFFFFFFFFFFFFFFF", 16)
    #
    g = 2
    private_keys = {}

    @classmethod
    def get_diffie_hellman_key(cls, client):
        """Returns the Diffie-Hellman public key that is sent to the other party.

        Args:
            client: Name of the other party.
        Returns:
            The Diffie-Hellman public key.
        """
        if client not in cls.private_keys:
            cls.add_private_key(client, 120)
        return str(pow(cls.g, cls.private_keys[client], cls.p_s))

    @classmethod
    async def receive_diffie_hellman_from_client(cls, client, received_key):
        """Returns the shared key that is computed from the received Diffie-Hellman public key.

        Args:
            client: Name of the other party.
            received_key: The public key received from the other party.
        Returns:
            The Diffie-Hellman shared key.
        """
        if client not in cls.private_keys:
            await cls.add_private_key(client, 120)
        return pow(int(received_key), cls.private_keys[client], cls.p_s)

    @classmethod
    async def add_private_key(cls, client, n_bits):
        """Adds a random private key for the Diffie-Hellman key exchange between a client.

        Args:
            client: Name of the other party.
            n_bits: The length of the key in bits.
        """
        cls.private_keys[client] = int.from_bytes(urandom(n_bits), sys.byteorder)

    @staticmethod
    def decrypt(message, client_key):
        """Decrypts and returns the message with a given key.

        Args:
            message: The encrypted message.
            client_key: The key used for the decryption.
        Returns:
            The decrypted message.
        """
        random.seed(client_key)
        k = base64.urlsafe_b64encode(bytearray(random.getrandbits(8) for _ in range(32)))
        f = Fernet(k)
        return f.decrypt(message.encode("UTF-8")).decode()

    @staticmethod
    def hash_password(password, salt=None):
        """Uses PBKDF2-HMAC-SHA512 password hashing with 100 000 iterations to hash the given password.

        Args:
            password: The password that will be hashed.
            salt: The salt used to hash the password. If None, a random 16-bit salt is generated.
        Returns:
            A tuple of the hashed password and the used salt.
        """
        if not salt:
            salt = urandom(16)
        hashed_password = hashlib.pbkdf2_hmac("sha512", bytes(password, "utf-8"), salt, 100000)
        return binascii.hexlify(hashed_password), salt


class Database:
    """Contains database operations that the server needs."""

    def __init__(self):
        """Constructor."""
        self.user_db = sqlite3.connect("user_info.db")
        self.user_db.execute("CREATE TABLE IF NOT EXISTS user_info (username TEXT PRIMARY KEY,password BLOB,salt BLOB)")
        self.user_db.execute("CREATE TABLE IF NOT EXISTS friends (user1 TEXT, user2 TEXT, PRIMARY KEY (user1, user2))")

    def add_user(self, username, password):
        """Adds a user to the database.

        Args:
            username: The name of the added user.
            password: The unhashed password of the user.
        """
        username = username.lower()
        hashed_password, salt = Encryption.hash_password(password)

        c = self.user_db.cursor()
        c.execute("INSERT INTO user_info VALUES (?, ?, ?)", (username, hashed_password, salt))
        self.user_db.commit()

    def find_user(self, username):
        """Checks if the user is in the database.

        Args:
            username: The name of the searched user.
        Returns:
            None if the username is not in the database, row id if the user is found.
        """
        username = username.lower()
        c = self.user_db.cursor()
        c.execute("SELECT rowid FROM user_info WHERE username=?", (username,))
        ret = c.fetchone()
        if not ret:
            return None
        return ret[0]

    def verify_user(self, username, password):
        """Verifies that the given username and password are in the database.

        Args:
            username: The name of the searched user.
            password: The password of the searched user.
        Returns:
            True if the username and password are correct, False otherwise.
        """
        username = username.lower()
        c = self.user_db.cursor()
        c.execute("SELECT password, salt FROM user_info WHERE username=?", (username,))
        try:
            found_hashed_password, salt = c.fetchone()
            hashed_password, _ = Encryption.hash_password(password, salt)
            if found_hashed_password == hashed_password:
                return True
            return False
        except TypeError:
            return False

    def add_friends(self, user_1, user_2):
        """Adds two users as friends to the database.

        Args:
            user_1: The username of the first user.
            user_2: The username of the second user.
        """
        user_1, user_2 = user_1.lower(), user_2.lower()
        c = self.user_db.cursor()
        if not self.are_friends(user_1, user_2):
            c.execute("INSERT INTO friends VALUES (?, ?)", (user_1, user_2))
            self.user_db.commit()

    def are_friends(self, user_1, user_2):
        """Checks whether the two users are friends.

        Args:
            user_1: The username of the first user.
            user_2: The username of the second user.
        Returns:
            True if the users are friends, False if they are not.
        """
        user_1, user_2 = user_1.lower(), user_2.lower()
        c = self.user_db.cursor()
        c.execute("SELECT rowid FROM friends WHERE (user1=? AND user2=?) OR (user1=? AND user2=?)",
                  (user_1, user_2, user_2, user_1))
        if c.fetchone():
            return True
        return False

    def find_friends(self, user):
        """Finds all friends of the given user.

        Args:
            user: The name of the given user.
        Returns:
            A list containing all of the friends of the user.
        """
        user = user.lower()
        friends = []
        c = self.user_db.cursor()
        c.execute("SELECT user1 FROM friends WHERE user2=?", (user,))
        res = c.fetchall()
        if res:
            friends += [friend[0] for friend in res]
        c.execute("SELECT user2 FROM friends WHERE user1=?", (user,))
        res = c.fetchall()
        if res:
            friends += [friend[0] for friend in res]
        return friends
