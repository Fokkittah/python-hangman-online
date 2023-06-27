import socket
import threading
import sys
import time

class Client:
    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Creates a new socket using IPv4 and TCP.
        self.client.connect((host, port)) #  Connects the client to the server at the specified host and port.
        # Flags used to manage the game state.
        self.game_over = False
        self.game_started = False
        self.my_turn = False

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('ascii') # Listens for a message from the server, decodes it from bytes to a string, and assigns it to message.
                if message == "Game is starting...":
                    self.game_started = True
                    print(message)
                elif message.startswith("Player") and "wins" in message:
                    self.game_over = True
                    print(message)
                    break
                elif message.startswith("It is your turn"): # This is the message sent to the player whose turn it is.
                    self.my_turn = True
                    print(message)
                elif message.startswith("Your turn"): # This is the message sent to the other player when it's their turn.
                    self.my_turn = True
                    print(message)
                else:
                    print(message)
            except:
                print("An error occurred!")
                self.client.close()
                break

    def write(self):
        while not self.game_started:
            time.sleep(1)  # Wait for the game to start

        while not self.game_over:
            if self.my_turn:
                message = input("Guess a letter: ")
                self.client.send(message.encode('ascii'))
                self.my_turn = False  # Reset after making a guess

    # Method creates and starts two separate threads: one for receiving messages and one for sending messages. 
    # This allows the client to listen for messages from the server and send messages to the server at the same time.
    def start(self):
        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

        write_thread = threading.Thread(target=self.write)
        write_thread.start()

if len(sys.argv) > 3:
    print("Usage: python client.py (optional: [ip] [port])")
    exit()

host = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
port = int(sys.argv[2]) if len(sys.argv) > 2 else 55555

client = Client(host, port)
client.start()
