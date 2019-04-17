import asyncio
import websockets
import ssl
import pathlib
import sqlite3


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
            # Receive a message
            elif msg_type == "m":
                await self.connections[sender].send(sender + ";" + message)
                if sender in self.connections and receiver != sender:
                    await self.connections[receiver].send(sender + ";" + message)

    @staticmethod
    def parse_message(message):
        split_message = message.split(";", 3)
        return split_message[0], split_message[1], split_message[2], split_message[3]


class Database:
    def __init__(self):
        self.user_db = sqlite3.connect("user_info.db")
        self.user_db.execute("CREATE TABLE IF NOT EXISTS user_info (username TEXT, password TEXT)")

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


if __name__ == "__main__":
    Connection()
