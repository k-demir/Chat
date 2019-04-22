"""
Contains the server functionality.
"""

import asyncio
import websockets
import pickle

from server_tools import Encryption, Database


class Server:
    """Initializes the server and handles the connections. """

    def __init__(self, hostname="localhost", port=8765):
        """Constructor.

        Args:
            hostname: The hostname. Default value "localhost".
            port: The port for the websocket connections. Default value 8765.
        """
        self.connections = {}
        self.db = Database()
        self.keys = {}

        start_server = websockets.serve(self.msg, hostname, port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def msg(self, websocket, _):
        """Handles the received messages."""
        try:
            async for received_message in websocket:
                msg_type, receiver, sender, message = self.parse_message(received_message)

                # Login
                if msg_type == "l":
                    message = Encryption.decrypt(message, self.keys[sender])
                    username, password = message.split("@", 1)
                    if self.db.verify_user(username, password):
                        self.keys[username] = self.keys[sender]
                        self.keys.pop(sender)
                        await websocket.send("1")
                    else:
                        await websocket.send("0")
                # Registration
                elif msg_type == "r":
                    message = Encryption.decrypt(message, self.keys[sender])
                    username, password = message.split("@", 1)
                    if not self.db.find_user(username):
                        self.db.add_user(username, password)
                        await websocket.send("1")
                    else:
                        await websocket.send("0")
                # Connection
                elif msg_type == "c":
                    if sender.lower() not in self.connections:
                        self.connections[sender.lower()] = websocket
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
                    if self.db.find_user(receiver) and receiver.lower() in self.connections\
                            and not self.db.are_friends(sender, receiver):
                        self.db.add_friends(sender, receiver)
                        if receiver.lower() in self.connections:
                            await self.connections[receiver.lower()].send("a+" + sender + ";")
                        await websocket.send("1")
                    else:
                        await websocket.send("0")
                # Diffie-Hellman key exchange between clients
                elif msg_type == "d":
                    if receiver.lower() in self.connections:
                        await self.connections[receiver.lower()].send("d+" + sender + ";" + message)
                # Diffie-Hellman exchange between server and a client
                elif msg_type == "s":
                    self.keys[sender] = await Encryption.receive_diffie_hellman_from_client(sender, message)
                    await websocket.send(Encryption.get_diffie_hellman_key(sender))
                # Disconnection request
                elif msg_type == "g":
                    try:
                        self.connections.pop(sender.lower())
                        online_friends = self.find_online_friends(sender)
                        for friend, online in online_friends.items():
                            if online:
                                await self.connections[friend].send("c+" + sender + ";0")
                        self.keys.pop(sender)
                    except KeyError:
                        continue

        except websockets.ConnectionClosed:
            pass

    def find_online_friends(self, user):
        """Returns the friends of the given user and their online status.

        Args:
            user: The name of the given user.
        Returns:
            A dict with the usernames as keys and values 1 denoting online and 0 denoting offline.
        """
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
        """Parses the received message into 4 parts that are separated by ";".

        Args:
            message: The message to be parsed.
        Returns:
            A tuple containing the four parsed parts.
        """
        split_message = message.split(";", 3)
        return split_message[0], split_message[1], split_message[2], split_message[3]


if __name__ == "__main__":
    Server()
