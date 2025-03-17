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
                if msg == "@names":
                    names(client_socket)

                #split after commands that require no args, as msg[0] will be null otherwise
                msg = msg.split(" ")

                #group management
                if msg[0] == "@group":
                    group(client_socket, msg)

                #not done as spec requires @<username>
                if msg[0] == "@username":
                    username(client_socket, msg[1], msg[2])

            #conn.send("Msg received".encode(FORMAT))
            #broadcast(client_name + " msg: " + msg, client_socket)


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected")

        client_name = conn.recv(1024).decode()
        client = {'client_name': client_name, 'client_socket': conn}

        Clients.append(client)
        print(Clients)

        thread = threading.Thread(target=handle_client, args=(conn, addr, client))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


def broadcast(message, sender_conn=None,):
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
        message+= f"{client['client_name']}, "

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
    message = ""
    print(msg)
    group = msg[2]

    #checks if @group cmd only has 1 arg
    if len(msg) <= 1:
        invalidarg(client_socket,"group",1)
        return

    if msg[1] == "set":
        #TODO ensure user is in clients?
        if len(msg) <= 3:
            invalidarg(client_socket, "group set", 3)
            return

        if group not in Groups:
            Groups[group] = [] #create new dictionary key of group

        members = Groups.get(group)
        for i in range(3, len(msg)):
            if msg[i] not in members:
                members.append(msg[i])

        Groups[group] = members
        print(Groups)

    if msg[1] == "send":
        if len(msg) <= 3:
            invalidarg(client_socket, "group send", 3)
            return

        if group not in Groups:
            #TODO refactor invalidarg to account for other error messages
            message = "Group not found!"
            client_socket.send(message.encode(FORMAT))
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

#def checkusername(username):
def socketfromusername(username):
    for i in range(len(Clients)):
        if Clients[i]['client_name'] == username:
            return Clients[i]['client_socket']


#consolidated arg number error return function
def invalidarg(client_socket, cmdtype, count):
    message = f"erroneous command usage :{cmdtype}, requires more than {count} arguments"
    client_socket.send(message.encode(FORMAT))

print("[STARTING] server is starting...")
start()
