import socket
import os
import sys
import threading

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

SERVER = "127.0.1.1"
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(message)

def receive_message():
    while True:
        server_message = client.recv(HEADER).decode(FORMAT)
        if not server_message.strip():
            sys.exit()

        print(server_message)

def chat():
    while True:
        client_input = input("")
        client_message = name + ":" + client_input.strip("\n")
        send(client_message)

# First send is username
name = input("Enter your name: ")
send(name)  # Send the username in the same format as other messages

# Start a thread to receive messages
threading.Thread(target=receive_message).start()

# Start the chat loop
chat()