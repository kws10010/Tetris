import pygame
import random
import copy
import time
import numpy
import os
os.environ['SDL_VIDEO_WINDOW_POS'] = "250,25"
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
                    tmp.append(t)
                if len(tmp) == BOARD_WIDTH:
                    Processed_Board.append(tmp)
                    tmp = []
            if Processed_Board == []:
                return [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]
            print(f"{save_file_path}에서 보드를 불러왔습니다.")
            return copy.deepcopy(Processed_Board)
    except Exception as e:
        if save_file_path == ".txt":
            print("새로 만듭니다.")
            return [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]
        print(f"파일을 불러오는 중 오류가 발생하였습니다: {e}")
        return [[0 for i in range(BOARD_WIDTH)] for i in range(BOARD_HEIGHT)]

COLOR = [
    [0,240,240],
    [0,0,240],
    [240,160,0],
    [240,240,0],
    [0,240,0],
    [160,0,240],
    [240,0,0],
    [255,255,255]
]

SPECIAL = [None,"Bomb","Add_1","Goal"]
SPECIAL_EMOJI = {None : "",
                 "Bomb" : "💥",
                 "Add_1" : "+1",
                 "Goal": "G"}

SCREEN_X,SCREEN_Y = 800,800
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
BOARD_SIZE = 30
BOARD_X_OFFSET = -(SCREEN_X/6)
FPS = 120
CLOCK = pygame.time.Clock()
pygame.init()
pygame.font.init()
EmojiFont = pygame.font.SysFont("Segoe UI Emoji", 24)
screen = pygame.display.set_mode([SCREEN_X, SCREEN_Y])
Board_Object = []
SelectionBoard_Object = []
SpecialBoard_Object = []
Gameover = False

CurrentBoard = LoadSavedBoard()

Run = True
class Board:
    def __init__(self,surface,color,xy,size,index):
        self.surface = surface
        self.color = color
        self.xy = xy
        self.size = size
        self.movable = False
        self.index = index
        self.selected = False
    def draw(self):
        pygame.draw.rect(self.surface,self.color,[self.xy[0],self.xy[1],self.size,self.size],0,50 if self.selected else 0)
    def setcolor(self,color):
        self.color = color
    def setselected(self,selected):
        self.selected = selected
    def returnmovable(self):
        return self.movable
    def returnAxis(self):
        return self.xy

for i in range(BOARD_HEIGHT):
    for j in range(BOARD_WIDTH):
        x = (SCREEN_X - (BOARD_WIDTH * BOARD_SIZE)) / 2 + BOARD_SIZE * j + BOARD_X_OFFSET
        y = (SCREEN_Y - (BOARD_HEIGHT * BOARD_SIZE)) / 2 + BOARD_SIZE * i
        Board_Object.append(Board(screen, [50,50,50], [x, y], BOARD_SIZE,i*BOARD_WIDTH+j))

for i,col in enumerate(COLOR):
    x = SCREEN_X//2 + i*BOARD_SIZE + 100 + i*5
    y = SCREEN_Y//2
    SelectionBoard_Object.append(Board(screen, col, [x, y], BOARD_SIZE,i*BOARD_WIDTH+j))

for i in range(len(SPECIAL)):
    x = SCREEN_X//2 + i*BOARD_SIZE + 100 + i*5
    y = SCREEN_Y//2 + 35
    SpecialBoard_Object.append(Board(screen, [50,50,50], [x, y], BOARD_SIZE,i*BOARD_WIDTH+j))

