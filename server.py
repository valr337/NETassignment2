import socket
import threading

# Constants for server configuration
HEADER = 1024  # Potential issue: Small header size
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "@quit"

# Server setup
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

# Global data structures
Clients = []  # List of connected clients
Groups = {}  # Dictionary to store groups
Users = []  # List of usernames
HelpCommands = [  # List of help commands
    "@quit:Disconnect from server",
    "@names:List all connected clients",
    "@username <message>: Sends a private msg",
    "@group set ggg xxx, yyy, zzz Creates a group ggg with specified members xxx, yyy, zzz",
    "@group send ggg <message> Sends a message to all members of group ggg",
    "@group leave ggg Removes the user from group ggg.",
    "@group delete ggg Deletes the group ggg."
]

def handle_client(conn, addr, client):
    """Handle communication with a connected client."""
    client_name = client['client_name']
    client_socket = conn

    while True:
        msg = conn.recv(HEADER).decode(FORMAT)

        if not msg or msg == DISCONNECT_MESSAGE:
            # Handle client disconnect
            broadcast(client_name + " disconnected")
            Clients.remove(client)
            client_socket.close()
            break
        else:
            print(f"[{client_name}] {msg}")
            # Check if the message is a command
            if msg[0] == "@":
                msg = msg.split(" ")
                if msg[0] == "@names":
                    names(client_socket)
                elif msg[0] == "@group":
                    group(client_socket, msg)
                elif msg[0] == "@help":
                    for cmd in HelpCommands:
                        client_socket.send(cmd.encode(FORMAT))
                else:
                    privatemessage(client_socket, msg)

def start():
    """Start the server and accept incoming connections."""
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected")

        while True:
            client_name = conn.recv(HEADER).decode(FORMAT)
            if client_name not in Users:
                break
            errormessage(conn, "", "", "Username in use! Renter username.")

        Users.append(client_name)
        client = {'client_name': client_name, 'client_socket': conn}
        Clients.append(client)
        print(Clients)

        thread = threading.Thread(target=handle_client, args=(conn, addr, client))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

def broadcast(message, sender_conn=None):
    """Broadcast a message to all connected clients except the sender."""
    for client in Clients:
        client_socket = client['client_socket']
        if client_socket != sender_conn:
            try:
                client_socket.send(message.encode(FORMAT))
            except Exception as e:
                print(f"[ERROR] Failed to send message to {client['client_name']}: {e}")

def broadcastall(message, sender_conn=None):
    """Broadcast a message to all connected clients including the sender."""
    for client in Clients:
        client_socket = client['client_socket']
        if client_socket != sender_conn:
            try:
                client_socket.send(message.encode(FORMAT))
            except Exception as e:
                print(f"[ERROR] Failed to send message to {client['client_name']}: {e}")

def names(client_socket):
    """Send a list of connected clients to the requesting client."""
    message = "Connected: "
    for client in Clients:
        message += f"{client['client_name']}, "
    message = message[:-2]  # Remove last comma + space
    client_socket.send(message.encode(FORMAT))

def username(client_socket, recipient, msg):
    """Send a private message to a specific client."""
    if not msg:
        message = "Empty message!"
        client_socket.send(message.encode(FORMAT))

    print(Clients)
    for client in Clients:
        if client['client_name'] == recipient:
            message = f"message from {client_socket}: {msg}"
            client_socket.send(message.encode(FORMAT))
            return

    message = "Recipient not found!"
    client_socket.send(message.encode(FORMAT))

def group(client_socket, msg):
    """Handle group-related commands."""
    print(msg)
    if len(msg) <= 2:
        errormessage(client_socket, "group", 2, "")
        return

    message = ""
    group = msg[2]

    if msg[1] == "set":
        if len(msg) <= 3:
            errormessage(client_socket, "group set", 4, "")
            return

        if group in Groups:
            message = "Group already exists!"
            errormessage(client_socket, "", "", message)
            return
        else:
            Groups[group] = []

        members = Groups.get(group)
        for i in range(3, len(msg)):
            if msg[i] not in members:
                members.append(msg[i])

        Groups[group] = members
        print(Groups)
        return

    if msg[1] == "send":
        if len(msg) <= 3:
            errormessage(client_socket, "group send", 4, "")
            return

        if group not in Groups:
            message = "Group not found!"
            errormessage(client_socket, "", "", message)
            return

        message = ""
        for i in range(3, len(msg)):
            message += msg[i] + " "
        message = message[:-1]

        members = Groups.get(group)
        for member in members:
            csocket = socketfromusername(member)
            csocket.send(message.encode(FORMAT))

        return

    if msg[1] == "leave":
        if len(msg) <= 2:
            errormessage(client_socket, "group leave", 3, "")
            return

        if group not in Groups:
            message = "Group not found!"
            errormessage(client_socket, "", "", message)
            return

        name = usernamefromsocket(client_socket)
        members = Groups.get(group)

        print(name)

        if name not in members:
            message = "You are not a member of this group!"
            errormessage(client_socket, "", "", message)
            return

        members.remove(name)
        print(members)
        return

    if msg[1] == "delete":
        if len(msg) <= 2:
            errormessage(client_socket, "group delete", 3, "")
            return

        if group not in Groups:
            message = "Group not found!"
            errormessage(client_socket, "", "", message)
            return

        Groups.pop(group)
        print(Groups)
        return

def privatemessage(client_socket, msg):
    """Send a private message to a specific client."""
    if len(msg) <= 1:
        errormessage(client_socket, "private message", 2, "")
        return

    if msg[1] == "":
        errormessage(client_socket, "", "", "Empty message!")
        return

    name = msg[0][1:]
    message = msg[1]

    for client in Clients:
        if name == client['client_name']:
            sender = usernamefromsocket(client_socket)
            message = f"message from {sender}: {message}"
            c_socket = socketfromusername(name)
            c_socket.send(message.encode(FORMAT))
            return

    errormessage(client_socket, "", "", "Recipient not found!")
    return

def socketfromusername(username):
    """Get the socket object for a given username."""
    for i in range(len(Clients)):
        if Clients[i]['client_name'] == username:
            return Clients[i]['client_socket']

def usernamefromsocket(socket):
    """Get the username for a given socket object."""
    for i in range(len(Clients)):
        if Clients[i]['client_socket'] == socket:
            return Clients[i]['client_name']

def errormessage(client_socket, cmdtype, count, msg):
    """Send an error message to the client."""
    if msg != "":
        client_socket.send(msg.encode(FORMAT))
    else:
        message = f"erroneous command usage : {cmdtype}, requires at least {count} arguments"
        client_socket.send(message.encode(FORMAT))

print("[STARTING] server is starting...")
start()