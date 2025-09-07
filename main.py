import pygame
import random
import copy
import time
import numpy
import socket
import threading
import os
DEBUG = False
os.environ['SDL_VIDEO_WINDOW_POS'] = "250,25"

Players = int(input("플레이어 수는?\n: "))
my_Turn = 1
player_ports = []
player_ips = []
my_port = 0
if Players > 1:
    my_Turn = int(input("몇 번째 플레이어 입니까? 1 or 2 or 3\n: "))
    my_port = int(input("자신의 포트입력: "))
if not DEBUG:
    for i in range(Players-1):
        player_ports.append(int(input(f"다른 플레이어의 포트 입력: ")))
        player_ips.append(input(f"다른 플레이어의 IP입력"))

if Players > 1 and not DEBUG:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', my_port))
save_file_path = input("불러올 맵 이름을 입력하세요. 없으면 빈 상태로 시작합니다.\n: ")+".txt"
def LoadSavedBoard():
    try:
        with open(save_file_path, "r", encoding="utf-8") as file:
            Loaded_Board = file.read().split(" ")
            Processed_Board = []
            tmp = []
            for i,q in enumerate(Loaded_Board):
                if q=="\n":
                    continue
                if q=="0":
                    tmp.append(0)
                else:
                    t=q.split("$")
                    if t==['']:
                        continue
                    t[0]=int(t[0])
                    if t[1]=="True":
                        t[1] = True
                    else:
                        t[1] = False
                    if t[2]=="None":
                        t[2] = None
                    tmp.append(t)
                if len(tmp) == BOARD_WIDTH:
                    Processed_Board.append(tmp)
                    tmp = []
            print(f"{save_file_path}에서 보드를 불러왔습니다.")
            return copy.deepcopy(Processed_Board)
    except Exception as e:
        if save_file_path == ".txt":
            print("빈 보드로 시작합니다")
            return [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]
        print(f"파일을 불러오는 중 오류가 발생하였습니다: {e}")
        return [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]

SCREEN_X,SCREEN_Y = 800,800
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
BOARD_SIZE = 30 - Players*5
FPS = 60
CLOCK = pygame.time.Clock()
pygame.init()
pygame.font.init()
TextFont = pygame.font.SysFont("Segoe UI Symbol", 24)
EmojiFont = pygame.font.SysFont("Segoe UI Emoji", 24)
screen = pygame.display.set_mode([SCREEN_X, SCREEN_Y])
Gameover = False

CurrentBoard = LoadSavedBoard() if not DEBUG else [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]
CurrentBoard2 = [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]
CurrentBoard3 = [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]
Run = True
Block_Spawn_Ready = True
Score = 0
tick = 0
fall_tick = 0
stop_tick = 0

