import socket  # provides low-level network services.
import threading  # allows for multiple operations to run in separate threads.
import random  # allows you to perform random generations.
import sys  # provides functions for interacting with the interpreter.

def load_words(file_path):
    with open(file_path, 'r') as file:
        words = file.readlines()
    return [word.strip() for word in words]

class Server:
    def __init__(self, host, port, word_list_path):
        self.host = host  # The IP address of the host where the server is running.
        self.port = port  # The port on which the server is running.
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a new socket using IPv4 and TCP.
        self.server.bind((self.host, self.port)) # Bind the socket to address.
        self.server.listen() # Enable the server to accept connections.
        self.clients = [] # List to hold the clients connected to the server.
        self.words = load_words(word_list_path) # Load words from a file.
        self.randomize = random.choice(self.words) # Select a random word.
        self.current_words = [self.randomize, self.randomize] # Current words to guess for both players.
        self.blanks = [] # List to hold the blanks for the words (e.g., _ _ _ _ for a 4-letter word).
        self.guessed_letters = [] # List to hold the letters already guessed by the players.
        self.errors = [] # List to hold the number of errors made by the players.
        self.turns = 0 # Variable to track the number of turns taken.
        self.lock = threading.Lock() # Create a lock object to ensure thread-safety.
        self.player_turn_msg_sent = [False, False] # List to check whether the "player turn" message was sent to each player.
        
    def broadcast(self, message):
        for client in self.clients:
            client.send(message)   # Sends a message to each connected client.

    def start_game(self):
        self.broadcast('Game is starting...'.encode('ascii')) # Sends a "Game is starting..." message to all clients to make them know game started.
        self.blanks = ['_' * len(word) for word in self.current_words] # Sets up the blanks for each word.
        self.guessed_letters = [[], []] # Resets the guessed letters for each player.
        self.errors = [0, 0] # Resets the error count for each player.
        print(self.current_words) # Print the current words for debug purposes.

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
                    # Check if the letter has already been guessed
                    if guess in self.guessed_letters[player]:
                        client.send('This letter has already been guessed! Try again.'.encode('ascii'))
                    # If the letter hasn't been guessed yet, check if it's in the word
                    else:
                        self.guessed_letters[player].append(guess)
                        # If it is, reveal it in the blanks
                        if guess in self.current_words[player]:
                            for i, letter in enumerate(self.current_words[player]):
                                if letter == guess:
                                    self.blanks[player] = self.blanks[player][:i] + letter + self.blanks[player][i+1:]
                            client.send(f'Correct guess! The word is: {self.blanks[player]}'.encode('ascii'))
                            # If the word is complete, the player wins
                            if "_" not in self.blanks[player]:
                                self.broadcast(f'Player {player + 1} wins!'.encode('ascii'))
                                [c.close() for c in self.clients]
                                break
                        else:
                            # If the letter is not in the word, increment the error count
                            self.errors[player] += 1
                            # If there have been too many errors, the other player wins
                            if self.errors[player] > 5:
                                self.broadcast(f'Player {2 - player} wins! Player {player + 1} made too many mistakes.'.encode('ascii'))
                                [c.close() for c in self.clients]
                                break
                            client.send(f'Wrong guess! You have made {self.errors[player]} mistakes.'.encode('ascii'))

                    # Update turns
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
            client, address = self.server.accept()  # Wait for a client to connect.
            print(f"Connected with {address}")
            threading.Thread(target=self.handle, args=(client, len(self.clients))).start()  # Start threads before starting game
            
            # If there's only one client connected, send a message to wait for the other player.
            if len(self.clients) == 1:
                client.send('Waiting for other player to connect...'.encode('ascii'))

            # If two clients have connected, start the game.
            if len(self.clients) == 2:
                self.start_game()
                break

# If there are not enough command line arguments, print usage information and exit the script. The script needs at least the path to the word list file.
if len(sys.argv) < 2:
    print("Usage: python server.py [text_file_with_words] (optional: [ip] [port])")
    exit()

word_list_path = sys.argv[1] 
host = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
port = int(sys.argv[3]) if len(sys.argv) > 3 else 55555

server = Server(host, port, word_list_path)
server.start()
