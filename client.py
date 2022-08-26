from socket import *
import tkinter as tk
import multiprocessing
import gui
import time

if __name__ == '__main__':
    name = input('Player name: ')
    ip = input('Server ip (default localhost): ') or 'localhost'
    port = int(input('Server port (default 50000): ') or 50000)
    attempts = 0
    client_id = 0

    client = socket(AF_INET,SOCK_DGRAM)
    client.settimeout(5)

    while attempts <= 3:
        try:
            print('Attempting to connect...')
            client.sendto(f'JOIN;{name}'.encode(), (ip,port))
            msg = client.recv(1500) #ACPT;NAME;ID

            status, svname, client_id = msg.decode().split(';')
            if status == 'ACPT' and svname == name:
                print(f'Sucessfully joined server! Player id: {client_id}')
                break

        except timeout as err:
            attempts += 1
    else:
        print('No response from the server after 15s (3 attempts)...')

    client.settimeout(60)

    status = ''
    type = ''
    #p_queue = None
    #gui_process = None

    try:
        while status != 'SHUT':
            msg = client.recv(1500)
            res = msg.decode().split(';')
            print(f'Recebido no client: {res}')
            status = res[0]

            if status == 'STRT':
                type = res[1]
                p_queue = multiprocessing.Queue()
                gui_process = multiprocessing.Process(target=gui.run_gui, args=(p_queue,type))
                gui_process.start()
                while p_queue.empty():
                    continue
                print(p_queue.get())

            if status == 'TURN' and res[1] == client_id:
                print('Your turn...')
                #logica comunicacao gui x client
                p_queue.put(f'{type};{res[2]}')
                time.sleep(0.2)
                move = ''
                while move == '':
                    if not p_queue.empty():
                        move = p_queue.get()

                if move == 'n':
                    print(move)
                    client.sendto(f'MOVE;1;{client_id}'.encode(), (ip,port))
                elif move != '':
                    print(move)
                    client.sendto(f'MOVE;{move};{client_id}'.encode(), (ip,port))

            if status == 'SHOW':
                print(res[1])
            
        print('Kill process!')
        gui_process.kill()

    except timeout as err:
        print('Exiting...')
    finally:
        print('Exiting...')
        quit()