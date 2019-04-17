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
            receiver, sender, message = self.parse_message(received_message)

            sender_id = self.db.find_user(sender)

            if not sender_id:
                sender_id = self.db.add_user(sender, "password")

            if str(sender_id) not in self.connections:
                self.connections[str(sender_id)] = websocket
                continue

            receiver_id = self.db.find_user(receiver)

            await self.connections[str(sender_id)].send(sender + ";" + message)
            if str(receiver_id) in self.connections and receiver != sender:
                await self.connections[str(receiver_id)].send(sender + ";" + message)

    @staticmethod
    def parse_message(message):
        split_message = message.split(";", 2)
        return split_message[0], split_message[1], split_message[2]


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


if __name__ == "__main__":
    Connection()
