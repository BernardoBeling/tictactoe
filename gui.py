import tkinter as tk
import multiprocessing

def enable():
    for button in buttons:
        button['state'] = tk.NORMAL if button['text'] == ' ' else tk.DISABLED

def disable():
    for button in buttons:
        button['state'] = tk.DISABLED 

def set_click(move_type,button):
    if move_type == 'X':
        button['text'] = 'X'
    else:
        button['text'] = 'O'

def click(button,process_queue):

    if process_queue.empty():
        if gui_type == 'X':
            if button['text'] == ' ':
                button['text'] = 'X'
        else: 
             if button['text'] == ' ':
                button['text'] = 'O'

        disable()

        move = str(button)[-1]
        process_queue.put(move)

def run_gui(process_queue,type):  
    window = tk.Tk()
    global buttons, gui_type
    gui_type = type
    buttons = []

    for i in range(0,10):
        button = tk.Button(window, text=' ', font=('Helvetica', 20), height = 3, width = 6, bg = 'Grey')
        button.configure(command = lambda j=button: click(j,process_queue))
        button['state'] = tk.DISABLED
        buttons.append(button)

    b = 0
    for x in range(0,3):
        for y in range (0,3):
            buttons[b].grid(row = x, column = y)
            b += 1
    process_queue.put('Gui Started!!!')
    while True:
        window.update()
        if not process_queue.empty():
            move_type, move = process_queue.get().split(';')
            if move_type == type: #when is this gui's type, the move is from the other player
                other_type = 'X' if type == 'O' else 'O' #get other player type to refresh gui before move
                if move != '':
                    set_click(other_type,buttons[int(move)-1])
                enable()
            else:
                set_click(type,move)
###############################################################################

if __name__ == '__main__':
    run_gui(None)