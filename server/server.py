import asyncio
import websockets
import ssl
import pathlib
import sqlite3
import pickle


class Connection:
    def __init__(self):
        self.connections = {}
        start_server = websockets.serve(self.msg, 'localhost', 8765)
        self.db = Database()
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def msg(self, websocket, path):
        async for received_message in websocket:
            msg_type, receiver, sender, message = self.parse_message(received_message)

            # Login
            if msg_type == "l":
                if self.db.verify_user(sender, message):
                    await websocket.send("1")
                else:
                    await websocket.send("0")
            # Registration
            elif msg_type == "r":
                if not self.db.find_user(sender):
                    self.db.add_user(sender, message)
                    await websocket.send("1")
                else:
                    await websocket.send("0")
            # Connection
            elif msg_type == "c":
                if sender not in self.connections:
                    self.connections[sender] = websocket
                await websocket.send(pickle.dumps(self.db.find_friends(sender)))
            # Receive a message
            elif msg_type == "m":
                await self.connections[sender].send(sender + ";" + message)
                if sender in self.connections and receiver != sender:
                    await self.connections[receiver].send(sender + ";" + message)
            # Add friend
            elif msg_type == "a":
                if self.db.find_user(message) and not self.db.are_friends(sender, message):
                    self.db.add_friends(sender, message)
                    await websocket.send("1")
                else:
                    await websocket.send("0")

    @staticmethod
    def parse_message(message):
        split_message = message.split(";", 3)
        return split_message[0], split_message[1], split_message[2], split_message[3]


class Database:
    def __init__(self):
        self.user_db = sqlite3.connect("user_info.db")
        self.user_db.execute("CREATE TABLE IF NOT EXISTS user_info (username TEXT PRIMARY KEY, password TEXT)")
        self.user_db.execute("CREATE TABLE IF NOT EXISTS friends (user1 TEXT, user2 TEXT, PRIMARY KEY (user1, user2))")

    def add_user(self, username, password):
        c = self.user_db.cursor()
        c.execute("INSERT INTO user_info VALUES (?, ?)", (username, password))
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
        c.execute("SELECT rowid FROM user_info WHERE username=? AND password=?", (username, password))
        if c.fetchone():
            return True
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


if __name__ == "__main__":
    Connection()
