import socket
import threading

#potential issue with small header
HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(ADDR)

Clients = []


def handle_client(conn, addr, client):
    client_name = client['client_name']
    client_socket = conn

    while True:
        msg = conn.recv(HEADER).decode(FORMAT)

        if not msg or msg == DISCONNECT_MESSAGE:
            broadcast(client_name + " disconnected")
            Clients.remove(client)
            client_socket.close()
            break
        else:
            print(f"[{addr}] {msg}")
            #conn.send("Msg received".encode(FORMAT))
            broadcast(client_name + " msg: " + msg, client_socket)


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected")

        client_name = conn.recv(1024).decode()
        client = {'client_name': client_name, 'client_socket': conn}

        Clients.append(client)
        thread = threading.Thread(target=handle_client, args=(conn, addr, client))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")


def broadcast(message, sender_conn=None):
    for client in Clients:
        client_name = client['client_name']
        client_socket = client['client_socket']
        if client_socket != sender_conn:  # Avoid sending the message back to the sender
            try:
                client_socket.send(message.encode(FORMAT))
            except Exception as e:
                print(f"[ERROR] Failed to send message to {client['client_name']}: {e}")


print("[STARTING] server is starting...")
start()
