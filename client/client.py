import asyncio
import websockets
from tkinter import *
from tkinter import scrolledtext
import threading
import time
import pickle
import random
from cryptography.fernet import Fernet
import base64
import atexit
from os import urandom
import sys

username = ""
friends = {}
to_user = ""
chats = {}
keys = {}

connection_id = base64.urlsafe_b64encode(urandom(30)).decode()
connection_secret_key = int.from_bytes(urandom(120), sys.byteorder)
connection_key = None

color_1 = "#F3F4EF"
color_2 = "#BDC696"
color_3 = "#D1D3C4"


# ------------------ Login Window ------------------


class LoginWindow(Frame):

    def __init__(self, parent, wd, ht, controller):
        Frame.__init__(self, parent, width=wd, height=ht, bg=color_1)
        self.controller = controller

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        login_container = Frame(self, width=wd / 3, height=ht / 2, bg=color_1)
        login_container.grid(column=0, row=0)
        login_container.rowconfigure(0, weight=0)

        self.error_frame = Frame(login_container, width=wd / 3, height=ht / 2, bg=color_1)
        self.error_frame.grid(column=0, row=0, sticky=EW)
        self.error_frame.columnconfigure(0, weight=1)
        self.print_login_error("")

        username_label = Label(login_container, text="Username", justify=LEFT, bg=color_1)
        username_label.grid(column=0, row=1, sticky=EW)

        self.username_entry = Entry(login_container, width=30, highlightthickness=1, borderwidth=0,
                                    relief=SOLID, highlightbackground=color_1, highlightcolor=color_2)
        self.username_entry.grid(column=0, row=2, sticky=EW)
        self.username_entry.bind("<Return>", lambda _: self.try_login())

        password_label = Label(login_container, text="Password", justify=LEFT, bg=color_1)
        password_label.grid(column=0, row=3, sticky=EW)

        self.password_entry = Entry(login_container, width=30, highlightthickness=1, borderwidth=0,
                                    relief=SOLID, highlightbackground=color_1, highlightcolor=color_2, show="*")
        self.password_entry.grid(column=0, row=4, sticky=EW)
        self.password_entry.bind("<Return>", lambda _: self.try_login())

        login_btn_frame = Frame(login_container, bg=color_2)
        login_btn_frame.grid(column=0, row=5, sticky=EW, pady=(20, 0))
        login_btn_frame.columnconfigure(0, weight=1)
        self.login_button = Label(login_btn_frame, text="Login", bg="white")
        self.login_button.bind("<Button-1>", lambda _: self.try_login())
        self.login_button.grid(column=0, row=0, sticky=EW, padx=(1, 1), pady=(1, 1))

        reg_btn_frame = Frame(login_container, bg=color_2)
        reg_btn_frame.grid(column=0, row=6, sticky=EW, pady=(20, 0))
        reg_btn_frame.columnconfigure(0, weight=1)
        self.register_button = Label(reg_btn_frame, text="Register", bg="white")
        self.register_button.bind("<Button-1>", lambda _: self.controller.raise_register_window())
        self.register_button.grid(column=0, row=0, sticky=EW, padx=(1, 1), pady=(1, 1))

        self.grid(row=0, column=0)

    def try_login(self):
        asyncio.get_event_loop().run_until_complete(self.verify_login(self.username_entry.get(),
                                                                      self.password_entry.get()))

    async def verify_login(self, username, password):
        async with websockets.connect("ws://localhost:8765") as websocket:
            await websocket.send("l;;" + connection_id + ";" + Encryption.encrypt_to_server(username + "@" + password))
            response = await websocket.recv()
            if response == "1":
                self.complete_login(username)
            else:
                self.print_login_error("Incorrect username or password")

    def complete_login(self, name):
        global username
        username = name
        self.controller.raise_chat_window()

    def print_login_error(self, message):
        label = Label(self.error_frame, text=message, fg="red", anchor=CENTER, justify=CENTER, bg=color_1)
        label.grid(column=0, row=0, sticky=EW)


# ------------------ Registration Window ------------------


