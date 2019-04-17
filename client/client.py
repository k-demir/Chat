import asyncio
import websockets
import ssl
import pathlib
from tkinter import *
from tkinter import scrolledtext
import threading
import time
import pickle


username = ""
friends = []
to_user = ""
chats = {}


# ------------------ Login Window ------------------

class LoginWindow(Frame):

    def __init__(self, parent, wd, ht, controller):
        Frame.__init__(self, parent, width=wd, height=ht)
        self.controller = controller

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        login_container = Frame(self, width=wd/3, height=ht/2)
        login_container.grid(column=0, row=0)
        login_container.rowconfigure(0, weight=0)

        username_label = Label(login_container, text="Username", justify=LEFT)
        username_label.grid(column=0, row=0, sticky=EW)

        self.username_entry = Entry(login_container, width=30, highlightthickness=0, borderwidth=1)
        self.username_entry.grid(column=0, row=1, sticky=EW)
        self.username_entry.bind("<Return>", lambda _: self.try_login())

        password_label = Label(login_container, text="Password", justify=LEFT)
        password_label.grid(column=0, row=2, sticky=EW)

        self.password_entry = Entry(login_container, width=30, highlightthickness=0, borderwidth=1, show="*")
        self.password_entry.grid(column=0, row=3, sticky=EW)
        self.password_entry.bind("<Return>", lambda _: self.try_login())

        self.login_button = Button(login_container, text="Login", command=self.try_login)
        self.login_button.grid(column=0, row=4, sticky=EW, pady=(20, 0))

        self.login_button = Button(login_container, text="Register",
                                   command=lambda: self.controller.raise_register_window())
        self.login_button.grid(column=0, row=5, sticky=EW, pady=(20, 0))

        self.grid(row=0, column=0)

    def try_login(self):
        asyncio.get_event_loop().run_until_complete(self.verify_login(self.username_entry.get(),
                                                                      self.password_entry.get()))

    async def verify_login(self, username, password):
        async with websockets.connect("ws://localhost:8765") as websocket:
            await websocket.send("l;;" + username + ";" + password)
            response = await websocket.recv()
            if response == "1":
                self.complete_login(username)

    def complete_login(self, name):
        global username
        username = name
        self.controller.raise_chat_window()


# ------------------ Registration Window ------------------


class RegisterWindow(Frame):
    def __init__(self, parent, wd, ht, controller):
        Frame.__init__(self, parent, width=wd, height=ht)
        self.controller = controller

        register_container = Frame(self, width=wd / 3, height=ht / 2)
        register_container.grid(column=0, row=0)
        register_container.rowconfigure(0, weight=0)

        username_label = Label(register_container, text="Select username", justify=LEFT)
        username_label.grid(column=0, row=0, sticky=EW)

        self.username_entry = Entry(register_container, width=30, highlightthickness=0, borderwidth=1)
        self.username_entry.grid(column=0, row=1, sticky=EW)
        self.username_entry.bind("<Return>", lambda _: self.try_registration())

        password_label_1 = Label(register_container, text="Password", justify=LEFT)
        password_label_1.grid(column=0, row=2, sticky=EW)

        self.password_entry_1 = Entry(register_container, width=30, highlightthickness=0, borderwidth=1, show="*")
        self.password_entry_1.grid(column=0, row=3, sticky=EW)
        self.password_entry_1.bind("<Return>", lambda _: self.try_registration())

        password_label_2 = Label(register_container, text="Confirm password", justify=LEFT)
        password_label_2.grid(column=0, row=4, sticky=EW)

        self.password_entry_2 = Entry(register_container, width=30, highlightthickness=0, borderwidth=1, show="*")
        self.password_entry_2.grid(column=0, row=5, sticky=EW)
        self.password_entry_2.bind("<Return>", lambda _: self.try_registration())

        self.register_button = Button(register_container, text="Register", command=self.try_registration)
        self.register_button.grid(column=0, row=6, sticky=EW, pady=(20, 0))

        self.grid(row=0, column=0)

    def try_registration(self):
        if self.password_entry_1.get() != self.password_entry_2.get():
            return
        asyncio.get_event_loop().run_until_complete(self.send_registration(self.username_entry.get(),
                                                                           self.password_entry_1.get()))

    async def send_registration(self, username, password):
        async with websockets.connect("ws://localhost:8765") as websocket:
            await websocket.send("r;;" + username + ";" + password)
            response = await websocket.recv()
            if response == "1":
                self.controller.raise_login_window()


# ------------------ Chat Window ------------------


