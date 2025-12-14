# terrain.py

from tkinter import *
from PIL import Image, ImageTk, ImageDraw
import random
import math
import config

class Terrain:
    def __init__(self, canvas):
        self.canvas = canvas
        self.height_map = [] # 지형의 높이 정보를 담는 리스트
        self.ground = None
        self.sky = None
        
        # 이미지 로드
        self.sky_img = Image.open("image/bgimage.png").resize((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.tk_sky_img = ImageTk.PhotoImage(self.sky_img)
            
        self.rock_img = Image.open("image/rock_texture.png").resize((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        

        # 초기 지형 생성
        self.reset_terrain(stage=1)

    def reset_terrain(self, stage):
        self.height_map = []
        self.generate(stage)
        self.draw_sky()
        self.draw_ground()

    def generate(self, stage):
        # 평지 생성
        base_height = config.SCREEN_HEIGHT - 100
        self.height_map = [base_height] * config.SCREEN_WIDTH

        # 울퉁불퉁함 구현 
        current = base_height
        for x in range(config.SCREEN_WIDTH):
            current += random.uniform(-3, 3) # random.random 사용 시 너무 극단적인 지형이 나오기 쉽다
            current = max(200, min(config.SCREEN_HEIGHT - 50, current))
            self.height_map[x] = current

        # 플레이어와 컴퓨터 사이에 벽 생성, stage 증가 시 벽 개수 증가
        num_walls = random.randint(1, 1 + (stage // 3))
        for _ in range(num_walls):
            cx = random.randint(450, config.SCREEN_WIDTH - 450) # cx : 벽의 중심의 x좌표
            width = random.randint(50, 125)
            height = random.randint(70, 400)

            lx = max(0, cx - width//2)                   # lx : 벽의 왼쪽 끝의 x좌표
            rx = min(config.SCREEN_WIDTH, cx + width//2) # rx : 벽의 오른쪽 끝의 x좌표

            for x in range(lx, rx):
                ratio = (x - (cx - width//2)) / width     # ratio 값은 0에서 시작해 1을 찍고 다시 0으로 간다
                bump = math.sin(ratio * math.pi) * height # sin함수를 이용해 둥근 모양이 나오도록 구현
                self.height_map[x] -= bump                # x좌표에 해당하는 y좌표의 값을 작게 해야 벽이 생긴다

    def draw_sky(self):
        
        s1 = self.canvas.create_image(0, 0, image=self.tk_sky_img, anchor=NW, tags="sky")
        self.sky = s1

    def draw_ground(self):
        # 포탄에 의해 지형에 변형이 생긴 후, 새 지형 이미지를 불러오기 전 기존 지형 삭제
        if self.ground:
            self.canvas.delete(self.ground)

        # 마스킹을 이용한 지형 그리기 (tk는 이미지를 사각형으로밖에 못 불러오는 것 같음)
        mask = Image.new("L", (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), 0) # 화면 크기의 흑백 이미지
        draw = ImageDraw.Draw(mask)

        # 울퉁불퉁한 땅의 모양을 이루는 다각형의 좌표을 순서대로 담음
        coords = [(config.SCREEN_WIDTH, config.SCREEN_HEIGHT), (0, config.SCREEN_HEIGHT)]
        for x in range(0, config.SCREEN_WIDTH):
            coords.append((x, self.height_map[x]))
        
        # 위에서 구한 좌표를 기준으로 땅의 모양을 그리고 하얗게 채움
        draw.polygon(coords, fill=255) 

        # rock_img에 마스크 적용 : 255인 부분에는 이미지가 보이고, 0인 부분에는 이미지가 안 보임
        final_ground = self.rock_img.copy()
        final_ground.putalpha(mask)

        # Tkinter 이미지로 변환 및 그리기
        self.tk_ground_final = ImageTk.PhotoImage(final_ground)
        self.ground = self.canvas.create_image(0, 0, image=self.tk_ground_final, anchor=NW, tags="ground")
        
        # 탱크 객체들과 UI를 지형보다 앞으로 가져옴
        self.canvas.tag_raise("tank") 
        self.canvas.tag_raise("ui")

    def get_height(self, x):
        x = int(max(0, min(x, config.SCREEN_WIDTH - 1)))
        return self.height_map[x]

    def destroy_land(self, hit_x, radius):
        hit_x = int(hit_x)
        changed = False
        for x in range(max(0, hit_x - radius), min(config.SCREEN_WIDTH, hit_x + radius)):
            dx = x - hit_x
            if radius**2 - dx**2 >= 0:
                depth = math.sqrt(radius**2 - dx**2)
                if self.height_map[x] < config.SCREEN_HEIGHT:
                    self.height_map[x] += depth
                    changed = True
        
        if changed:
            self.draw_ground()