class RegisterWindow(Frame):
    def __init__(self, parent, wd, ht, controller):
        Frame.__init__(self, parent, width=wd, height=ht, bg=color_1)
        self.controller = controller

        register_container = Frame(self, width=wd / 3, height=ht / 2, bg=color_1)
        register_container.grid(column=0, row=0)
        register_container.rowconfigure(0, weight=0)

        self.error_frame = Frame(register_container, width=wd / 3, height=ht / 2, bg=color_1)
        self.error_frame.grid(column=0, row=0, sticky=EW)
        self.error_frame.columnconfigure(0, weight=1)
        self.print_registration_error("")

        username_label = Label(register_container, text="Select username", bg=color_1)
        username_label.grid(column=0, row=1, sticky=EW)

        self.username_entry = Entry(register_container, width=30, highlightthickness=1, borderwidth=0,
                                    relief=SOLID, highlightbackground=color_1, highlightcolor=color_2)
        self.username_entry.grid(column=0, row=2, sticky=EW)
        self.username_entry.bind("<Return>", lambda _: self.try_registration())

        password_label_1 = Label(register_container, text="Select password", bg=color_1)
        password_label_1.grid(column=0, row=3, sticky=EW)

        self.password_entry_1 = Entry(register_container, width=30, highlightthickness=1, borderwidth=0,
                                      relief=SOLID, highlightbackground=color_1, highlightcolor=color_2, show="*")
        self.password_entry_1.grid(column=0, row=4, sticky=EW)
        self.password_entry_1.bind("<Return>", lambda _: self.try_registration())

        password_label_2 = Label(register_container, text="Confirm password", bg=color_1)
        password_label_2.grid(column=0, row=5, sticky=EW)

        self.password_entry_2 = Entry(register_container, width=30, highlightthickness=1, borderwidth=0,
                                      relief=SOLID, highlightbackground=color_1, highlightcolor=color_2, show="*")
        self.password_entry_2.grid(column=0, row=6, sticky=EW)
        self.password_entry_2.bind("<Return>", lambda _: self.try_registration())

        reg_btn_frame = Frame(register_container, bg=color_2)
        reg_btn_frame.grid(column=0, row=7, sticky=EW, pady=(20, 0))
        reg_btn_frame.columnconfigure(0, weight=1)
        self.register_button = Label(reg_btn_frame, text="Register", bg="white")
        self.register_button.bind("<Button-1>", lambda _: self.try_registration())
        self.register_button.grid(column=0, row=0, sticky=EW, padx=(1, 1), pady=(1, 1))

        ret_btn_frame = Frame(register_container, bg=color_2)
        ret_btn_frame.grid(column=0, row=8, sticky=EW, pady=(20, 0))
        ret_btn_frame.columnconfigure(0, weight=1)
        self.return_button = Label(ret_btn_frame, text="Return", bg="white")
        self.return_button.bind("<Button-1>", lambda _: self.controller.login_window.tkraise())
        self.return_button.grid(column=0, row=0, sticky=EW, padx=(1, 1), pady=(1, 1))

        self.grid(row=0, column=0)

    def try_registration(self):
        if len(self.username_entry.get()) < 4 or len(self.username_entry.get()) > 15:
            self.print_registration_error("Username must be between 4 and 15 characters")
            return
        elif not self.username_entry.get().isalnum():
            self.print_registration_error("Username can contain only alphanumeric characters")
            return
        elif self.password_entry_1.get() != self.password_entry_2.get():
            self.print_registration_error("Passwords must match")
            return
        elif len(self.password_entry_1.get()) < 5 or len(self.password_entry_1.get()) > 20:
            self.print_registration_error("Password must be between 5 and 20 characters")
            return
        asyncio.get_event_loop().run_until_complete(self.send_registration(self.username_entry.get(),
                                                                           self.password_entry_1.get()))

    async def send_registration(self, username, password):
        async with websockets.connect("ws://localhost:8765") as websocket:
            await websocket.send("r;;" + connection_id + ";" + Encryption.encrypt_to_server(username + "@" + password))
            response = await websocket.recv()
            if response == "1":
                self.controller.raise_login_window()
            elif response == "0":
                self.print_registration_error("Username taken")

    def print_registration_error(self, message):
        label = Label(self.error_frame, text=message, fg="red", anchor=CENTER, justify=CENTER, bg=color_1)
        label.grid(column=0, row=0, sticky=EW)