class ChatWindow(Frame):

    def __init__(self, parent, wd, ht):
        Frame.__init__(self, parent, width=wd, height=ht)

        # Chat frame
        chat_frame = Frame(self, width=4*wd/5, height=ht-50)
        chat_frame.grid(column=1, row=0)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.grid_propagate(False)

        # Message frame
        message_frame = Frame(self, width=4*wd/5, height=50)
        message_frame.grid(column=1, row=1, padx=(15, 25))
        message_frame.columnconfigure(0, weight=1)
        message_frame.grid_propagate(False)

        # Received messages areas
        self.received_messages = scrolledtext.ScrolledText(chat_frame)
        self.received_messages.grid(column=0, row=0, sticky=NSEW)
        self.received_messages.config(state=DISABLED)

        # Message entry
        self.message_entry = Entry(message_frame, highlightthickness=0, borderwidth=1)
        self.message_entry.grid(column=0, row=0, sticky=NSEW)
        self.message_entry.bind("<Return>", lambda _: self.send_message())

        # Send button
        send_button = Button(message_frame, text="Send",
                             command=lambda: self.send_message(),
                             width=10)
        send_button.grid(column=1, row=0, sticky=NSEW, padx=(0, 20))

        # Sidebar frame
        sidebar = Frame(self, width=wd/5, height=ht)
        sidebar.grid(column=0, row=0, rowspan=2)
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(0, weight=1)
        sidebar.grid_propagate(False)

        # Sidebar friends area
        self.friends_frame = Frame(sidebar, height=200)
        self.friends_frame.grid(column=0, row=0, sticky=N+EW)
        self.friends_frame.columnconfigure(0, weight=1)
        self.friends_frame.rowconfigure(0, weight=0)
        self.friends_frame.grid_propagate(True)

        # Sidebar border
        sidebar_border = Frame(sidebar, width=1, height=ht)
        sidebar_border.grid(column=1, row=0, rowspan=2)
        sidebar_border.config(bg="#bebac6")

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
        self.add_friends_entry = Entry(add_friends_frame, highlightthickness=0, borderwidth=1)
        self.add_friends_entry.grid(column=0, row=1, sticky=EW)
        self.add_friends_entry.bind("<Return>", lambda _: self.try_add_friend())

        self.add_sidebar_buttons()

        self.grid(row=0, column=0, sticky=NSEW)

    def add_sidebar_buttons(self):
        friend_btns = []
        for friend in friends:
            b = Button(self.friends_frame, text=friend)
            b.config(command=lambda f=friend: self.change_chat_partner(f))
            friend_btns.append(b)
        for idx, btn in enumerate(friend_btns):
            btn.grid(column=0, row=idx, sticky=EW)

    def send_message(self):
        message = self.message_entry.get()
        if not message:
            return

        self.message_entry.delete(0, "end")
        asyncio.get_event_loop().run_until_complete(self.msg(message))

    def update_chat(self):
        self.received_messages.config(state=NORMAL)

        self.received_messages.delete(1.0, END)
        self.received_messages.insert(INSERT, "\n".join(chats[to_user][max(0, len(chats[to_user])-100):]))
        self.received_messages.see(END)
        self.received_messages.config(state=DISABLED)

    @staticmethod
    async def msg(message):
        async with websockets.connect("ws://localhost:8765") as websocket:
            await websocket.send("m;" + to_user + ";" + username + ";" + message)

    def change_chat_partner(self, friend):
        global to_user
        to_user = friend
        self.update_chat()

    def try_add_friend(self):
        asyncio.get_event_loop().run_until_complete(self.add_friend(self.add_friends_entry.get()))

    async def add_friend(self, user):
        async with websockets.connect("ws://localhost:8765") as websocket:
            await websocket.send("a;;" + username + ";" + user)
            response = await websocket.recv()
            if response == "1":
                global friends
                global chats
                friends.append(user)
                chats[user] = []
                self.add_sidebar_buttons()
            self.add_friends_entry.delete(0, END)

# ------------------ Connection Thread ------------------


class ConnectionThread(threading.Thread):
    def __init__(self, chat_window):
        threading.Thread.__init__(self)
        self.chat_window = chat_window

    def run(self):
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
            to_user = friends[0]
            for friend in friends:
                chats[friend] = []

            while True:
                message = await websocket.recv()
                sender, parsed_message = message.split(";")
                chats[to_user].append(sender + ": " + parsed_message)
                self.chat_window.update_chat()


# ------------------ Controller ------------------


class Controller:
    def __init__(self):
        width = 800
        height = 600
        global username

        app = Tk()
        app.title("Chat")
        app.geometry("%dx%d" % (width, height))

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
    Controller()
