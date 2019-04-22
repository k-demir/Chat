"""
Contains elements for the graphical user interface.
"""

import websockets
import asyncio
from tkinter import *
from tkinter import scrolledtext

from tools import Encryption


class LoginWindow(Frame):
    """Creates and adds logic to the login frame."""

    def __init__(self, parent, wd, ht, controller):
        """Constructor

        Args:
            parent: The parent element.
            wd: The width of the frame.
            ht: The height of the frame.
            controller: An instance of the Controller class.
        """
        Frame.__init__(self, parent, width=wd, height=ht, bg=controller.color_1)
        self.controller = controller

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        # A container for the other elements
        login_container = Frame(self, width=wd/3, height=ht/2, bg=controller.color_1)
        login_container.grid(column=0, row=0)
        login_container.rowconfigure(0, weight=0)

        # An area for error messages
        self.error_frame = Frame(login_container, width=wd/3, height=ht/2, bg=controller.color_1)
        self.error_frame.grid(column=0, row=0, sticky=EW)
        self.error_frame.columnconfigure(0, weight=1)
        self.print_login_error("")

        # A text field for "Username"
        username_label = Label(login_container, text="Username", justify=LEFT, bg=controller.color_1)
        username_label.grid(column=0, row=1, sticky=EW)

        # Username entry field
        self.username_entry = Entry(login_container, width=30, highlightthickness=1, borderwidth=0,
                                    relief=SOLID, highlightbackground=controller.color_1,
                                    highlightcolor=controller.color_2)
        self.username_entry.grid(column=0, row=2, sticky=EW)
        self.username_entry.bind("<Return>", lambda _: self.try_login())

        # A text field for "Password"
        password_label = Label(login_container, text="Password", justify=LEFT, bg=controller.color_1)
        password_label.grid(column=0, row=3, sticky=EW)

        # Password entry field
        self.password_entry = Entry(login_container, width=30, highlightthickness=1, borderwidth=0, relief=SOLID,
                                    highlightbackground=controller.color_1, highlightcolor=controller.color_2, show="*")
        self.password_entry.grid(column=0, row=4, sticky=EW)
        self.password_entry.bind("<Return>", lambda _: self.try_login())

        # Login button
        login_btn_frame = Frame(login_container, bg=controller.color_2)
        login_btn_frame.grid(column=0, row=5, sticky=EW, pady=(20, 0))
        login_btn_frame.columnconfigure(0, weight=1)
        self.login_button = Label(login_btn_frame, text="Log in", bg="white")
        self.login_button.bind("<Button-1>", lambda _: self.try_login())
        self.login_button.grid(column=0, row=0, sticky=EW, padx=(1, 1), pady=(1, 1))

        # Registration button
        reg_btn_frame = Frame(login_container, bg=controller.color_2)
        reg_btn_frame.grid(column=0, row=6, sticky=EW, pady=(20, 0))
        reg_btn_frame.columnconfigure(0, weight=1)
        self.register_button = Label(reg_btn_frame, text="Register", bg="white")
        self.register_button.bind("<Button-1>", lambda _: self.controller.raise_register_window())
        self.register_button.grid(column=0, row=0, sticky=EW, padx=(1, 1), pady=(1, 1))

        self.grid(row=0, column=0)

    def try_login(self):
        """Initiates the login process."""
        asyncio.get_event_loop().run_until_complete(self.verify_login(self.username_entry.get(),
                                                                      self.password_entry.get()))

    async def verify_login(self, name, password):
        """Sends the username and password to the server and handles the response.

        Args:
            name: The username.
            password: The password.
        """
        async with websockets.connect(self.controller.ws_uri) as websocket:
            await websocket.send("l;;" + self.controller.connection_id + ";" + Encryption.encrypt(
                name + "@" + password, self.controller.connection_key))
            response = await websocket.recv()
            if response == "1":
                self.controller.username = name
                self.controller.raise_chat_window()
            else:
                self.print_login_error("Incorrect username or password")

    def print_login_error(self, message):
        """Prints the given message to the login error text area.

        Args:
            message: The error message that is printed.
        """
        label = Label(self.error_frame, text=message, fg="red", anchor=CENTER, justify=CENTER,
                      bg=self.controller.color_1)
        label.grid(column=0, row=0, sticky=EW)