# ------------------ Chat Window ------------------


class ChatWindow(Frame):

    def __init__(self, parent, wd, ht):
        Frame.__init__(self, parent, width=wd, height=ht, bg=color_1)

        # Chat frame
        chat_frame = Frame(self, width=4 * wd / 5, height=ht - 50, bg=color_1)
        chat_frame.grid(column=1, row=0)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.grid_propagate(False)

        # Message frame
        message_frame = Frame(self, width=4 * wd / 5, height=50, bg=color_1)
        message_frame.grid(column=1, row=1, sticky=NSEW)
        message_frame.columnconfigure(0, weight=1)
        message_frame.grid_propagate(False)

        # Received messages areas
        self.received_messages = scrolledtext.ScrolledText(chat_frame, bg=color_1, highlightthickness=0)
        self.received_messages.grid(column=0, row=0, sticky=NSEW, padx=(10, 0), pady=(10, 10))
        self.received_messages.config(state=DISABLED)

        # Message entry
        self.message_entry = Entry(message_frame, highlightthickness=1, borderwidth=0,
                                   relief=SOLID, highlightbackground=color_1, highlightcolor=color_2)
        self.message_entry.grid(column=0, row=0, sticky=NSEW, padx=(20, 0))
        self.message_entry.bind("<Return>", lambda _: self.send_message())
        self.message_entry.config(state=DISABLED)

        # Send button
        send_button_frame = Frame(message_frame, bg=color_2)
        send_button_frame.grid(column=1, row=0, sticky=NSEW, padx=(5, 20))
        send_button = Label(send_button_frame, text="Send", bg="white")
        send_button.bind("<Button-1>", lambda _: self.send_message())
        send_button.grid(column=0, row=0, sticky=NSEW, padx=(1, 1), pady=(1, 1))

        # Sidebar frame
        sidebar = Frame(self, width=wd / 5, height=ht)
        sidebar.grid(column=0, row=0, rowspan=2)
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(0, weight=1)
        sidebar.grid_propagate(False)

        # Sidebar friends area
        self.friends_frame = Frame(sidebar, height=200)
        self.friends_frame.grid(column=0, row=0, sticky=N + EW)
        self.friends_frame.columnconfigure(0, weight=1)
        self.friends_frame.rowconfigure(0, weight=0)
        self.friends_frame.grid_propagate(True)

        # Sidebar border
        sidebar_border = Frame(sidebar, width=1, height=ht)
        sidebar_border.grid(column=1, row=0, rowspan=2)
        sidebar_border.config(bg=color_2)

        # Add friends area
        add_friends_frame = Frame(sidebar, height=100)
        add_friends_frame.grid(column=0, row=1, sticky=N + EW)
        add_friends_frame.columnconfigure(0, weight=1)
        add_friends_frame.rowconfigure(0, weight=0)
        add_friends_frame.grid_propagate(True)

        # Add friends label
        add_friends_label = Label(add_friends_frame, text="Add friends")
        add_friends_label.grid(column=0, row=0, sticky=EW)

        # Add friends entry
        self.add_friends_entry = Entry(add_friends_frame, highlightthickness=1, borderwidth=0,
                                       relief=SOLID, highlightbackground=color_1, highlightcolor=color_2)
        self.add_friends_entry.grid(column=0, row=1, sticky=EW, padx=(3, 3), pady=(0, 25))
        self.add_friends_entry.bind("<Return>", lambda _: self.try_add_friend())

        self.add_sidebar_buttons()

        self.grid(row=0, column=0, sticky=NSEW)

    def add_sidebar_buttons(self):
        friend_btns = []
        online_friends = []
        offline_friends = []
        for friend, online in friends.items():
            if online:
                online_friends.append(friend)
            else:
                offline_friends.append(friend)

        for friend in sorted(online_friends):
            if friend == to_user:
                bg = color_2
            else:
                bg = color_3
            b = Label(self.friends_frame, text=friend, bg=bg)
            b.bind("<Button-1>", lambda _, f=friend: self.change_chat_partner(f))
            friend_btns.append(b)

        for friend in sorted(offline_friends):
            if friend == to_user:
                bg = color_2
            else:
                bg = color_1
            b = Label(self.friends_frame, text=friend, bg=bg)
            b.bind("<Button-1>", lambda _, f=friend: self.change_chat_partner(f))
            friend_btns.append(b)

        for idx, btn in enumerate(friend_btns):
            btn.grid(column=0, row=idx, sticky=EW, pady=(0, 1))

    def send_message(self):
        message = self.message_entry.get()
        if not message:
            return

        self.message_entry.delete(0, "end")
        asyncio.get_event_loop().run_until_complete(self.msg(message))

    def update_chat(self):
        self.received_messages.config(state=NORMAL)

        self.received_messages.delete(1.0, END)
        self.received_messages.insert(INSERT, "\n\n".join(chats[to_user][max(0, len(chats[to_user]) - 500):]))
        self.received_messages.see(END)
        self.received_messages.config(state=DISABLED)

    @staticmethod
    async def msg(message):
        async with websockets.connect("ws://localhost:8765") as websocket:
            await websocket.send("m;" + to_user + ";" + username + ";" + Encryption.encrypt(message, to_user))

    def change_chat_partner(self, friend):
        global to_user
        to_user = friend
        self.add_sidebar_buttons()
        self.message_entry.config(state=NORMAL)
        self.update_chat()

    def try_add_friend(self):
        asyncio.get_event_loop().run_until_complete(self.add_friend(self.add_friends_entry.get()))

    async def add_friend(self, user):
        async with websockets.connect("ws://localhost:8765") as websocket:
            if user == username:
                return
            await websocket.send("a;" + user + ";" + username + ";")
            response = await websocket.recv()
            if response == "1":
                await Encryption.send_diffie_hellman(user)
            self.add_friends_entry.delete(0, END)


