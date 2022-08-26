'''
    - input fields para capturar o nome dos jogadores
    - input fields para informar o endereço ip e porta
    - tipo de conexão (TCP/UDP)
    - botão de conectar

    BELO protocol:
    JOIN;PLAYER_NAME (client-side)
    ACPT;PLAYER_NAME;PLAYER_ID (server-side)
    REFS;ERR_MSG (server-side) servidor deve especificar o tipo de erro
    STRT;TYPE (server-side)
    TURN;PLAYER_ID;OTHER PLAYER MOVE (server-side)
    MOVE;COORD;PLAYER_ID (client-side)
    RFSH;COORD;PLAYER_ID (server-side)
    DROP;
    SHUT;
'''

from socket import *

def check_moves(player_moves):
    win_moves = [
        [1,2,3], #linha
        [4,5,6], #linha
        [7,8,9], #linha
        [1,4,7], #coluna
        [2,5,8], #coluna
        [3,6,9], #coluna
        [1,5,9], #diag
        [3,5,7] #diag
    ]

    for move in win_moves:
        # testar interseção (set)
        if (set(move) & set(player_moves)) == set(move):        
            return True  
    return False

def switch_turn(turn):
    return 1 if turn == 0 else 0

class player:
    def __init__(self, name,id, ip):
        self.name = name
        self.id = id 
        self.ip = ip
        self.moves = []

    def add_move(self,move):
        self.moves.append(move)

class server:
    def __init__(self,ip,port, max_players = 2):
        self.ip = ip
        self.port = port
        self.players_count = 0
        self.moves_count = 0
        self.max_players = max_players
        self.state = 0 #0: lobby, 1: Game started, 2:Game finished!
        self.players = [] #queue
        self.turn = 0 #0|1
        self.refresh = False
        self.scoreboard = {}
    
    def clear_moves(self):
        self.players[0].moves = []
        self.players[1].moves = []
    
    def set_scoreboard(self):
        p1_name = self.players[0].name
        p2_name = self.players[1].name

        self.scoreboard[p1_name] = 0
        self.scoreboard[p2_name] = 0
    
    def update_scoreboard(self, name):       
        self.scoreboard[name] += 1
    
    def print_scoreboard(self):
        print('Scoreboard:' + str(self.scoreboard).replace("'","").replace("{","").replace("}",""))
    
    def start(self):
        s = socket(AF_INET,SOCK_DGRAM)
        try:
            s.bind((self.ip,self.port))
        except socket.error as err:
            print(f'Error binding server to IP:PORT\n Error: {err}')
            return False
            
        print(f'Server online on {self.ip}:{self.port} with UDP connection!')

        winner = ''
        while 1:
            if self.state == 0: #lobby
                s.settimeout(15)
                try:
                    if self.players_count == self.max_players:
                        self.state = 1
                        for i in range(2): #2 first players from queue
                            type = 'X' if i == 0 else 'O'
                            s.sendto(f'STRT;{type}'.encode(), self.players[i].ip)
                            self.set_scoreboard()
                    else:
                        msg, clientIP = s.recvfrom(1500)
                        status, name = msg.decode().split(';')
                        if status == 'JOIN' and self.players_count < self.max_players:
                            self.players_count += 1
                            self.players.append(player(name,self.players_count,clientIP)) #create player
                            print(f'{name} joined server!')
                            
                            res = f'ACPT;{name};{self.players_count}'
                            s.sendto(res.encode(), clientIP)

                    print(f'Total players: {self.players_count}/{self.max_players}')

                except timeout as err:
                    print(f'No connection attempts after 15s...\nError: {err}, exiting...')
                    s.close()
                    break

            elif self.state == 1:
                
                p_ip = self.players[self.turn].ip
                p_id = self.players[self.turn].id

                idx = 0 if self.turn else 1 #get index of other player 
                last_move = self.players[idx].moves[-1] if len(self.players[idx].moves) != 0 else ''
                turn_msg = f'TURN;{p_id};{last_move}'.encode()

                s.settimeout(10) #move time

                try:
                    print(f"{self.players[self.turn].name}'s turn...")
                    s.sendto(turn_msg,p_ip)
                    print(f"Sended message: {turn_msg,p_ip}")
                    move_msg, clientIP = s.recvfrom(1500)
                    print(f'Move recebido no server: {move_msg}')
                    try:
                        status, move, move_id = move_msg.decode().split(';')
                    except ValueError:
                        print('Malformatted message!')

                    if status == 'MOVE':
                        self.players[self.turn].add_move(int(move))
                        self.moves_count += 1 

                        if self.moves_count >= 5:
                            if check_moves(self.players[self.turn].moves):
                                winner = self.players[self.turn].name
                                self.update_scoreboard(winner)
                                self.state = 2
                        self.turn = switch_turn(self.turn)

                except timeout as err:
                    print(f"{self.players[self.turn].name} didn't move in time, switching turn...")
                    self.turn = switch_turn(self.turn)

            elif self.state == 2:
                self.print_scoreboard()
                self.clear_moves()

                for p in self.players:
                    s.sendto('SHUT;'.encode(),(p.ip))
                break
  
        return


    def __del__(self):
        print('Server closed!')

ip = input('Server ip (default localhost): ') or 'localhost'
port = int(input('Server port (default 50000): ') or 50000)
server = server(ip,port)
server.start() #multiprocess?