class RegisterWindow(Frame):
    """Creates and adds logic to the registration frame."""

    def __init__(self, parent, wd, ht, controller):
        """Contructor.

        Args:
            parent: The parent element.
            wd: The width of the frame.
            ht: The height of the frame.
            controller: An instance of the Controller class.
        """
        Frame.__init__(self, parent, width=wd, height=ht, bg=controller.color_1)
        self.controller = controller

        # A container for the other elements
        register_container = Frame(self, width=wd/3, height=ht/2, bg=controller.color_1)
        register_container.grid(column=0, row=0)
        register_container.rowconfigure(0, weight=0)

        # A text area for error messages
        self.error_frame = Frame(register_container, width=wd/3, height=ht/2, bg=controller.color_1)
        self.error_frame.grid(column=0, row=0, sticky=EW)
        self.error_frame.columnconfigure(0, weight=1)
        self.print_registration_error("")

        # A text field for "Select username"
        username_label = Label(register_container, text="Select username", bg=controller.color_1)
        username_label.grid(column=0, row=1, sticky=EW)

        # Username entry field
        self.username_entry = Entry(register_container, width=30, highlightthickness=1, borderwidth=0, relief=SOLID,
                                    highlightbackground=controller.color_1, highlightcolor=controller.color_2)
        self.username_entry.grid(column=0, row=2, sticky=EW)
        self.username_entry.bind("<Return>", lambda _: self.try_registration())

        # A text field for "Select password"
        password_label_1 = Label(register_container, text="Select password", bg=controller.color_1)
        password_label_1.grid(column=0, row=3, sticky=EW)

        # Password entry field 1
        self.password_entry_1 = Entry(register_container, width=30, highlightthickness=1, borderwidth=0, relief=SOLID,
                                      highlightbackground=controller.color_1, highlightcolor=controller.color_2,
                                      show="*")
        self.password_entry_1.grid(column=0, row=4, sticky=EW)
        self.password_entry_1.bind("<Return>", lambda _: self.try_registration())

        # A text field for "Confirm password"
        password_label_2 = Label(register_container, text="Confirm password", bg=controller.color_1)
        password_label_2.grid(column=0, row=5, sticky=EW)

        # Password entry field 2
        self.password_entry_2 = Entry(register_container, width=30, highlightthickness=1, borderwidth=0,
                                      relief=SOLID, highlightbackground=controller.color_1,
                                      highlightcolor=controller.color_2, show="*")
        self.password_entry_2.grid(column=0, row=6, sticky=EW)
        self.password_entry_2.bind("<Return>", lambda _: self.try_registration())

        # Registration button
        reg_btn_frame = Frame(register_container, bg=controller.color_2)
        reg_btn_frame.grid(column=0, row=7, sticky=EW, pady=(20, 0))
        reg_btn_frame.columnconfigure(0, weight=1)
        self.register_button = Label(reg_btn_frame, text="Register", bg="white")
        self.register_button.bind("<Button-1>", lambda _: self.try_registration())
        self.register_button.grid(column=0, row=0, sticky=EW, padx=(1, 1), pady=(1, 1))

        # Return button
        ret_btn_frame = Frame(register_container, bg=controller.color_2)
        ret_btn_frame.grid(column=0, row=8, sticky=EW, pady=(20, 0))
        ret_btn_frame.columnconfigure(0, weight=1)
        self.return_button = Label(ret_btn_frame, text="Return", bg="white")
        self.return_button.bind("<Button-1>", lambda _: self.controller.login_window.tkraise())
        self.return_button.grid(column=0, row=0, sticky=EW, padx=(1, 1), pady=(1, 1))

        self.grid(row=0, column=0)

    def try_registration(self):
        """Initiates the registration process after checking that the username and passwords are valid."""

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

    async def send_registration(self, name, password):
        """Sends the registration request to the server.

        Args:
            name: The username.
            password: The password.
        """
        async with websockets.connect(self.controller.ws_uri) as websocket:
            await websocket.send("r;;" + self.controller.connection_id + ";" + Encryption.encrypt(
                name + "@" + password, self.controller.connection_key))
            response = await websocket.recv()
            if response == "1":
                self.controller.raise_login_window()
            elif response == "0":
                self.print_registration_error("Username taken")

    def print_registration_error(self, message):
        """Prints the given message to the error message area.

        Args:
            message: The message that is printed.
        """
        label = Label(self.error_frame, text=message, fg="red", anchor=CENTER, justify=CENTER,
                      bg=self.controller.color_1)
        label.grid(column=0, row=0, sticky=EW)