# ------------------ Connection Thread ------------------


class ConnectionThread(threading.Thread):
    def __init__(self, chat_window):
        threading.Thread.__init__(self)
        self.chat_window = chat_window

    def run(self):
        asyncio.new_event_loop().run_until_complete(Encryption.diffie_hellman_to_server())
        while not username:
            time.sleep(0.1)
        asyncio.new_event_loop().run_until_complete(self.connect())

    async def connect(self):
        async with websockets.connect("ws://localhost:8765") as websocket:
            await websocket.send("c;;" + username + ";")
            res = await websocket.recv()

            global friends
            global chats
            global to_user

            friends = pickle.loads(res)
            self.chat_window.add_sidebar_buttons()

            FileManager.load()
            a = AutoSaver()
            a.start()

            while True:
                message = await websocket.recv()
                sender, parsed_message = message.split(";", 1)

                if sender[:2] == "c+":
                    friends[sender[2:]] = int(parsed_message)
                    self.chat_window.add_sidebar_buttons()
                elif sender[:2] == "a+":
                    await Encryption.send_diffie_hellman(sender[2:])
                elif sender[:2] == "d+":
                    Encryption.receive_diffie_hellman(sender[2:], parsed_message)
                    friends[sender[2:]] = 1
                    chats[sender[2:]] = []
                    self.chat_window.add_sidebar_buttons()
                    to_user = sender[2:]
                else:
                    from_user, to_chat = sender.split(">", 1)
                    chats[to_chat].append(from_user + ": " + Encryption.decrypt(parsed_message, to_chat))
                    if to_user:
                        self.chat_window.update_chat()


# ------------------ File manager ------------------


