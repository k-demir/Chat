"""
Contains client functionality.
"""

import atexit

from tools import *
from gui_elements import *


# ------------------ Connection Thread ------------------


class ConnectionThread(threading.Thread):
    """Handles the incoming messages."""

    def __init__(self, controller):
        """Constructor.

        Args:
            controller: An instance of the Controller class.
        """
        threading.Thread.__init__(self)
        self.controller = controller

    def run(self):
        """Exchanges the Diffie-Hellman key with the server and forms the connection after login."""
        self.controller.connection_key = asyncio.new_event_loop().run_until_complete(
            Encryption.diffie_hellman_to_server(
                self.controller.connection_id, self.controller.connection_secret_key, self.controller.ws_uri))
        while not self.controller.username:
            time.sleep(0.1)
        asyncio.new_event_loop().run_until_complete(self.connect())

    async def connect(self):
        """Forms the connection to the server after login and handles incoming messages."""
        async with websockets.connect(self.controller.ws_uri) as websocket:
            await websocket.send("c;;" + self.controller.username + ";")
            res = await websocket.recv()

            self.controller.friends = pickle.loads(res)
            self.controller.chat_window.add_sidebar_buttons()

            self.controller.file_manager.load()
            a = AutoSaver(1800, self.controller.file_manager)
            a.daemon = True
            a.start()

            while True:
                message = await websocket.recv()
                sender, parsed_message = message.split(";", 1)

                if sender[:2] == "c+":
                    self.controller.friends[sender[2:]] = int(parsed_message)
                    self.controller.chat_window.add_sidebar_buttons()
                elif sender[:2] == "a+":
                    await websocket.send("d;" + sender[2:] + ";" + self.controller.username + ";"
                                         + Encryption.get_diffie_hellman(sender[2:]))
                elif sender[:2] == "d+":
                    self.controller.keys[sender[2:]] = Encryption.receive_diffie_hellman(sender[2:], parsed_message)
                    self.controller.friends[sender[2:]] = 1
                    self.controller.chats[sender[2:]] = []
                    self.controller.chat_window.add_sidebar_buttons()
                    self.controller.to_user = sender[2:]
                else:
                    from_user, to_cht = sender.split(">", 1)
                    self.controller.chats[to_cht].append(
                        from_user + ": " + Encryption.decrypt(parsed_message, self.controller.keys[to_cht]))
                    if self.controller.to_user:
                        self.controller.chat_window.update_chat()


# ------------------ Controller ------------------


class Controller:
    """Creates the UI and starts the application."""

    def __init__(self, ws_uri="ws://localhost:8765"):
        """Constructor.

        Args:
            ws_uri: The location of the server.
        """
        self.ws_uri = ws_uri

        width = 800
        height = 600

        self.username = ""
        self.friends = {}
        self.to_user = ""
        self.chats = {}
        self.keys = {}

        self.connection_id = base64.urlsafe_b64encode(urandom(30)).decode()
        self.connection_secret_key = int.from_bytes(urandom(120), sys.byteorder)
        self.connection_key = None

        self.color_1 = "#F3F4EF"
        self.color_2 = "#BDC696"
        self.color_3 = "#D1D3C4"

        app = Tk()
        app.title("Chat")
        app.geometry("%dx%d" % (width, height))
        app.resizable(False, False)

        self.chat_window = ChatWindow(app, width, height, self)
        self.register_window = RegisterWindow(app, width, height, self)
        self.login_window = LoginWindow(app, width, height, self)

        self.raise_login_window()

        self.file_manager = FileManager(self)

        atexit.register(self.file_manager.save)
        atexit.register(CleanUp(self).disconnect)

        ct = ConnectionThread(self)
        ct.daemon = True
        ct.start()
        app.mainloop()

    def raise_register_window(self):
        self.register_window.tkraise()

    def raise_login_window(self):
        self.login_window.tkraise()

    def raise_chat_window(self):
        self.chat_window.tkraise()


if __name__ == "__main__":
    Controller()
