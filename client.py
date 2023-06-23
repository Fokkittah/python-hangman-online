import socket
import threading
import sys
import time

class Client:
    def __init__(self, host, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        self.game_over = False
        self.game_started = False
        self.my_turn = False

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('ascii')
                if message == "Game is starting...":
                    self.game_started = True
                    print(message)
                elif message.startswith("Player") and "wins" in message:
                    self.game_over = True
                    print(message)
                    break
                elif message.startswith("It is your turn"):
                    self.my_turn = True
                    print(message)
                elif message.startswith("Your turn"): #"Your turn" in message:
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
            time.sleep(1)  # wait for the game to start

        while not self.game_over:
            if self.my_turn:
                message = input("Guess a letter: ")
                self.client.send(message.encode('ascii'))
                self.my_turn = False  # reset after making a guess


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
