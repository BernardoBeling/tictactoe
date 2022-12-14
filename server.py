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
    SHOW;SCOREBOARD
    DROP;
    SHUT;
'''

from socket import *
  
class player:
    def __init__(self, name,id, ip):
        self.name = name
        self.id = id 
        self.ip = ip
        self.moves = []

    def add_move(self,move):
        self.moves.append(move)

    def check_moves(self):
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
            if (set(move) & set(self.moves)) == set(move):        
                return True  
        return False

class server:
    def __init__(self,ip,port,log,max_players = 2):
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
        self.log = log
    
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
        scoreboard_str = '='*5 + ' Scoreboard ' + '='*5 +'\n'\
             + str(self.scoreboard).replace("'","").replace("{","").replace("}","") + '\n'\
                + '='*22
        print(scoreboard_str)
        return scoreboard_str
    
    def printl(self,string):
        print(string)
        log.write(string + '\n')

    def switch_turn(self):
        self.turn = 1 if self.turn == 0 else 0

    def parse(self,message,clientIP):
        message = message.decode().split(';')
        status = message[0]

        try:
            if status == 'JOIN' and self.players_count < self.max_players:
                name = message[1]
                self.players_count += 1
                self.players.append(player(name,self.players_count,clientIP)) #create player
                print(f'{name} joined server!')
                
                res = f'ACPT;{name};{self.players_count}'

                return res
            
            elif status == 'MOVE':
                move = message[1]
                self.players[self.turn].add_move(int(move))
                self.moves_count += 1 

                if self.moves_count >= 5:
                    if self.players[self.turn].check_moves():
                        winner = self.players[self.turn].name
                        self.update_scoreboard(winner)
                        self.state = 2
                self.switch_turn()
                return move
        except ValueError:
            print('Malformatted message!')
            return
    
    def start(self):
        s = socket(AF_INET,SOCK_DGRAM)
        try:
            s.bind((self.ip,self.port))
        except socket.error as err:
            print(f'Error binding server to IP:PORT\n Error: {err}')
            return False
            
        self.printl(f'Server online on {self.ip}:{self.port} with UDP connection!')

        while 1:
            if self.state == 0: #lobby
                s.settimeout(60)
                try:
                    if self.players_count == self.max_players:
                        self.state = 1
                        for i in range(2): #2 first players from queue
                            move_type = 'X' if i == 0 else 'O'
                            s.sendto(f'STRT;{move_type}'.encode(), self.players[i].ip)
                            self.set_scoreboard()
                    else:
                        msg, clientIP = s.recvfrom(1500)
                        res = self.parse(msg, clientIP)
                        s.sendto(res.encode(), clientIP)
                        

                    self.printl(f'Total players: {self.players_count}/{self.max_players}')

                except timeout as err:
                    self.printl(f'No connection attempts after 15s...\nError: {err}, exiting...')
                    s.close()
                    break

            elif self.state == 1: #game started
                
                cur_player_ip = self.players[self.turn].ip
                cur_player_id = self.players[self.turn].id

                s.settimeout(15) #move time
                try:
                    self.printl(f"{self.players[self.turn].name}'s turn...")

                    if self.moves_count == 0:
                        last_move = ''
                    
                    turn_msg = f'TURN;{cur_player_id};{last_move}'.encode()
                    s.sendto(turn_msg,cur_player_ip)
                    self.printl(f"Sended message: {turn_msg,cur_player_ip}")

                    move_msg, clientIP = s.recvfrom(1500)
                    self.printl(f'Recebido no server: {move_msg}')
                    
                    last_move = self.parse(move_msg,clientIP)
                                
                except timeout as err:
                    self.printl(f"{self.players[self.turn].name} didn't move in time, switching turn...")
                    self.switch_turn()

            elif self.state == 2: #game finished
                scoreboard_str = self.print_scoreboard()
                self.clear_moves()
                for p in self.players:
                    show_msg = f'SHOW;{scoreboard_str}'.encode()
                    s.sendto(show_msg,p.ip)
                    s.sendto('SHUT;'.encode(),(p.ip))
                break
        return

    def __del__(self):
        print('Server closed!')

ip = input('Server ip (default localhost): ') or 'localhost'
port = int(input('Server port (default 50000): ') or 50000)
log = open('server_log.txt', 'w')
server = server(ip,port,log)
server.start()
log.close()