import asyncio
import websockets
import ssl
import pathlib
from tkinter import *
from tkinter import scrolledtext
import threading
import time


username = ""
friends = ["a", "b", "c", "d"]
to_user = friends[0]
chats = {x: [] for x in friends}


# ------------------ GUI ------------------

class LoginWindow(Frame):

    def __init__(self, parent, wd, ht):
        Frame.__init__(self, parent, width=wd, height=ht)
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
        self.username_entry.bind("<Return>", lambda _: self.login())

        password_label = Label(login_container, text="Password", justify=LEFT)
        password_label.grid(column=0, row=2, sticky=EW)

        self.password_entry = Entry(login_container, width=30, highlightthickness=0, borderwidth=1, show="*")
        self.password_entry.grid(column=0, row=3, sticky=EW)
        self.password_entry.bind("<Return>", lambda _: self.login())

        self.login_button = Button(login_container, text="Login", command=self.login)
        self.login_button.grid(column=0, row=4, sticky=EW, pady=(20, 0))

        self.grid(row=0, column=0, sticky=NSEW)

    def login(self):
        global username
        username = self.username_entry.get()
        self.destroy()


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
        friends_frame = Frame(sidebar, height=200)
        friends_frame.grid(column=0, row=0, sticky=N+EW)
        friends_frame.columnconfigure(0, weight=1)
        friends_frame.rowconfigure(0, weight=0)
        friends_frame.grid_propagate(True)

        # Sidebar border
        sidebar_border = Frame(sidebar, width=1, height=ht)
        sidebar_border.grid(column=1, row=0)
        sidebar_border.config(bg="#bebac6")

        # Sidebar buttons
        self.friend_btns = []
        for friend in friends:
            b = Button(friends_frame, text=friend)
            b.config(command=lambda f=friend, b=b: self.change_chat_partner(f, b))
            self.friend_btns.append(b)
        for idx, btn in enumerate(self.friend_btns):
            btn.grid(column=0, row=idx, sticky=EW)
            if idx == 0:
                btn.config(state=DISABLED)

        self.grid(row=0, column=0, sticky=NSEW)

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
            await websocket.send(to_user + ";" + username + ";" + message)

    def change_chat_partner(self, friend, btn):
        global to_user
        to_user = friend
        self.update_chat()
        for b in self.friend_btns:
            b.config(state=NORMAL)
        btn.config(state=DISABLED)


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
            await websocket.send(";" + username + ";")
            while True:
                message = await websocket.recv()
                sender, parsed_message = message.split(";")
                global chats
                chats[to_user].append(sender + ": " + parsed_message)
                self.chat_window.update_chat()


class GUI:
    def __init__(self):
        width = 800
        height = 600
        global username

        app = Tk()
        app.title("Chat")
        app.geometry("%dx%d" % (width, height))

        login_window = LoginWindow(app, width, height)
        chat_window = ChatWindow(app, width, height)

        login_window.tkraise()

        ct = ConnectionThread(chat_window)
        ct.start()
        app.mainloop()


if __name__ == "__main__":
    GUI()