def Func_Update_Visual():
    global NextBlockBoard
    pygame.display.set_caption("테트리스 맵 에디터")


    for i,board in enumerate(Board_Object):
        if CurrentBoard[i//BOARD_WIDTH][i%BOARD_WIDTH]==0:
            board.setcolor([50,50,50])
        else:
            board.setcolor(COLOR[CurrentBoard[i//BOARD_WIDTH][i%BOARD_WIDTH][0]])
        board.draw()
    
    for i,board in enumerate(SelectionBoard_Object):
        if i == Selected_Color:
            board.setselected(True)
        else:
            board.setselected(False)
        board.draw()

    for i,board in enumerate(SpecialBoard_Object):
        if i == Selected_Special:
            board.setselected(True)
        else:
            board.setselected(False)
        board.setcolor(COLOR[Selected_Color])
        board.draw()
    
    for i, v in enumerate(CurrentBoard):
        for j, v2 in enumerate(v):
            if v2 != 0 and v2[2] != 'None':
                text = EmojiFont.render(SPECIAL_EMOJI[v2[2]], True, [0,0,0])
                x, y = Board_Object[(i * BOARD_WIDTH) + j].returnAxis()
                text_rect = text.get_rect(topleft=(x - 1, y + 2))
                screen.blit(text, text_rect)
    
    for i,board in enumerate(SpecialBoard_Object):
        text = EmojiFont.render(SPECIAL_EMOJI[SPECIAL[i]], True, [0,0,0])
        x, y = SpecialBoard_Object[i].returnAxis()
        text_rect = text.get_rect(topleft=(x - 1, y + 2))
        screen.blit(text, text_rect)
    for i in range(BOARD_WIDTH+1):
        x = (SCREEN_X - (BOARD_WIDTH * BOARD_SIZE)) / 2 + BOARD_SIZE * i + BOARD_X_OFFSET
        y = (SCREEN_Y - (BOARD_HEIGHT * BOARD_SIZE)) / 2
        y2 = y + BOARD_SIZE * BOARD_HEIGHT
        pygame.draw.line(screen, [185,185,185], [x, y], [x, y2], 2)
    for i in range(BOARD_HEIGHT+1):
        x = (SCREEN_X - (BOARD_WIDTH * BOARD_SIZE)) / 2 + BOARD_X_OFFSET
        y = (SCREEN_Y - (BOARD_WIDTH * BOARD_SIZE)) / 5 + BOARD_SIZE * i
        x2 = x + BOARD_SIZE * BOARD_WIDTH
        pygame.draw.line(screen, [185,185,185], [x, y], [x2, y], 2)
    pygame.display.flip()

Selected_Color = 0
Selected_Special = 0

def Func_Set_Board(AddorRemove,Index):
    global Selected
    if AddorRemove == "Add":
        CurrentBoard[Index//BOARD_WIDTH][Index%BOARD_WIDTH] = [Selected_Color,False,SPECIAL[Selected_Special]]
    else:
        CurrentBoard[Index//BOARD_WIDTH][Index%BOARD_WIDTH] = 0
    

inputted = {"LMB" : False,"RMB" : False}

while Run:
    CLOCK.tick(FPS)
    screen.fill([0, 0, 0])
    Func_Update_Visual()
    for event in pygame.event.get():
        Detect_Any_CB = False
        Detect_Any_SPB = False
        if event.type == pygame.QUIT:
            Run = False
            break
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for i, v in enumerate(SelectionBoard_Object):
                    j = v.returnAxis()
                    if x >= j[0] and x <= j[0] + BOARD_SIZE and y >= j[1] and y <= j[1] + BOARD_SIZE:
                        print("Color"+str(i))
                        Detect_Any_CB = True
                        break
                for ix, vx in enumerate(SpecialBoard_Object):
                    jx = vx.returnAxis()
                    if x >= jx[0] and x <= jx[0] + BOARD_SIZE and y >= jx[1] and y <= jx[1] + BOARD_SIZE:
                        print("Special"+str(ix))
                        Detect_Any_SPB = True
                        break
                if Detect_Any_CB or Detect_Any_SPB:
                    if Detect_Any_CB:
                        Selected_Color = i
                    if Detect_Any_SPB:
                        Selected_Special = ix
                    break
                inputted["LMB"] = True
            if event.button == 3:
                inputted["RMB"] = True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                inputted["LMB"] = False
            if event.button == 3:
                inputted["RMB"] = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                for i in CurrentBoard:
                    print(i)
            if event.key == pygame.K_s:
                save_file_path = input("저장할 맵 이름을 입력하세요.\n저장을 원치 않으면 exit를 입력하세요\n: ")+".txt"
                if save_file_path == "exit.txt":
                    continue
                try:
                    with open(save_file_path, "w", encoding="utf-8") as file:
                        t=""
                        for q in CurrentBoard:
                            for i,p in enumerate(q):
                                if p==0:
                                    t=t+"0 "
                                    continue
                                tt = str(p[0])+"$"+str(p[1])+"$"+str(p[2])
                                t=t+tt+" "
                            t=t+"\n "
                        file.write(t)
                        print(f"{save_file_path}에 보드를 저장하였습니다.")
                except Exception as e:
                    print(f"파일 저장 중 오류가 발생하였습니다: {e}")
    x, y = pygame.mouse.get_pos()
    if Detect_Any_CB or Detect_Any_SPB:
        continue
    for button in inputted:
        if inputted[button]:
            Found = False
            for i, v in enumerate(Board_Object):
                j = v.returnAxis()
                if x >= j[0] and x <= j[0] + BOARD_SIZE and y >= j[1] and y <= j[1] + BOARD_SIZE:
                    Found = True
                    break
            if Found:
                if button == "LMB":
                    Func_Set_Board("Add",i)
                if button == "RMB":
                    Func_Set_Board("Remove",i)