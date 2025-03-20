import socket
import threading

#potential issue with small header
HEADER = 1024
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "@quit"

SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

Clients = []
Groups = {}
Users = []
HelpCommands = [
    "@quit:Disconnect from server",
    "@names:List all connected clients",
    "@username <message>: Sends a private msg",
    "@group set ggg xxx, yyy, zzz Creates a group ggg with specified members xxx, yyy, zzz",
    "@group send ggg <message> Sends a message to all members of group ggg",
    "@group leave ggg Removes the user from group ggg.",
    "@group delete ggg Deletes the group ggg."
]


def handle_client(conn, addr, client):
    client_name = client['client_name']
    client_socket = conn

    while True:
        msg = conn.recv(HEADER).decode(FORMAT)

        if not msg or msg == DISCONNECT_MESSAGE:
            #@quit is handled here
            broadcast(client_name + " disconnected")
            Clients.remove(client)
            client_socket.close()
            break
        else:
            print(f"[{client_name}] {msg}")
            #command format| @command_msg<space>msg
            #check if command
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
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected")

        #TODO refactor this to handle duplicate usernames
        while True:
            print("HERE")
            client_name = conn.recv(HEADER).decode(FORMAT)
            if client_name not in Users:
                break
            errormessage(conn, "", "", "Username in use!")

        Users.append(client_name)
        client = {'client_name': client_name, 'client_socket': conn}

        Clients.append(client)
        print(Clients)

        thread = threading.Thread(target=handle_client, args=(conn, addr, client))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


def broadcast(message, sender_conn=None, ):
    for client in Clients:
        client_socket = client['client_socket']
        if client_socket != sender_conn:  # Avoid sending the message back to the sender
            try:
                client_socket.send(message.encode(FORMAT))
            except Exception as e:
                print(f"[ERROR] Failed to send message to {client['client_name']}: {e}")


def broadcastall(message, sender_conn=None):
    for client in Clients:
        client_socket = client['client_socket']
        if client_socket != sender_conn:  # Avoid sending the message back to the sender
            try:
                client_socket.send(message.encode(FORMAT))
            except Exception as e:
                print(f"[ERROR] Failed to send message to {client['client_name']}: {e}")


def names(client_socket):
    message = "Connected: "
    for client in Clients:
        message += f"{client['client_name']}, "

    #remove last comma + space
    message = message[:-2]
    client_socket.send(message.encode(FORMAT))


def username(client_socket, recipient, msg):
    #if message is empty
    if not msg:
        message = "Empty message!"
        client_socket.send(message.encode(FORMAT))

    print(Clients)
    for client in Clients:
        if client['client_name'] == recipient:
            message = f"message from {client_socket}: {msg}"
            client_socket.send(message.encode(FORMAT))
            return

    #if client is not found
    message = "Recipient not found!"
    client_socket.send(message.encode(FORMAT))


def group(client_socket, msg):
    print(msg)
    #checks if @group cmd only has 2 arg
    if len(msg) <= 2:
        errormessage(client_socket, "group", 2, "")
        return

    message = ""
    group = msg[2]

    if msg[1] == "set":
        #TODO ensure user exists in current context?
        if len(msg) <= 3:
            errormessage(client_socket, "group set", 4, "")
            return

        #TODO Defined in spec that once group is created, adding new members is not possible?
        if group in Groups:
            message = "Group already exists!"
            errormessage(client_socket, "", "", message)
            return
        else:
            Groups[group] = []  #create new dictionary key of group

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
        #concantate remaining msg into one string
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
    if len(msg) <= 1:
        errormessage(client_socket, "private message", 2, "")
        return

    if msg[1] == "":
        errormessage(client_socket, "", "", "Empty message!")
        return

    name = msg[0][1:]
    message = msg[1]

    #TODO change socket to username
    for client in Clients:
        if name == client['client_name']:
            message = f"message from {client_socket}: {message}"
            c_socket = socketfromusername(name)
            c_socket.send(message.encode(FORMAT))
            return

    #if client is not found
    errormessage(client_socket, "", "", "Recipient not found!")
    return


def socketfromusername(username):
    for i in range(len(Clients)):
        if Clients[i]['client_name'] == username:
            return Clients[i]['client_socket']


def usernamefromsocket(socket):
    for i in range(len(Clients)):
        if Clients[i]['client_socket'] == socket:
            return Clients[i]['client_name']


#consolidated arg number error return function
def errormessage(client_socket, cmdtype, count, msg):
    if msg != "":
        #potentially unsafe
        client_socket.send(msg.encode(FORMAT))
    else:
        message = f"erroneous command usage : {cmdtype}, requires at least {count} arguments"
        client_socket.send(message.encode(FORMAT))


print("[STARTING] server is starting...")
start()
