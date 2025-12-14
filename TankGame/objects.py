# objects.py

from tkinter import *
from PIL import Image, ImageTk
import math

from PIL.ImageDraw import Outline
import config

class Tank:
    def __init__(self, canvas, x, terrain, is_player=True):
        self.canvas = canvas
        self.terrain = terrain
        self.is_player = is_player
        
        # 최대 체력, 현재 체력, 충격량
        self.max_hp = config.DEFAULT_HP
        self.hp = self.max_hp
        self.damage = config.DEFAULT_DAMAGE
        
        # x좌표, y좌표 (지형 상태에 따라 달라짐), 포탑 각도, 발사 세기
        self.x = x
        self.y = terrain.get_height(x)
        self.angle = 45 if is_player else 135
        self.power = 15
        
        # 이미지 로드 (PIL 회전 처리)

        # 1. 차체
        self.body_img = Image.open("image/tank.png")
        if not self.is_player: 
            self.body_img = self.body_img.transpose(Image.FLIP_LEFT_RIGHT)
        self.body_tk = ImageTk.PhotoImage(self.body_img)

        # 2. 포탑
        self.turret_img = Image.open("image/tank_weapon.png")

        self.body_id = None
        self.turret_id = None
        self.draw()

    def draw(self):
        # 기존 그림 삭제
        if self.body_id: self.canvas.delete(self.body_id)
        if self.turret_id: self.canvas.delete(self.turret_id)

        # 차체 그리기
        self.y = self.terrain.get_height(self.x)
        self.body_id = self.canvas.create_image(self.x, self.y, image=self.body_tk, tags="tank")
        
        # 포탑 그리기
        rotated_img = self.turret_img.rotate(self.angle) # 포탑 회전
        self.turret_tk = ImageTk.PhotoImage(rotated_img)
        if self.is_player:
            self.turret_id = self.canvas.create_image(self.x+15, self.y-5, image=self.turret_tk, tags="tank")
        else:
            self.turret_id = self.canvas.create_image(self.x-15, self.y-5, image=self.turret_tk, tags="tank")

    def move(self, dx):
        self.x += dx
        self.x = max(0, min(self.x, config.SCREEN_WIDTH - 1))
        self.draw()

    def set_angle(self, change):
        self.angle += change
        self.angle = max(-20, min(200, self.angle))
        self.draw()

    def set_power(self, change):
        self.power += change
        self.power = max(1, min(100, self.power))

    def fire(self):
        rad = math.radians(self.angle)
        vx = self.power * math.cos(rad)
        vy = -self.power * math.sin(rad)        
        return Shell(self.canvas, self.x, self.y - 25, vx, vy, self.terrain, self.damage, self)

    def take_damage(self, damage):
        self.hp -= damage
        self.hp = max(0, self.hp)
        return self.hp <= 0

class Shell:
    def __init__(self, canvas, x, y, vx, vy, terrain, damage, shooter):
        self.canvas = canvas
        self.x = x   # x좌표
        self.y = y   # y좌표
        self.vx = vx # x축 방향 속도
        self.vy = vy # y축 방향 속도
        self.terrain = terrain
        self.damage = damage
        self.shooter = shooter
        self.is_active = True
        self.id = self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="black")

    def update(self, tanks):
        if not self.is_active: return None

        # 포탄 이동
        self.x += self.vx         # 새 x좌표
        self.y += self.vy         # 새 y좌표
        self.vy += config.GRAVITY # 중력 방향 속도 변화

        self.canvas.coords(self.id, self.x-3, self.y-3, self.x+3, self.y+3) # 포탄 이동

        # 화면 밖 처리
        if self.x < 0 or self.x > config.SCREEN_WIDTH or self.y > config.SCREEN_HEIGHT:
            self.destroy()
            return None        

        # 탱크 충돌
        for tank in tanks:

            # bbox(id)는 id의 좌상단의 좌표와 우하단의 좌표를 리스트로 반환
            if tank.body_id:
                bbox = self.canvas.bbox(tank.body_id)
                if bbox:
                    # 포탄 좌표가 사각형 안에 있는지 확인
                    if bbox[0]-2 <= self.x <= bbox[2]+2 and bbox[1]-2 <= self.y <= bbox[3]-2:
                        is_dead = tank.take_damage(self.damage)
                        self.destroy()
                        return tank # 맞은 탱크 객체 반환
        
        # 지형 충돌
        if self.y >= self.terrain.get_height(self.x): # y축 방향과 부등호 방향 주의
            self.terrain.destroy_land(self.x, config.EXPLOSION_RADIUS)
            self.destroy()
            return "ground" # 땅에 맞음
                    
        return None

    def destroy(self):
        self.is_active = False
        self.canvas.delete(self.id)

# 폭발 이펙트 클래스
class Explosion:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.time = 15 # 이펙트 지속 시간 (프레임)
        self.id = self.canvas.create_oval(x-10, y-10, x+10, y+10, fill="orange", outline="red")
    
    def update(self):
        self.time -= 1
        if self.time <= 0:
            self.canvas.delete(self.id)
            return False
        return True