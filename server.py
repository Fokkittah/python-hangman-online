import socket
import threading
import random
import sys

def load_words(file_path):
    with open(file_path, 'r') as file:
        words = file.readlines()
    return [word.strip() for word in words]

class Server:
    def __init__(self, host, port, word_list_path):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.clients = []
        self.words = load_words(word_list_path)
        self.randomize = random.choice(self.words)
        self.current_words = [self.randomize, self.randomize]
        self.blanks = []
        self.guessed_letters = []
        self.errors = []
        self.turns = 0
        self.lock = threading.Lock()
        self.player_turn_msg_sent = [False, False]
        

    def broadcast(self, message):
        for client in self.clients:
            client.send(message)  # Remove .encode('ascii') from here

    def start_game(self):
        self.broadcast('Game is starting...'.encode('ascii'))
        self.blanks = ['_' * len(word) for word in self.current_words]
        self.guessed_letters = [[], []]
        self.errors = [0, 0]
        print(self.current_words)

        # Send the initial turn message to both players
        for i, client in enumerate(self.clients):
            if i == 0:
                client.send(f'It is your turn. The word is: {self.blanks[i]}'.encode('ascii'))
            else:
                client.send('Waiting for other player to guess...'.encode('ascii'))


    def handle(self, client, player):
        self.lock.acquire()
        self.clients.append(client)
        self.lock.release()

        while True:
            try:
                if self.turns % 2 == player:
                    guess = client.recv(1024).decode('ascii')
                    self.lock.acquire()
                    if guess in self.guessed_letters[player]:
                        client.send('This letter has already been guessed! Try again.'.encode('ascii'))
                    else:
                        self.guessed_letters[player].append(guess)
                        if guess in self.current_words[player]:
                            for i, letter in enumerate(self.current_words[player]):
                                if letter == guess:
                                    self.blanks[player] = self.blanks[player][:i] + letter + self.blanks[player][i+1:]
                            client.send(f'Correct guess! The word is: {self.blanks[player]}'.encode('ascii'))

                            if "_" not in self.blanks[player]:
                                self.broadcast(f'Player {player + 1} wins!'.encode('ascii'))
                                [c.close() for c in self.clients]
                                break
                        else:
                            self.errors[player] += 1
                            if self.errors[player] > 5:
                                self.broadcast(f'Player {2 - player} wins! Player {player + 1} made too many mistakes.'.encode('ascii'))
                                [c.close() for c in self.clients]
                                break
                            client.send(f'Wrong guess! You have made {self.errors[player]} mistakes.'.encode('ascii'))

                    # update turns
                    self.turns += 1
                    next_player = self.turns % 2
                    self.clients[next_player].send(f'Your turn: {self.blanks[next_player]}'.encode('ascii'))  # Signal for client to take their turn
                    self.clients[1 - next_player].send('Waiting for other player to guess...'.encode('ascii'))
            except:
                self.clients.remove(client)
                client.close()
                for remaining_client in self.clients:  # Send to remaining clients
                    remaining_client.send(f'Player {player + 1} has left the game'.encode('ascii'))
                break
            finally:
                if self.lock.locked():
                    self.lock.release()

    def start(self):
        print("Server Started")
        while True:
            client, address = self.server.accept()
            print(f"Connected with {address}")
            threading.Thread(target=self.handle, args=(client, len(self.clients))).start()  # Start threads before starting game
            
            if len(self.clients) == 1:
                client.send('Waiting for other player to connect...'.encode('ascii'))

            if len(self.clients) == 2:
                self.start_game()
                break

if len(sys.argv) < 2:
    print("Usage: python server.py [text_file_with_words] (optional: [ip] [port])")
    exit()

word_list_path = sys.argv[1]
host = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
port = int(sys.argv[3]) if len(sys.argv) > 3 else 55555

server = Server(host, port, word_list_path)
server.start()