class ChatWindow(Frame):
    """Creates and adds logic to the chat frame."""

    def __init__(self, parent, wd, ht, controller):
        """Constructor.

        Args:
            parent: The parent element.
            wd: The width of the frame.
            ht: The height of the frame.
            controller: An instance of the Controller class.
        """
        Frame.__init__(self, parent, width=wd, height=ht, bg=controller.color_1)
        self.controller = controller

        # Chat frame
        chat_frame = Frame(self, width=4 * wd / 5, height=ht - 50, bg=controller.color_1)
        chat_frame.grid(column=1, row=0)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.grid_propagate(False)

        # Message frame
        message_frame = Frame(self, width=4 * wd / 5, height=50, bg=controller.color_1)
        message_frame.grid(column=1, row=1, sticky=NSEW)
        message_frame.columnconfigure(0, weight=1)
        message_frame.grid_propagate(False)

        # Received messages areas
        self.received_messages = scrolledtext.ScrolledText(chat_frame, bg=controller.color_1, highlightthickness=0)
        self.received_messages.grid(column=0, row=0, sticky=NSEW, padx=(10, 0), pady=(10, 10))
        self.received_messages.config(state=DISABLED)

        # Message entry
        self.message_entry = Entry(message_frame, highlightthickness=1, borderwidth=0,
                                   relief=SOLID, highlightbackground=controller.color_1,
                                   highlightcolor=controller.color_2)
        self.message_entry.grid(column=0, row=0, sticky=NSEW, padx=(20, 0))
        self.message_entry.bind("<Return>", lambda _: self.send_message())
        self.message_entry.config(state=DISABLED)

        # Send button
        send_button_frame = Frame(message_frame, bg=controller.color_2)
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
        sidebar_border.config(bg=controller.color_2)

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
                                       relief=SOLID, highlightbackground=controller.color_1,
                                       highlightcolor=controller.color_2)
        self.add_friends_entry.grid(column=0, row=1, sticky=EW, padx=(3, 3), pady=(0, 25))
        self.add_friends_entry.bind("<Return>", lambda _: self.try_add_friend())

        self.add_sidebar_buttons()

        self.grid(row=0, column=0, sticky=NSEW)

    def add_sidebar_buttons(self):
        """Adds new friend buttons to the sidebar."""

        friend_btns = []
        online_friends = []
        offline_friends = []
        for friend, online in self.controller.friends.items():
            if online:
                online_friends.append(friend)
            else:
                offline_friends.append(friend)

        for friend in sorted(online_friends):
            if friend.lower() == self.controller.to_user.lower():
                bg = self.controller.color_2
            else:
                bg = self.controller.color_3
            b = Label(self.friends_frame, text=friend, bg=bg)
            b.bind("<Button-1>", lambda _, f=friend: self.change_chat_partner(f))
            friend_btns.append(b)

        for friend in sorted(offline_friends):
            if friend.lower() == self.controller.to_user.lower():
                bg = self.controller.color_2
            else:
                bg = self.controller.color_1
            b = Label(self.friends_frame, text=friend, bg=bg)
            b.bind("<Button-1>", lambda _, f=friend: self.change_chat_partner(f))
            friend_btns.append(b)

        for idx, btn in enumerate(friend_btns):
            btn.grid(column=0, row=idx, sticky=EW, pady=(0, 1))

    def send_message(self):
        """Sends a message to the current chat partner and erases the message entry field."""

        message = self.message_entry.get()
        if not message:
            return
        self.message_entry.delete(0, "end")
        asyncio.get_event_loop().run_until_complete(self.msg(message))

    def update_chat(self):
        """Updates the received messages area."""

        self.received_messages.config(state=NORMAL)

        self.received_messages.delete(1.0, END)
        self.received_messages.insert(INSERT, "\n\n".join(
            self.controller.chats[self.controller.to_user]
            [max(0, len(self.controller.chats[self.controller.to_user]) - 500):]))
        self.received_messages.see(END)
        self.received_messages.config(state=DISABLED)

    async def msg(self, message):
        """Sends the given message to the current chat partner.

        Args:
            message: The message that is sent.
        """
        async with websockets.connect(self.controller.ws_uri) as websocket:
            await websocket.send("m;" + self.controller.to_user + ";" + self.controller.username + ";"
                                 + Encryption.encrypt(message, self.controller.keys[self.controller.to_user]))

    def change_chat_partner(self, friend):
        """Changes the current chat partner.

        Args:
            friend: The new chat partner.
        """
        self.controller.to_user = friend
        self.add_sidebar_buttons()
        self.message_entry.config(state=NORMAL)
        self.update_chat()

    def try_add_friend(self):
        """Initiates the process to add a new friend."""
        asyncio.get_event_loop().run_until_complete(self.add_friend(self.add_friends_entry.get()))

    async def add_friend(self, user):
        """Sends a request to the server to add a new friend and sends the Diffie-Hellman key if the request succeeds.

        Args:
            user: The added friend.
        """
        async with websockets.connect(self.controller.ws_uri) as websocket:
            if user == self.controller.username:
                return
            await websocket.send("a;" + user + ";" + self.controller.username + ";")
            response = await websocket.recv()
            if response == "1":
                await websocket.send(
                    "d;" + user + ";" + self.controller.username + ";" + Encryption.get_diffie_hellman(user))
            self.add_friends_entry.delete(0, END)
