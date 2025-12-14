# config.py

# 화면 크기
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# 세부 변수 설정
GRAVITY = 0.25        # 중력
EXPLOSION_RADIUS = 10 # 지형 파괴 범위
TANK_SPEED = 5        # 이동 속도
DEFAULT_HP = 100       # 기본 체력
DEFAULT_DAMAGE = 20   # 기본 포탄 데미지량

# 게임 상태
STATE_PLAYER_MOVE = 0     # 플레이어 이동
STATE_PLAYER_AIM = 1      # 플레이어 각도 조절
STATE_PLAYER_POWER = 2    # 플레이어 파워 조절
STATE_SHELL_ACTIVE = 3    # 포탄 날아가는 중
STATE_COMPUTER_TURN = 4   # 컴퓨터 턴
STATE_GAME_OVER = 5       # 게임 종료
STATE_STAGE_CLEAR = 6     # 스테이지 클리어
STATE_TURN_TRANSITION = 7 # 턴 교체 대기
