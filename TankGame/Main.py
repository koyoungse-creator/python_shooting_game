# main.py

from tkinter import *
import random
import math
import config
import time # 루프 대기 시간을 위해 추가
from terrain import Terrain
from objects import Tank, Explosion

class GameMain:
    def __init__(self):
        self.window = Tk()
        self.window.title("Tank Battle")
        self.window.geometry(f"{config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        self.window.resizable(False, False)
        
        self.canvas = Canvas(self.window, bg="black")
        self.canvas.pack(fill=BOTH, expand=True)

        self.stage = 1
        self.keys = set()
        self.shells = []
        self.explosions = [] 
        
        # 턴 및 환경 변수
        self.current_turn = "PLAYER" # 현재 누구 턴인지
        self.turn_timer = 0

        # 업그레이드 메뉴 선택 디폴트 인덱스 (0: HP, 1: Damage)
        self.upgrade_selection = 0 
        
        self.terrain = Terrain(self.canvas)
        self.init_stage()

        self.window.bind("<KeyPress>", self.key_press)
        self.window.bind("<KeyRelease>", self.key_release)
        
        # 게임 Main 루프
        while True:
            try:
                self.process()

            except TclError: # x누르고 종료할 때 에러 안 뜨게 하기 위해
                return

            self.window.after(33) # 33ms 대기 (fps 조절)
            self.window.update()  # 화면 업데이트

    def init_stage(self):
        # 스테이지 초기화
        self.terrain.reset_terrain(self.stage)
        self.shells = []
        self.explosions = []

        # 턴과 상태 초기화
        self.current_turn = "PLAYER"
        self.game_state = config.STATE_PLAYER_MOVE
        self.turn_timer = 0
        
        # 플레이어 위치 리셋
        if hasattr(self, 'player'):
            self.player.x = 100
            self.player.terrain = self.terrain
            self.player.draw()
        else:
            self.player = Tank(self.canvas, 100, self.terrain, is_player=True)

        # 컴퓨터 위치 리셋
        comp_x = random.randint(config.SCREEN_WIDTH - 250, config.SCREEN_WIDTH - 50)
        self.computer = Tank(self.canvas, comp_x, self.terrain, is_player=False)
        if self.stage < 10:
            self.computer.max_hp = self.stage * 10            
            self.computer.hp = self.computer.max_hp
        self.computer.damage += (self.stage-1) // 3 * 5
        
        # UI 갱신
        self.draw_ui()    

    def restart_game(self):
        # 게임 완전 재시작
        self.stage = 1
        self.player.max_hp = config.DEFAULT_HP
        self.player.hp = self.player.max_hp
        self.player.damage = config.DEFAULT_DAMAGE
        self.init_stage()

    def key_press(self, event):
        self.keys.add(event.keysym)
        
        # 게임 오버 시 'r'로 재시작
        if self.game_state == config.STATE_GAME_OVER:
            if event.keysym.lower() == 'r':
                self.restart_game()
            return

        # 스테이지 완료 후 업그레이드 메뉴 조작
        if self.game_state == config.STATE_STAGE_CLEAR:
            if event.keysym == "Left":
                self.upgrade_selection = 0 # 왼쪽(HP) 선택
                self.show_upgrade_menu()   # 왼쪽에 하이라이트 생성
            elif event.keysym == "Right":
                self.upgrade_selection = 1 # 오른쪽(Damage) 선택
                self.show_upgrade_menu()   # 오른쪽에 하이라이트 생성
            elif event.keysym == "space":
                # 선택된 항목 적용
                if self.upgrade_selection == 0:
                    self.apply_upgrade("hp")
                else:
                    self.apply_upgrade("dmg")
            return

        # 게임 플레이 중 스페이스바로 상태 전환
        # 좌우키로 이동 -> 스페이스바 -> 각도조절 -> 스페이스바 -> 발사 강도 조절 -> 스페이스바 -> 발사
        if event.keysym == "space":
            if self.game_state == config.STATE_PLAYER_MOVE:
                self.game_state = config.STATE_PLAYER_AIM 
            elif self.game_state == config.STATE_PLAYER_AIM:
                self.game_state = config.STATE_PLAYER_POWER 
            elif self.game_state == config.STATE_PLAYER_POWER:
                self.fire_shell(self.player)
                self.game_state = config.STATE_SHELL_ACTIVE

    def key_release(self, event):
        if event.keysym in self.keys:
            self.keys.remove(event.keysym)

    def fire_shell(self, shooter):
        shell = shooter.fire()
        self.shells.append(shell)

    def handle_input(self):
        if self.game_state == config.STATE_PLAYER_MOVE:
            if "Left" in self.keys: self.player.move(-config.TANK_SPEED)
            if "Right" in self.keys: self.player.move(config.TANK_SPEED)
        elif self.game_state == config.STATE_PLAYER_AIM:
            if "Up" in self.keys: self.player.set_angle(1)
            if "Down" in self.keys: self.player.set_angle(-1)
        elif self.game_state == config.STATE_PLAYER_POWER:
            if "Up" in self.keys: self.player.set_power(1)
            if "Down" in self.keys: self.player.set_power(-1)

    def computer_turn(self):
        # 컴퓨터 탱크 이동
        if self.computer.hp == self.computer.max_hp:
            self.computer.move(random.randint(-5,5)) # 한 대 맞기 전에는 조금만 이동
        else:
            if self.computer.x > config.SCREEN_WIDTH-50:
                self.computer.move(-50)
            else:
                self.computer.move(random.choice([-40, -30, -20, 20, 30, 40, 50]))

        # 발사 각도랑 강도에 더해줄 에러
        error = random.random()
        error += 2 * self.computer.hp / self.computer.max_hp # 컴퓨터 체력이 높으면 에러도 큼
        error -= self.player.hp / self.player.max_hp         # 플레이어 체력이 낮으면 에러 작음

        dx = self.player.x - self.computer.x        # 수평 거리 차이
        dy = self.player.y - (self.computer.y - 25) # 수직 거리 차이, 포탄이 발사되는 높이를 고려해 25 빼줌

        H = random.randint(50, 300) # 포탄의 최대 고도,
        vy = -math.sqrt(2 * config.GRAVITY * ((self.computer.y - 25) - H))  # 수직 초기 속도

        # 발사 각도랑 강도 계산을 위한 근의 공식에 들어갈 계수들
        a = 0.5 * config.GRAVITY
        b = vy
        c = -dy
        
        D = b**2 - 4*a*c # 판별식
        
        if D < 0:
            T = 100
        else:
            T = (-b + math.sqrt(D)) / (2 * a)

        if T == 0:
            T = 0.01 # 0 나누기 방지
        vx = dx / T

        # 수직, 수평 속도를 이용해 발사 강도 구하기
        power = math.sqrt(vx**2 + vy**2)
        self.computer.power = min(100, max(1, power)) + int(random.uniform(-error, error))
        
        # 수직, 수평 속도를 이용해 발사 각도 산출. 
        radian_angle = math.atan2(-vy, vx)
        angle = math.degrees(radian_angle)
        self.computer.angle = angle + random.uniform(-error, error)

        # 발사
        self.fire_shell(self.computer)
        self.game_state = config.STATE_SHELL_ACTIVE

    def draw_ui(self):
        self.canvas.delete("ui")
        
        # 스테이지 표시
        self.canvas.create_text(config.SCREEN_WIDTH//2, 30, text=f"STAGE {self.stage}", font=("Arial", 30, "bold"), fill="white", tags="ui")

        # 플레이어 체력 표시
        hp_ratio = self.player.hp / self.player.max_hp
        hp_col = "green"
        if hp_ratio < 0.3: hp_col = "red"
        elif hp_ratio < 0.6: hp_col = "yellow"
        
        self.canvas.create_rectangle(20, 20, 220, 40, fill="red", tags="ui")
        self.canvas.create_rectangle(20, 20, 20 + 200 * hp_ratio, 40, fill=hp_col, tags="ui")
        self.canvas.create_text(20, 50, text=f"HP: {self.player.hp}/{self.player.max_hp}, DAMAGE: {self.player.damage}",
                               font=("Arial", 17), anchor=NW, fill="white", tags="ui")
        
        # 조작 단계 표시
        msg = ""
        if self.game_state == config.STATE_PLAYER_MOVE: 
            msg = "1. MOVE (Arrows) -> SPACE"
        elif self.game_state == config.STATE_PLAYER_AIM: 
            msg = f"2. Angle: {self.player.angle:.1f}° -> SPACE"
        elif self.game_state == config.STATE_PLAYER_POWER: 
            msg = f"3. SPEED: {self.player.power:.1f} -> SPACE (FIRE)"
        self.canvas.create_text(18, 76, text=msg, font=("Arial", 18), anchor=NW, fill="yellow", tags="ui")

        # 컴퓨터 체력 표시
        c_hp_ratio = self.computer.hp / self.computer.max_hp
        c_hp_col = "green"
        if c_hp_ratio < 0.3: c_hp_col = "red"
        elif c_hp_ratio < 0.6: c_hp_col = "yellow"

        self.canvas.create_rectangle(config.SCREEN_WIDTH-220, 20, config.SCREEN_WIDTH-20, 40, fill="red", tags="ui")
        self.canvas.create_rectangle(config.SCREEN_WIDTH-220, 20, config.SCREEN_WIDTH-220 + 200 * c_hp_ratio, 40, fill=c_hp_col, tags="ui")
        self.canvas.create_text(config.SCREEN_WIDTH-20, 50, 
                                text=f"Enemy HP: {self.computer.hp}/{self.computer.max_hp}, DAMAGE: {self.computer.damage}", 
                                font=("Arial", 17), anchor=NE, fill="white", tags="ui")

    def show_upgrade_menu(self):
        self.canvas.delete("upgrade") # 기존 메뉴 삭제 (다시 그리기 위해)
        
        self.canvas.create_rectangle(440, 200, 840, 400, fill="gray", tags="upgrade")
        self.canvas.create_text(640, 230, text="STAGE CLEARED!", font=("Arial", 20, "bold"), tags="upgrade")
        self.canvas.create_text(640, 260, text="Select Upgrade (Left / Right -> Space)", font=("Arial", 12), fill="white", tags="upgrade")
        
        # 버튼 스타일 설정
        # 선택된 버튼은 노란색 테두리와 두께 강조
        outline_hp = "yellow" if self.upgrade_selection == 0 else "black"
        width_hp = 5 if self.upgrade_selection == 0 else 1
        
        outline_dmg = "yellow" if self.upgrade_selection == 1 else "black"
        width_dmg = 5 if self.upgrade_selection == 1 else 1

        # 체력 버튼 (Left)
        btn_hp = self.canvas.create_rectangle(470, 300, 630, 360, fill="blue", outline=outline_hp, width=width_hp, tags="upgrade")
        self.canvas.create_text(550, 330, text="HP +20", fill="white", font=("Arial", 14, "bold"), tags="upgrade")
        
        # 공격력 버튼 (Right)
        btn_dmg = self.canvas.create_rectangle(650, 300, 810, 360, fill="red", outline=outline_dmg, width=width_dmg, tags="upgrade")
        self.canvas.create_text(730, 330, text="Damage +5", fill="white", font=("Arial", 14, "bold"), tags="upgrade")

    def apply_upgrade(self, type):
        if type == "hp":
            self.player.hp = min(self.player.hp + 20, self.player.max_hp)
        elif type == "dmg":
            self.player.damage += 5

        self.canvas.delete("upgrade")
        self.stage += 1
        self.init_stage()

    def process(self):
        if self.game_state in [config.STATE_PLAYER_MOVE, config.STATE_PLAYER_AIM, config.STATE_PLAYER_POWER]:
            self.handle_input()

        for exp in self.explosions[:]:
            if not exp.update():
                self.explosions.remove(exp)

        if self.game_state == config.STATE_SHELL_ACTIVE:
            if self.game_state in [config.STATE_STAGE_CLEAR, config.STATE_GAME_OVER]:
                pass 
            else:
                if not self.shells:
                    self.game_state = config.STATE_TURN_TRANSITION
                    self.turn_timer = 40 
                
                for shell in self.shells[:]:
                    target_list = [self.computer, self.player]
                    hit_result = shell.update(target_list)
                    
                    if hit_result:
                        self.explosions.append(Explosion(self.canvas, shell.x, shell.y))
                        
                        if isinstance(hit_result, Tank):
                            if self.computer.hp <= 0:
                                self.game_state = config.STATE_STAGE_CLEAR
                                self.upgrade_selection = 0 
                                self.shells = []
                                if self.stage >= 1:
                                   self.show_upgrade_menu()
                                break
                            elif self.player.hp <= 0:
                                self.game_state = config.STATE_GAME_OVER
                                self.canvas.create_text(config.SCREEN_WIDTH//2, config.SCREEN_HEIGHT//2,
                                                       text="GAME OVER\nPress 'R' to Restart", font=("Arial", 40), fill="black", justify=CENTER)
                                break

                    if not shell.is_active:
                        self.shells.remove(shell)

        if self.game_state == config.STATE_TURN_TRANSITION:
            if self.game_state not in [config.STATE_STAGE_CLEAR, config.STATE_GAME_OVER]:
                self.turn_timer -= 1
                if self.turn_timer <= 0:
                    if self.current_turn == "PLAYER":
                        self.current_turn = "COMPUTER"
                        self.game_state = config.STATE_COMPUTER_TURN
                        self.window.after(500, self.computer_turn)
                    else:
                        self.current_turn = "PLAYER"
                        self.game_state = config.STATE_PLAYER_MOVE

        self.draw_ui()

if __name__ == "__main__":
    GameMain()