class FileManager:

    @staticmethod
    def load():
        try:
            f = open(username + ".pickle", "rb")
            f.close()
        except IOError:
            f = open(username + ".pickle", "wb+")
            f.close()
        with open(username + ".pickle", "rb") as file:
            global keys
            global chats
            try:
                loaded_keys, loaded_chats = pickle.load(file)
                keys = loaded_keys
                chats = loaded_chats
            except EOFError:
                keys = {}
                chats = {}

    @staticmethod
    def save():
        if username:
            with open(username + ".pickle", "wb+") as file:
                pickle.dump((keys, chats), file)


# ------------------ Saver thread ------------------

class AutoSaver(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        time.sleep(1800)
        FileManager.save()


# ------------------ Clean up ------------------

class CleanUp:

    @classmethod
    def disconnect(cls):
        asyncio.get_event_loop().run_until_complete(cls.send_disconnect_request())

    @classmethod
    async def send_disconnect_request(cls):
        async with websockets.connect("ws://localhost:8765") as websocket:
            if username:
                await websocket.send("g;;" + username + ";")
            else:
                await websocket.send("g;;" + connection_id + ";")


# ------------------ Encryption ------------------


class Encryption:
    # 2048-bit prime for end-to-end encryption
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
    async def send_diffie_hellman(cls, friend):
        async with websockets.connect("ws://localhost:8765") as ws:
            if friend not in cls.private_keys:
                await cls.add_private_key(friend, 160)
            await ws.send("d;" + friend + ";" + username + ";" + str(pow(cls.g, cls.private_keys[friend], cls.p)))

    @classmethod
    def receive_diffie_hellman(cls, friend, received_key):
        if friend not in cls.private_keys:
            cls.add_private_key(friend, 160)
        keys[friend] = pow(int(received_key), cls.private_keys[friend], cls.p)

    @classmethod
    async def diffie_hellman_to_server(cls):
        async with websockets.connect("ws://localhost:8765") as ws:
            await ws.send("s;;" + connection_id + ";" + str(pow(cls.g, connection_secret_key, cls.p_s)))
            received_key = await ws.recv()
            global connection_key
            connection_key = pow(int(received_key), connection_secret_key, cls.p_s)

    @classmethod
    async def add_private_key(cls, friend, n_bits):
        cls.private_keys[friend] = int.from_bytes(urandom(n_bits), sys.byteorder)

    @staticmethod
    def encrypt(message, friend):
        random.seed(keys[friend])
        k = base64.urlsafe_b64encode(bytearray(random.getrandbits(8) for _ in range(32)))
        f = Fernet(k)
        return f.encrypt(bytes(message, encoding="UTF-8")).decode("UTF-8")

    @staticmethod
    def decrypt(message, friend):
        random.seed(keys[friend])
        k = base64.urlsafe_b64encode(bytearray(random.getrandbits(8) for _ in range(32)))
        f = Fernet(k)
        return f.decrypt(message.encode("UTF-8")).decode()

    @staticmethod
    def encrypt_to_server(message):
        random.seed(connection_key)
        k = base64.urlsafe_b64encode(bytearray(random.getrandbits(8) for _ in range(32)))
        f = Fernet(k)
        return f.encrypt(bytes(message, encoding="UTF-8")).decode("UTF-8")


# ------------------ Controller ------------------


class Controller:
    def __init__(self):
        width = 800
        height = 600
        global username

        app = Tk()
        app.title("Chat")
        app.geometry("%dx%d" % (width, height))
        app.resizable(False, False)

        self.chat_window = ChatWindow(app, width, height)
        self.register_window = RegisterWindow(app, width, height, self)
        self.login_window = LoginWindow(app, width, height, self)

        self.raise_login_window()

        ct = ConnectionThread(self.chat_window)
        ct.start()
        app.mainloop()

    def raise_register_window(self):
        self.register_window.tkraise()

    def raise_login_window(self):
        self.login_window.tkraise()

    def raise_chat_window(self):
        self.chat_window.tkraise()


if __name__ == "__main__":
    atexit.register(FileManager.save)
    atexit.register(CleanUp().disconnect)
    Controller()
