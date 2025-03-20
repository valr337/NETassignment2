import socket
import os
import sys
import threading

# Constants for client configuration
HEADER = 1024  # Fixed header size for messages
PORT = 5050    # Port to connect to
FORMAT = 'utf-8'  # Encoding format
DISCONNECT_MESSAGE = "@quit"  # Command to disconnect

# Server address
SERVER = "127.0.1.1"  # Server IP address
ADDR = (SERVER, PORT)  # Tuple of server IP and port

# Create a socket object and connect to the server
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    """Send a message to the server."""
    message = msg.encode(FORMAT)  # Encode the message
    msg_length = len(message)  # Get the length of the message
    send_length = str(msg_length).encode(FORMAT)  # Encode the length
    send_length += b' ' * (HEADER - len(send_length))  # Pad the length to match HEADER size
    client.send(send_length)  # Send the length
    client.send(message)  # Send the actual message

def receive_message():
    """Receive messages from the server in a separate thread."""
    while True:
        server_message = client.recv(HEADER).decode(FORMAT)  # Receive and decode the message
        if not server_message.strip():  # If the message is empty, exit the client
            sys.exit()
        print(server_message)  # Print the received message

def chat():
    """Handle user input and send messages to the server."""
    while True:
        client_input = input("")  # Get user input
        client_message = client_input.strip("\n")  # Remove newline characters
        send(client_message)  # Send the message to the server

# Prompt the user for their name and send it to the server
name = input("Enter your name: ")
send(name)  # Send the username in the same format as other messages

# Start a thread to receive messages from the server
threading.Thread(target=receive_message).start()

# Start the chat loop to handle user input
chat()
