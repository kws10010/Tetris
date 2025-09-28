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
os.chdir('C:\\Users\\Windows10\\Desktop\\kws\\Tetris')

Started = False
Players = int(input("플레이어 수는? 최대 4명\n: "))
my_Turn = 1
player_ports = []
player_ips = []
my_port = 0
ports = [None,1234,2345,3456,4567]
if not DEBUG:
    if Players > 1:
        IS_LOCAL = False if int(input("로컬 실행 환경 입니까? 1 - 예 2 - 아니오\n: "))==2 else True
        #IS_LOCAL 값에 따라 다른 플레이어의 IP 주소가 localhost로 통합
        my_Turn = int(input("몇 번째 플레이어 입니까? 1~4\n: "))
        my_port = ports[my_Turn]#int(input("자신의 포트입력: "))

    for i in range(1,Players+1): #포트 플레이어에 따라 임의로 지정 >> ports 리스트
        if i!=my_Turn:
            player_ports.append(ports[i])
    for i in range(Players-1):
        if IS_LOCAL:
            player_ips.append("localhost")
        else:
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
FPS = 60
CLOCK = pygame.time.Clock()
pygame.init()
pygame.font.init()
TextFont = pygame.font.SysFont("Segoe UI Symbol", 24)
EmojiFont = pygame.font.SysFont("Segoe UI Emoji", 24)
screen = pygame.display.set_mode([SCREEN_X, SCREEN_Y], pygame.RESIZABLE)
Gameover = False

CurrentBoard = LoadSavedBoard() if not DEBUG else [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]
CurrentBoard2 = [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]
CurrentBoard3 = [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]
OtherBoards = {}
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

PlayerB1 = None
OthersPB = {}

