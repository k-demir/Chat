import asyncio
import websockets
import ssl
import pathlib

connections = {}


async def msg(websocket, path):
    async for received_message in websocket:
        receiver, sender, message = parse_message(received_message)

        if sender not in connections:
            connections[sender] = websocket
            continue

        await connections[sender].send(sender + ";" + message)
        if receiver in connections and receiver != sender:
            await connections[receiver].send(sender + ";" + message)


def parse_message(message):
    split_message = message.split(";", 2)
    return split_message[0], split_message[1], split_message[2]


if __name__ == "__main__":
    start_server = websockets.serve(msg, 'localhost', 8765)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
