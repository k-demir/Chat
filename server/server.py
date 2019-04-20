import asyncio
import websockets
import sqlite3
import pickle
import random
import base64
from cryptography.fernet import Fernet
from os import urandom
import sys
import hashlib
import binascii


keys = {}


class Connection:
    def __init__(self):
        self.connections = {}
        start_server = websockets.serve(self.msg, 'localhost', 8765)
        self.db = Database()
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def msg(self, websocket, path):
        try:
            async for received_message in websocket:
                global keys
                msg_type, receiver, sender, message = self.parse_message(received_message)

                # Login
                if msg_type == "l":
                    message = Encryption.decrypt(message, sender)
                    username, password = message.split("@", 1)
                    if self.db.verify_user(username, password):
                        keys[username] = keys[sender]
                        keys.pop(sender)
                        await websocket.send("1")
                    else:
                        await websocket.send("0")
                # Registration
                elif msg_type == "r":
                    message = Encryption.decrypt(message, sender)
                    username, password = message.split("@", 1)
                    if not self.db.find_user(username):
                        self.db.add_user(username, password)
                        await websocket.send("1")
                    else:
                        await websocket.send("0")
                # Connection
                elif msg_type == "c":
                    if sender not in self.connections:
                        self.connections[sender] = websocket
                    online_friends = self.find_online_friends(sender)
                    await websocket.send(pickle.dumps(online_friends))
                    for friend, online in online_friends.items():
                        if online:
                            await self.connections[friend].send("c+" + sender + ";1")
                # Receive a message
                elif msg_type == "m":
                    if receiver in self.connections and receiver != sender:
                        await self.connections[sender].send(sender + ">" + receiver + ";" + message)
                        await self.connections[receiver].send(sender + ">" + sender + ";" + message)
                # Add friend
                elif msg_type == "a":
                    if self.db.find_user(receiver) and not self.db.are_friends(sender, receiver):
                        self.db.add_friends(sender, receiver)
                        if receiver in self.connections:
                            await self.connections[receiver].send("a+" + sender + ";")
                        await websocket.send("1")
                    else:
                        await websocket.send("0")
                # Diffie-Hellman key exchange between clients
                elif msg_type == "d":
                    if receiver in self.connections:
                        await self.connections[receiver].send("d+" + sender + ";" + message)
                # Diffie-Hellman exchange between server and a client
                elif msg_type == "s":
                    await Encryption.receive_diffie_hellman_from_client(sender, message)
                    await websocket.send(Encryption.get_diffie_hellman_key(sender))
                # Disconnection request
                elif msg_type == "g":
                    try:
                        self.connections.pop(sender)
                        online_friends = self.find_online_friends(sender)
                        for friend, online in online_friends.items():
                            if online:
                                await self.connections[friend].send("c+" + sender + ";0")
                        keys.pop(sender)
                    except KeyError:
                        continue

        except websockets.ConnectionClosed:
            pass

    def find_online_friends(self, user):
        ret = {}
        friends = self.db.find_friends(user)
        for friend in friends:
            if friend in self.connections:
                ret[friend] = 1
            else:
                ret[friend] = 0
        return ret

    @staticmethod
    def parse_message(message):
        split_message = message.split(";", 3)
        return split_message[0], split_message[1], split_message[2], split_message[3]


class Database:
    def __init__(self):
        self.user_db = sqlite3.connect("user_info.db")
        self.user_db.execute("CREATE TABLE IF NOT EXISTS user_info (username TEXT PRIMARY KEY,password BLOB,salt BLOB)")
        self.user_db.execute("CREATE TABLE IF NOT EXISTS friends (user1 TEXT, user2 TEXT, PRIMARY KEY (user1, user2))")

    def add_user(self, username, password):
        hashed_password, salt = Encryption.hash_password(password)

        c = self.user_db.cursor()
        c.execute("INSERT INTO user_info VALUES (?, ?, ?)", (username, hashed_password, salt))
        self.user_db.commit()
        return self.find_user(username)

    def find_user(self, username):
        c = self.user_db.cursor()
        c.execute("SELECT rowid FROM user_info WHERE username=?", (username,))
        ret = c.fetchone()
        if not ret:
            return None
        return ret[0]

    def verify_user(self, username, password):
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
        c = self.user_db.cursor()
        if not self.are_friends(user_1, user_2):
            c.execute("INSERT INTO friends VALUES (?, ?)", (user_1, user_2))
            self.user_db.commit()

    def are_friends(self, user_1, user_2):
        c = self.user_db.cursor()
        c.execute("SELECT rowid FROM friends WHERE (user1=? AND user2=?) OR (user1=? AND user2=?)",
                  (user_1, user_2, user_2, user_1))
        if c.fetchone():
            return True
        return False

    def find_friends(self, user):
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


class Encryption:

    # 1536-bit prime for client-to-server encryption
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
    def get_diffie_hellman_key(cls, client):
        if client not in cls.private_keys:
            cls.add_private_key(client, 120)
        return str(pow(cls.g, cls.private_keys[client], cls.p_s))

    @classmethod
    async def receive_diffie_hellman_from_client(cls, client, received_key):
        if client not in cls.private_keys:
            await cls.add_private_key(client, 120)
        global keys
        keys[client] = pow(int(received_key), cls.private_keys[client], cls.p_s)

    @classmethod
    async def add_private_key(cls, friend, n_bits):
        cls.private_keys[friend] = int.from_bytes(urandom(n_bits), sys.byteorder)

    @staticmethod
    def decrypt(message, client):
        random.seed(keys[client])
        k = base64.urlsafe_b64encode(bytearray(random.getrandbits(8) for _ in range(32)))
        f = Fernet(k)
        return f.decrypt(message.encode("UTF-8")).decode()

    @staticmethod
    def hash_password(password, salt=None):
        if not salt:
            salt = urandom(16)
        hashed_password = hashlib.pbkdf2_hmac("sha512", bytes(password, "utf-8"), salt, 100000)
        return binascii.hexlify(hashed_password), salt


if __name__ == "__main__":
    Connection()
