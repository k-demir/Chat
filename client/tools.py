"""
Contains tools for the client to use.
"""

import random
import base64
import pickle
import threading
import asyncio
import websockets
import sys
import time
from os import urandom
from cryptography.fernet import Fernet


# ------------------ File manager ------------------


class FileManager:
    """Manages saving and loading the chats and the Diffie-Hellman keys."""

    def __init__(self, controller):
        """Constructor.

        Args:
            controller: An instance of the Controller class.
        """
        self.controller = controller

    def load(self):
        """Loads the chats and Diffie-Hellman keys from a pickle file."""
        try:
            f = open(self.controller.username + ".pickle", "rb")
            f.close()
        except IOError:
            f = open(self.controller.username + ".pickle", "wb+")
            f.close()
        with open(self.controller.username + ".pickle", "rb") as file:
            try:
                loaded_keys, loaded_chats = pickle.load(file)
                self.controller.keys = loaded_keys
                self.controller.chats = loaded_chats
            except EOFError:
                self.controller.keys = {}
                self.controller.chats = {}

    def save(self):
        """Saves the chats and Diffie-Hellman keys to a pickle file."""
        if self.controller.username:
            with open(self.controller.username + ".pickle", "wb+") as file:
                pickle.dump((self.controller.keys, self.controller.chats), file)


# ------------------ Saver thread ------------------

class AutoSaver(threading.Thread):
    """A thread that saves the keys and chats periodically."""

    def __init__(self, frequency, file_manager):
        """Constructor.

        Args:
            frequency: The frequency of autosaving in seconds.
            file_manager: An instance of the FileManager class.
        """
        threading.Thread.__init__(self)
        self.freq = frequency
        self.file_manager = file_manager

    def run(self):
        """Sleeps for the specified amount of seconds between autosaves."""
        time.sleep(self.freq)
        self.file_manager.save()


# ------------------ Clean up ------------------

class CleanUp:
    """Handles clean up when disconnecting."""

    def __init__(self, controller):
        """Constructor.

        Args:
            controller: An instance of the Controller class.
        """
        self.controller = controller

    def disconnect(self):
        """Initiates the disconnection process."""
        asyncio.get_event_loop().run_until_complete(self.send_disconnect_request())

    async def send_disconnect_request(self):
        """Sends the disconnection request to the server."""
        async with websockets.connect(self.controller.ws_uri) as websocket:
            if self.controller.username:
                await websocket.send("g;;" + self.controller.username + ";")
            else:
                await websocket.send("g;;" + self.controller.connection_id + ";")


# ------------------ Encryption ------------------


class Encryption:
    """Contains methods for Diffie-Hellman key exchange, encryption and decryption."""

    # 2048-bit prime for Diffie-Hellman key exchange
    p = int("FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
            "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
            "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
            "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
            "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
            "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
            "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
            "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
            "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
            "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
            "15728E5A8AACAA68FFFFFFFFFFFFFFFF", 16)

    # 1536-bit prime for Diffie-Hellman key exchange
    p_s = int("FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
              "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
              "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
              "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
              "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
              "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
              "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
              "670C354E4ABC9804F1746C08CA237327FFFFFFFFFFFFFFFF", 16)
    g = 2
    private_keys = {}

    @classmethod
    def get_diffie_hellman(cls, friend):
        """Returns the Diffie-Hellman public key that is sent to the other user through the server.

        Args:
            friend: The username of the other user.
            username: The username of the current user.
            ws_uri: The location of the server
        """
        if friend not in cls.private_keys:
            cls.add_private_key(friend, 160)
        return str(pow(cls.g, cls.private_keys[friend], cls.p))

    @classmethod
    def receive_diffie_hellman(cls, friend, received_key):
        """Computes the shared key from the received Diffie-Hellman public key.

        Args:
            friend: The username of the key sender.
            received_key: The received public key.

        Returns:
            The computed shared key.
        """
        if friend not in cls.private_keys:
            cls.add_private_key(friend, 160)
        return pow(int(received_key), cls.private_keys[friend], cls.p)

    @classmethod
    async def diffie_hellman_to_server(cls, connection_id, connection_secret_key, ws_uri):
        """Performs the Diffie-Hellman key exchange with the server before logging in.

        Args:
            connection_id: The connection id from an instance of the Controller class.
            connection_secret_key: The connection secret key from an instance of the Controller class.
            ws_uri: The location of the server.

        Returns:
            The computed shared key.
        """
        async with websockets.connect(ws_uri) as ws:
            await ws.send("s;;" + connection_id + ";" + str(pow(cls.g, connection_secret_key, cls.p_s)))
            received_key = await ws.recv()
            return pow(int(received_key), connection_secret_key, cls.p_s)

    @classmethod
    def add_private_key(cls, friend, n_bits):
        """Creates and adds a private key to the static private_keys variable.

        Args:
            friend: The username of the other user.
            n_bits: The length of the created key.
        """
        cls.private_keys[friend] = int.from_bytes(urandom(n_bits), sys.byteorder)

    @staticmethod
    def encrypt(message, key):
        """Encrypts a message that is sent to another user.

        Args:
            message: The message.
            key: The Diffie-Hellman key that is shared between the users.

        Returns:
            The encrypted message.
        """
        random.seed(key)
        k = base64.urlsafe_b64encode(bytearray(random.getrandbits(8) for _ in range(32)))
        f = Fernet(k)
        return f.encrypt(bytes(message, encoding="UTF-8")).decode("UTF-8")

    @staticmethod
    def decrypt(message, key):
        """Decrypts a message that is received from another user.

        Args:
            message: The message.
            key: The Diffie-Hellman key that is shared between the users.

        Returns:
            The decrypted message.
        """
        random.seed(key)
        k = base64.urlsafe_b64encode(bytearray(random.getrandbits(8) for _ in range(32)))
        f = Fernet(k)
        return f.decrypt(message.encode("UTF-8")).decode()