BLOCKS = [
    [[1,1,1,1],[0,0,0,0],[0,0,0,0],[0,0,0,0]],
    [[1,0,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    [[0,0,1,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    [[1,1,0,0],[1,1,0,0],[0,0,0,0],[0,0,0,0]],
    [[0,1,1,0],[1,1,0,0],[0,0,0,0],[0,0,0,0]],
    [[0,1,0,0],[1,1,1,0],[0,0,0,0],[0,0,0,0]],
    [[1,1,0,0],[0,1,1,0],[0,0,0,0],[0,0,0,0]],
]
BLOCKS_COLOR = [
    [0,240,240],
    [0,0,240],
    [240,160,0],
    [240,240,0],
    [0,240,0],
    [160,0,240],
    [240,0,0],
    [255,255,255]
]
BLOCKS_OFFSET = [
    [0,3],
    [0,3],
    [0,3],
    [0,4],
    [0,3],
    [0,3],
    [0,3],
]
SPECIAL = [None,"Bomb","Add_1","Goal"]
SPECIAL_EMOJI = {None : "",
                 "Bomb" : "💥",
                 "Add_1" : "+1",
                 "Goal": "G"}
NextBlockBoard = [[0]*4]*4
NextBlock = random.randint(0,len(BLOCKS)-1)

class PlayerBoard:
    def __init__(self, board_id, x_offset, y_offset, cell_size, board_ref):
        self.board_id = board_id
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.cell_size = cell_size
        self.board_ref = board_ref
    
    def update_board_ref(self, processed_data):
        self.board_ref = processed_data
    def draw(self):
        for i in range(BOARD_HEIGHT):
            for j in range(BOARD_WIDTH):
                cell = self.board_ref[i][j]
                if cell == 0:
                    color = [50, 50, 50]
                else:
                    if isinstance(cell, list):
                        color = BLOCKS_COLOR[cell[0]]
                    else:
                        color = [50, 50, 50]

                x = self.x_offset + j * self.cell_size
                y = self.y_offset + i * self.cell_size
                pygame.draw.rect(screen, color, [x, y, self.cell_size, self.cell_size])

                if isinstance(cell, list) and len(cell) > 2 and cell[2] is not None:
                    text = EmojiFont.render(SPECIAL_EMOJI[cell[2]], True, [0, 0, 0])
                    screen.blit(text, (x+2, y+2))
        for i in range(BOARD_WIDTH+1):
            x = self.x_offset + i * self.cell_size
            y1 = self.y_offset
            y2 = y1 + self.cell_size * BOARD_HEIGHT
            pygame.draw.line(screen, [185,185,185], [x, y1], [x, y2], 2)
        for i in range(BOARD_HEIGHT+1):
            y = self.y_offset + i * self.cell_size
            x1 = self.x_offset
            x2 = x1 + self.cell_size * BOARD_WIDTH
            pygame.draw.line(screen, [185,185,185], [x1, y], [x2, y], 2)

board_pixel_width = BOARD_WIDTH * BOARD_SIZE
board_pixel_height = BOARD_HEIGHT * BOARD_SIZE

def get_board_positions(players):
    positions = []
    spacing_x = SCREEN_X / (players + 1)
    y = (SCREEN_Y - board_pixel_height) / 2
    for i in range(players):
        x = spacing_x * (i + 1) - board_pixel_width / 2
        positions.append((x, y))
    return positions

positions = get_board_positions(Players)

p1_x, p1_y = positions[0]
if Players >= 2:
    p2_x, p2_y = positions[1]
if Players >= 3:
    p3_x, p3_y = positions[2]

PlayerB1 = PlayerBoard(1, p1_x, p1_y, BOARD_SIZE, CurrentBoard)
if Players >= 2:
    PlayerB2 = PlayerBoard(2, p2_x, p2_y, BOARD_SIZE, CurrentBoard2)
if Players >= 3:
    PlayerB3 = PlayerBoard(3, p3_x, p3_y, BOARD_SIZE, CurrentBoard3)

def Func_Update_Visual():
    global NextBlockBoard
    pygame.display.set_caption(f"테트리스 [점수 : {Score}]")
    PlayerB1.draw()
    if Players >= 2:
        PlayerB2.draw()
    if Players >= 3:
        PlayerB3.draw()
    NextBlockBoard = copy.deepcopy(BLOCKS[NextBlock])
    for i in range(4):
        for j in range(4):
            x = SCREEN_X / 6.5 + j * BOARD_SIZE
            y = SCREEN_Y / 25 + i * BOARD_SIZE
            if NextBlockBoard[i][j] != 0:
                color = BLOCKS_COLOR[NextBlock]
            else:
                color = [50,50,50]
            pygame.draw.rect(screen, color, [x, y, BOARD_SIZE, BOARD_SIZE])
    for i in range(5):
        x = SCREEN_X / 6.5 + BOARD_SIZE * i
        y = SCREEN_Y / 25
        y2 = y + BOARD_SIZE * 4
        pygame.draw.line(screen, [125,125,125], [x, y], [x, y2], 2)
    for i in range(5):
        x = SCREEN_X / 6.5
        y = SCREEN_Y / 25 + BOARD_SIZE * i
        x2 = x + BOARD_SIZE * 4
        pygame.draw.line(screen, [125,125,125], [x, y], [x2, y], 2)
    Next_Text = TextFont.render("Next:", True, (255,255,255))
    screen.blit(Next_Text, (SCREEN_X/12,SCREEN_Y/30.75))
    pygame.display.flip()

def Func_Spawn_Block(Next_Block):
    global NextBlock, Block_Spawn_Ready, Run, Gameover
    id = Next_Block
    recent = NextBlock
    r = random.randint(0, len(BLOCKS) - 1)
    while r == recent:
        r = random.randint(0, len(BLOCKS) - 1)
    NextBlock = r
    block = numpy.concatenate(BLOCKS[id]).tolist()
    offset = BLOCKS_OFFSET[id]
    k = 0
    for i in range(BOARD_HEIGHT):
        for j in range(BOARD_WIDTH):
            if offset[0] <= i < offset[0] + 4 and offset[1] <= j < offset[1] + 4:
                if k < len(block) and CurrentBoard[i][j] != 0 and block[k] != 0:
                    Gameover = True
                    break
                k += 1
    k = 0
    for i in range(BOARD_HEIGHT):
        for j in range(BOARD_WIDTH):
            if offset[0] <= i < offset[0] + 4 and offset[1] <= j < offset[1] + 4:
                if k < len(block) and block[k] != 0:
                    if Gameover and CurrentBoard[i][j] != 0:
                        CurrentBoard[i][j] = [7, True, None]
                    else:
                        CurrentBoard[i][j] = [id, True, None]
                k += 1

def Func_Move_Block(args):
    dir = args[0]
    global CurrentBoard,Score
    movable_positions = []
    for i in range(BOARD_HEIGHT):
        for j in range(BOARD_WIDTH):
            if CurrentBoard[i][j] != 0 and CurrentBoard[i][j][1]:
                movable_positions.append((i, j))
    if dir == "Right":
        d=(0, 1)
    elif dir == "Left":
        d=(0, -1)
    elif dir == "Down":
        d=(1, 0)
    else:
        return
    for (i, j) in movable_positions:
        di, dj = i + d[0], j + d[1]
        if di < 0 or di >= BOARD_HEIGHT or dj < 0 or dj >= BOARD_WIDTH:
            return
        if CurrentBoard[di][dj] != 0 and not CurrentBoard[di][dj][1]:
            return
    if dir == "Down" and len(args) >= 2 and args[1] == True:
        Score += 1
    if dir in ["Right", "Down"]:
        movable_positions.sort(reverse=True)
    else:
        movable_positions.sort()
    for (i, j) in movable_positions:
        block_data = CurrentBoard[i][j]
        CurrentBoard[i][j] = 0
        di, dj = i + d[0], j + d[1]
        CurrentBoard[di][dj] = block_data

def Special_Effect(Special_Name,Height):
    global save_file_path, CurrentBoard
    if Special_Name == "Bomb":
        if Height>0:
            CurrentBoard[Height+1] = [0 for i in range(BOARD_WIDTH)]
    elif Special_Name == "Add_1":
        fill = []
        blank = random.randint(0,BOARD_WIDTH-1)
        for i in range(BOARD_WIDTH):
            if i==blank:
                fill.append(0)
            else:
                fill.append([random.randint(0,6),False,None])
        CurrentBoard[Height+1] = fill
    elif Special_Name == "Goal":
        print("목표에 도달하였습니다")
        level = int(save_file_path.split("level")[1].split(".txt")[0])
        save_file_path = "level"+str(level+1)+".txt"
        CurrentBoard = LoadSavedBoard()

def Func_Rotate_Block(dir):
    global CurrentBoard
    movable_positions = [(i, j) for i in range(BOARD_HEIGHT) for j in range(BOARD_WIDTH) if CurrentBoard[i][j] != 0 and CurrentBoard[i][j][1]]
    if not movable_positions:
        return
    block_id = CurrentBoard[movable_positions[0][0]][movable_positions[0][1]][0]
    min_row, max_row = min(p[0] for p in movable_positions), max(p[0] for p in movable_positions)
    min_col, max_col = min(p[1] for p in movable_positions), max(p[1] for p in movable_positions)
    height, width = max_row - min_row + 1, max_col - min_col + 1
    shape = [[0]*width for _ in range(height)]
    for (r, c) in movable_positions:
        shape[r - min_row][c - min_col] = 1
    if dir == 1:
        rotated_shape = list(zip(*shape))[::-1]
    elif dir == -1:
        rotated_shape = list(zip(*shape[::-1]))
    else:
        return
    rotated_height = len(rotated_shape)
    rotated_width = len(rotated_shape[0])
    kicks = [(0,0), (0,-1), (0,1), (1,0), (-1,0)]
    for kick_r, kick_c in kicks:
        new_row = min_row + kick_r
        new_col = min_col + kick_c
        if new_col < 0 or new_col + rotated_width > BOARD_WIDTH or new_row < 0 or new_row + rotated_height > BOARD_HEIGHT:
            continue
        collision = False
        for i in range(rotated_height):
            for j in range(rotated_width):
                if rotated_shape[i][j] == 1:
                    board_r = new_row + i
                    board_c = new_col + j
                    cell = CurrentBoard[board_r][board_c]
                    if cell != 0 and not cell[1]:
                        collision = True
                        break
            if collision:
                break
        if not collision:
            for (r, c) in movable_positions:
                CurrentBoard[r][c] = 0
            for i in range(rotated_height):
                for j in range(rotated_width):
                    if rotated_shape[i][j] == 1:
                        CurrentBoard[new_row + i][new_col + j] = [block_id, True]
            return

def Force_Fall_Block():
    global CurrentBoard, Score, Block_Spawn_Ready
    while True:
        movable_positions = [(i, j) for i in range(BOARD_HEIGHT) for j in range(BOARD_WIDTH) if CurrentBoard[i][j] != 0 and CurrentBoard[i][j][1]]
        can_move_down = True
        for (i, j) in movable_positions:
            ni = i + 1
            nj = j
            if ni >= BOARD_HEIGHT:
                can_move_down = False
                break
            if CurrentBoard[ni][nj] != 0 and not CurrentBoard[ni][nj][1]:
                can_move_down = False
                break
        if can_move_down:
            Func_Move_Block(["Down", True])
        else:
            for (i, j) in movable_positions:
                if CurrentBoard[i][j] != 0:
                    CurrentBoard[i][j][1] = False
            lines_cleared = 0
            new_board = []
            for i,row in enumerate(CurrentBoard):
                if all(cell != 0 and not cell[1] for cell in row):
                    for xx in row:
                        if len(xx)>2:
                            if xx[2]!=None and xx[2] in SPECIAL:
                                Special_Effect(xx[2],i)
                                if xx[2] == "Goal":
                                    break
                    lines_cleared += 1
                else:
                    new_board.append(row)
            for _ in range(lines_cleared):
                new_board.insert(0, [0]*BOARD_WIDTH)
            if lines_cleared >= 4:
                t="1LineUp"
                t="Player"+str(my_Turn)+" "+t
                if Players >= 2 and not DEBUG:
                    sock.sendto(t.encode('utf-8'),(player_ips[0],player_ports[0]))
                if Players >= 3 and not DEBUG:
                    sock.sendto(t.encode('utf-8'),(player_ips[1],player_ports[1]))
            CurrentBoard[:] = copy.deepcopy(new_board)
            Score += lines_cleared * 100
            Block_Spawn_Ready = True
            break

def Func_Fall_Block():
    global tick, fall_tick, Block_Spawn_Ready, CurrentBoard, Score
    if tick < fall_tick:
        return False
    movable_positions = [(i, j) for i in range(BOARD_HEIGHT) for j in range(BOARD_WIDTH) if CurrentBoard[i][j] != 0 and CurrentBoard[i][j][1]]
    can_move_down = True
    for (i, j) in movable_positions:
        ni = i + 1
        nj = j
        if ni >= BOARD_HEIGHT:
            can_move_down = False
            break
        if CurrentBoard[ni][nj] != 0 and not CurrentBoard[ni][nj][1]:
            can_move_down = False
            break
    if can_move_down:
        Func_Move_Block(["Down"])
    else:
        for (i, j) in movable_positions:
            if CurrentBoard[i][j] != 0:
                CurrentBoard[i][j][1] = False
        lines_cleared = 0
        new_board = []
        for i,row in enumerate(CurrentBoard):
            if all(cell != 0 and not cell[1] for cell in row):
                for xx in row:
                    if len(xx)>2:
                        if xx[2]!=None and xx[2] in SPECIAL:
                            Special_Effect(xx[2],i)
                            if xx[2] == "Goal":
                                break
                lines_cleared += 1
            else:
                new_board.append(row)
        for _ in range(lines_cleared):
            new_board.insert(0, [0]*BOARD_WIDTH)
        if lines_cleared >= 4:
            t="1LineUp"
            t="Player"+str(my_Turn)+" "+t
            if Players >= 2 and not DEBUG:
                sock.sendto(t.encode('utf-8'),(player_ips[0],player_ports[0]))
            if Players >= 3 and not DEBUG:
                sock.sendto(t.encode('utf-8'),(player_ips[1],player_ports[1]))
        CurrentBoard[:] = copy.deepcopy(new_board)
        Score += lines_cleared * 100
        Block_Spawn_Ready = True
    fall_tick = tick + (FPS/(1+(0.1*(Score//200))))
    return True

def Func_Change_Block(n):
    global NextBlock
    for row_idx, row in enumerate(CurrentBoard):
        for col_idx, cell in enumerate(row):
            if cell != 0 and cell[1] == True:
                CurrentBoard[row_idx][col_idx] = 0
    backup = NextBlock
    NextBlock = n
    Func_Spawn_Block(NextBlock)
    NextBlock = backup

def Func_Line_Up(lines):
    global CurrentBoard
    target_line = 0
    for i,row in enumerate(CurrentBoard):
        if row == [0 for i in range(BOARD_WIDTH)]:
            target_line = i
    fill = []
    blank = random.randint(0,BOARD_WIDTH-1)
    for i in range(BOARD_WIDTH):
        if i==blank:
            fill.append(0)
        else:
            fill.append([random.randint(0,6),False,None])
    CurrentBoard[target_line] = fill
    


def recv_thread(sock):#수정필요
    global data,winner,Run,ForceStop,CurrentBoard2
    while True:
        data,addr = sock.recvfrom(2400)
        data = data.decode('utf-8')
        spl_data = data.split(" ")
        playern = spl_data[0][6]
        spl_data.pop(0)
        data = ""
        for i,v in enumerate(spl_data):
            data=data+v
            if i!=len(spl_data)-1:
                data=data+" "

        print(f"정보를 받았습니다. from player{playern}\n{data}")
        if data == "1LineUp":
            Func_Line_Up(1)
            continue
        Loaded_Board = data.split(" ")
        Processed_Board = []
        tmp = []
        for i,q in enumerate(Loaded_Board):
            if q=="\n":
                continue
            if q=="0":
                tmp.append(0)
            else:
                t=q.split("$")
                if t==['']:
                    continue
                t[0]=int(t[0])
                if t[1]=="True":
                    t[1] = True
                else:
                    t[1] = False
                if t[2] == "None":
                    t[2] = None
                tmp.append(t)
            if len(tmp) == BOARD_WIDTH:
                Processed_Board.append(tmp)
                tmp = []
        # CurrentBoard2 = copy.deepcopy(Processed_Board)
        playern = int(playern)
        if Players == 2:
            PlayerB2.board_ref = copy.deepcopy(Processed_Board)
        if Players == 3:
            if my_Turn == 1:
                if playern == 2:
                    PlayerB2.board_ref = copy.deepcopy(Processed_Board)
                elif playern == 3:
                    PlayerB3.board_ref = copy.deepcopy(Processed_Board)
            elif my_Turn == 2:
                if playern == 1:
                    PlayerB2.board_ref = copy.deepcopy(Processed_Board)
                elif playern == 3:
                    PlayerB3.board_ref = copy.deepcopy(Processed_Board)
            elif my_Turn == 3:
                if playern == 1:
                    PlayerB2.board_ref = copy.deepcopy(Processed_Board)
                elif playern == 2:
                    PlayerB3.board_ref = copy.deepcopy(Processed_Board)
        # PlayerB2.update_board_ref(Processed_Board)
if Players > 1 and not DEBUG:
    th_recv = threading.Thread(target=recv_thread,args=(sock,),daemon=True)
    th_recv.start()

key_pressed = {"Down" : False,"Left" : False,"Right" : False}
key_cooldown = {"Right": 0, "Left": 0, "Down": 0}
COOLDOWN_TIME = 5

while Run:
    CLOCK.tick(FPS)
    screen.fill([0, 0, 0])
    something =  False
    if Block_Spawn_Ready:
        Func_Spawn_Block(NextBlock)
        something = True
        Block_Spawn_Ready = False
    Func_Update_Visual()
    if Func_Fall_Block():
        something = True
    if Gameover:
        print("Gameover")
        time.sleep(2)
        Run = False
        break
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            Run = False
            break
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                key_pressed["Right"] = True
            elif event.key == pygame.K_LEFT:
                key_pressed["Left"] = True
            elif event.key == pygame.K_DOWN:
                key_pressed["Down"] = True
            if event.key == pygame.K_z:
                Func_Rotate_Block(-1)
                something = True
            if event.key == pygame.K_x:
                Func_Rotate_Block(1)
                something = True
            if event.key == pygame.K_q:
                for i in CurrentBoard:
                    print(i)
            if event.key == pygame.K_p:
                Score += 1000
            if event.key == pygame.K_SPACE:
                Force_Fall_Block()
                something = True
            if event.key >= 49 and event.key <=55:
                Func_Change_Block(event.key-49)
                something = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT:
                key_pressed["Right"] = False
            if event.key == pygame.K_LEFT:
                key_pressed["Left"] = False
            if event.key == pygame.K_DOWN:
                key_pressed["Down"] = False
    for key in key_pressed:
        if key_pressed[key]:
            if key_cooldown[key] == 0:
                Func_Move_Block([key, True])
                key_cooldown[key] = COOLDOWN_TIME
                something = True
            else:
                key_cooldown[key] -= 1
        else:
            key_cooldown[key] = 0
    if something:
        t = ""
        for q in CurrentBoard:
            for i,p in enumerate(q):
                if p==0:
                    t=t+"0 "
                    continue
                if len(p)>2:
                    tt = str(p[0])+"$"+str(p[1])+"$"+str(p[2])
                else:
                    tt = str(p[0])+"$"+str(p[1])+"$None"
                t=t+tt+" "
            t=t+"\n "
        
        t="Player"+str(my_Turn)+" "+t
        if Players >= 2 and not DEBUG:
            sock.sendto(t.encode('utf-8'),(player_ips[0],player_ports[0]))
        if Players >= 3 and not DEBUG:
            sock.sendto(t.encode('utf-8'),(player_ips[1],player_ports[1]))
    tick+=1