def layout(screen_w, screen_h, others_count):
    right_w = int(screen_w * 0.35)
    center_w = screen_w - right_w
    main_size = int(min((center_w*0.9)//BOARD_WIDTH, (screen_h*0.9)//BOARD_HEIGHT))
    if main_size < 5:
        main_size = 5
    main_px_w = BOARD_WIDTH * main_size
    main_px_h = BOARD_HEIGHT * main_size
    main_x = (screen_w - right_w - main_px_w) // 2
    main_y = (screen_h - main_px_h) // 2
    mini_size = int(min((right_w*0.8)//BOARD_WIDTH, (screen_h*0.8/max(1,others_count))//BOARD_HEIGHT))
    if mini_size < 3:
        mini_size = 3
    mini_px_h = BOARD_HEIGHT * mini_size
    mini_px_w = BOARD_WIDTH * mini_size
    mini_x = screen_w - right_w + (right_w - mini_px_w)//2
    minis = []
    if others_count > 0:
        total_h = others_count * mini_px_h
        spacing = (screen_h - total_h) // (others_count + 1)
        y = spacing
        for i in range(others_count):
            minis.append((mini_x, y, mini_size))
            y += mini_px_h + spacing
    return (main_x, main_y, main_size), minis

def get_board_positions(players, screen_w, screen_h):
    main, minis = layout(screen_w, screen_h, players-1)
    res = [(main[0], main[1], main[2])]
    for m in minis:
        res.append(m)
    return res

def update_boards():
    global PlayerB1, OthersPB,CurrentBoard
    positions = get_board_positions(Players, SCREEN_X, SCREEN_Y)
    p1_x, p1_y, size1 = positions[0]
    PlayerB1 = PlayerBoard(1, p1_x, p1_y, size1, CurrentBoard)
    other_ids = sorted([i for i in range(1, Players+1) if i != my_Turn])
    for idx, pid in enumerate(other_ids):
        if pid not in OtherBoards:
            OtherBoards[pid] = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        x, y, s = positions[idx+1]
        OthersPB[pid] = PlayerBoard(pid, x, y, s, OtherBoards[pid])

update_boards()


def Func_Update_Visual():
    global NextBlockBoard
    pygame.display.set_caption(f"테트리스 [점수 : {Score}]")
    PlayerB1.draw()
    for pid in sorted(OthersPB.keys()):
        OthersPB[pid].draw()
    NextBlockBoard = copy.deepcopy(BLOCKS[NextBlock])
    next_size = int(PlayerB1.cell_size * 0.7)
    base_x = SCREEN_X // 25
    base_y = SCREEN_Y // 20
    for i in range(4):
        for j in range(4):
            x = base_x + j * next_size
            y = base_y + i * next_size
            color = BLOCKS_COLOR[NextBlock] if NextBlockBoard[i][j] != 0 else [50,50,50]
            pygame.draw.rect(screen, color, [x, y, next_size, next_size])
    for i in range(5):
        pygame.draw.line(screen, [125,125,125],
                         [base_x + next_size * i, base_y],
                         [base_x + next_size * i, base_y + next_size * 4], 2)
        pygame.draw.line(screen, [125,125,125],
                         [base_x, base_y + next_size * i],
                         [base_x + next_size * 4, base_y + next_size * i], 2)
    font_size = max(14, int(next_size * 0.8))
    font = pygame.font.SysFont("Segoe UI Symbol", font_size)
    Next_Text = font.render("Next:", True, (255,255,255))
    screen.blit(Next_Text, (base_x, base_y - font_size - 5))
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
        try:
            level = int(save_file_path.split("level")[1].split(".txt")[0])
        except Exception:
            level = 1
        save_file_path = f"level{level+1}.txt"
        CurrentBoard[:] = LoadSavedBoard()
        time.sleep(0.5)
        return


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
            isgoal = False
            for i,row in enumerate(CurrentBoard):
                if all(cell != 0 and not cell[1] for cell in row):
                    for xx in row:
                        if len(xx)>2:
                            if xx[2]!=None and xx[2] in SPECIAL:
                                Special_Effect(xx[2],i)
                                if xx[2] == "Goal":
                                    isgoal = True
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
                    for ip,port in zip(player_ips,player_ports):
                        sock.sendto(t.encode('utf-8'),(ip,port))
            if not isgoal:
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
        isgoal = False
        for i,row in enumerate(CurrentBoard):
            if all(cell != 0 and not cell[1] for cell in row):
                for xx in row:
                    if len(xx)>2:
                        if xx[2]!=None and xx[2] in SPECIAL:
                            Special_Effect(xx[2],i)
                            if xx[2] == "Goal":
                                isgoal = False
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
                for ip,port in zip(player_ips,player_ports):
                    sock.sendto(t.encode('utf-8'),(ip,port))
        if not isgoal:
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
    for x in range(lines):
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


def recv_thread(sock):
    global Run, OtherBoards, OthersPB, Started
    while True:
        data,addr = sock.recvfrom(1<<20)
        data = data.decode('utf-8')
        spl_data = data.split(" ")
        header = spl_data[0]
        if not header.startswith("Player"):
            continue
        playern = int(header[6:])
        if playern == 1 and not Started:
            Started = True
        payload = " ".join(spl_data[1:])
        if playern == my_Turn:
            continue
        if payload == "1LineUp":
            Func_Line_Up(1)
            continue
        Loaded_Board = payload.split(" ")
        Processed_Board = []
        tmp = []
        for q in Loaded_Board:
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
        OtherBoards[playern] = copy.deepcopy(Processed_Board)
        if playern not in OthersPB:
            OthersPB[playern] = PlayerBoard(playern, 0, 0, 5, OtherBoards[playern])
        OthersPB[playern].board_ref = OtherBoards[playern]

if Players > 1 and not DEBUG:
    th_recv = threading.Thread(target=recv_thread,args=(sock,),daemon=True)
    th_recv.start()

key_pressed = {"Down" : False,"Left" : False,"Right" : False}
key_cooldown = {"Right": 0, "Left": 0, "Down": 0}
COOLDOWN_TIME = 3


if my_Turn != 1:
    while not Started:
        print("게임이 시작될때까지 대기하세요")
        time.sleep(0.25)
        if Started:
            break

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
        if event.type == pygame.VIDEORESIZE:
            SCREEN_X, SCREEN_Y = event.w, event.h
            screen = pygame.display.set_mode((SCREEN_X, SCREEN_Y), pygame.RESIZABLE)
            update_boards()
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
            if event.key == pygame.K_o:
                Score -= 1000
            if event.key == pygame.K_s:
                if Players >= 2 and not DEBUG:
                    t=input("다른 플레이어에게 전달할 메시지 입력\n: ")
                    t="Player"+str(my_Turn)+" "+t
                    for ip,port in zip(player_ips,player_ports):
                        sock.sendto(t.encode('utf-8'),(ip,port))
                else:
                    print("현재 사용 불가")
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
            for p in q:
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
            for ip,port in zip(player_ips,player_ports):
                sock.sendto(t.encode('utf-8'),(ip,port))
    tick+=1
