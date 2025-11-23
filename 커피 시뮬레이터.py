import pygame
import time
import math

# 1. 초기 설정 및 색상 정의
pygame.init()
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
BROWN = (139, 69, 19)
GREEN = (0, 150, 0)
RED = (200, 50, 50)
BLUE = (50, 50, 200)
ORANGE = (255, 140, 0)
DARK_BROWN = (101, 67, 33)
LIGHT_GREEN = (144, 238, 144)
# 생분해 컵 분해 효과를 위한 색상 및 투명도 설정
DECOMPOSE_START_COLOR = GRAY 
DECOMPOSE_END_COLOR = (200, 200, 200, 128) # 분해 완료 색상 (약간 밝은 회색/투명한 느낌)

# 화면 크기
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("생분해 커피컵 씨앗 성장 시뮬레이션")

# --- 한글 폰트 설정 ---
KOREAN_FONT = None
try:
    KOREAN_FONT = pygame.font.match_font('malgungothic')
    if not KOREAN_FONT:
        KOREAN_FONT = pygame.font.match_font('NanumGothic')
except:
    KOREAN_FONT = None

font_small = pygame.font.Font(KOREAN_FONT, 24)
font_medium = pygame.font.Font(KOREAN_FONT, 28) # 중간 폰트 추가
font_large = pygame.font.Font(KOREAN_FONT, 30)
font_title = pygame.font.Font(KOREAN_FONT, 40)
# --- 한글 폰트 설정 끝 ---

# 2. 씨앗 종류 및 성장 속도 정의
SEED_PROFILES = {
    '1': {
        'name': "바질 (Basil)",
        'base_speed': 0.08, # 컵 영양분 (1차) 기본 성장 속도
        'max_height': 160,
        'color': GREEN,
        'coffee_multiplier': 1.8 # 커피 찌꺼기 영양분 (2차) 성장 배율
    },
    '2': {
        'name': "참나무 (Oak)",
        'base_speed': 0.02,
        'max_height': 200,
        'color': (100, 50, 0),
        'coffee_multiplier': 1.2
    },
    '3': {
        'name': "토마토 (Tomato)",
        'base_speed': 0.05,
        'max_height': 180,
        'color': (255, 100, 0),
        'coffee_multiplier': 2.5
    }
}

# 3. 객체 속성 및 상수 정의
CUP_WIDTH = 100
CUP_HEIGHT = 200
CUP_X = SCREEN_WIDTH // 2 - CUP_WIDTH // 2
GROUND_Y = SCREEN_HEIGHT - 50
RING_HEIGHT = 10
SEED_RADIUS = 5

# 제작자 정보 내용
CREATOR_INFO_LINES = [
    "--- 프로젝트 정보 ---",
    "제목: 생분해 커피컵 씨앗 성장 시뮬레이션",
    "전주 해커톤 대회에서 프로젝트 시뮬레이션 구현을 위해 만들었습니다",

    "--- 제작 정보 ---",
    "제작: Dangel",
    "사용 언어/라이브러리: Python, Pygame",
    
    "--- 기능 설명 ---",
    "1차 성장: 컵 분해 영양분 사용",
    "2차 성장: 커피 찌꺼기 발효 영양분 사용 (씨앗별 효율 차이)",
    "조작: 마우스 클릭 (진행), M키 (메뉴), R키/F키 (성장 배속)",
]

# --- 상태 정의 (CREATOR_INFO 추가) ---
STATE_NAMES = {
    "SEED_SELECTION": "씨앗선택",
    "CREATOR_INFO": "제작자 정보", # 신규 추가
    "READY": "대기 (클릭: 커피 마시기)",
    "DRINKING_COFFEE": "커피 마시는 중",
    "RING_MOVED": "링 분리 및 컵 상단 고정",
    "WAITING_FALL": "화분 심기 대기 (클릭: 낙하/심기)",
    "FALLING": "화분 (컵) 낙하 및 심는 중",
    "WAITING_DECOMPOSE": "컵 분해 준비 (클릭: 분해 시작)", 
    "CUP_DECOMPOSING": "1차 성장: 컵 분해 중", 
    "FERMENTING": "2차 성장 준비: 양분 발효 중", # 1차 성장 후 자동 진입
    "INITIAL_GROWING": "1차 성장 중 (컵 영양분)", 
    "GROWING": "2차 성장 중 (찌꺼기 영양분)",
    "GROWTH_COMPLETE": "성장 완료"
}

COFFEE_DRINKING_DURATION = 2
CUP_DECOMPOSITION_DURATION = 3 # 컵 분해 시간
FERMENTATION_DURATION = 5 # 커피 찌꺼기 발효 시간
INITIAL_GROWTH_HEIGHT = 50 # 1차 성장 최대 높이

FERMENTATION_BAR_WIDTH = 200
FERMENTATION_BAR_HEIGHT = 20
FERMENTATION_BAR_X = SCREEN_WIDTH // 2 - FERMENTATION_BAR_WIDTH // 2
FERMENTATION_BAR_Y = 150
MAX_GROWTH_FACTOR = 30.0
growth_factor_step = 0.5

# "메뉴로 돌아가기" 버튼 크기와 위치 (사용하지 않지만, 변수는 유지)
BACK_BUTTON_RECT = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 60, 200, 40)


# 4. 전역 변수 초기화 블록
game_state = "SEED_SELECTION"
selected_seed = None
plant_height = 0
fall_speed = 0
growth_start_time = 0
ferment_start_time = 0
decomposition_start_time = 0
decomposition_progress = 0
fermentation_progress = 0
global_growth_factor = 1.0
last_coffee_drink_time = 0
current_sediment_color = BROWN
current_cup_color = GRAY + (255,)
COFFEE_AMOUNT = 100

# 위치 변수 초기화
CUP_Y = SCREEN_HEIGHT - CUP_HEIGHT - 50

RING_INITIAL_Y = CUP_Y + CUP_HEIGHT * 0.7
RING_TARGET_Y = CUP_Y

ring_y_target = RING_TARGET_Y
ring_y_current = RING_INITIAL_Y


# --- 초기화/리셋 함수 ---
def reset_game_to_selection():
    global game_state, selected_seed, plant_height, fall_speed, growth_start_time, ferment_start_time, decomposition_start_time, decomposition_progress, fermentation_progress, global_growth_factor, last_coffee_drink_time, current_sediment_color, current_cup_color, COFFEE_AMOUNT, CUP_Y, ring_y_current, ring_y_target, RING_INITIAL_Y, RING_TARGET_Y

    game_state = "SEED_SELECTION"
    selected_seed = None
    plant_height = 0
    fall_speed = 0
    growth_start_time = 0
    ferment_start_time = 0
    decomposition_start_time = 0
    decomposition_progress = 0
    fermentation_progress = 0
    global_growth_factor = 1.0
    last_coffee_drink_time = 0
    current_sediment_color = BROWN
    current_cup_color = GRAY + (255,) # 컵 색상 초기화 (불투명)
    COFFEE_AMOUNT = 100

    # 컵 및 링 위치 초기화
    CUP_Y = SCREEN_HEIGHT - CUP_HEIGHT - 50
    RING_INITIAL_Y = CUP_Y + CUP_HEIGHT * 0.7
    RING_TARGET_Y = CUP_Y
    ring_y_target = RING_TARGET_Y
    ring_y_current = RING_INITIAL_Y

# --- 색상 보간 함수 (발효/분해 애니메이션) ---
def interpolate_color(color1, color2, factor, is_decomposition=False):
    # color1과 color2는 RGB 튜플 (a=255 가정)
    r = int(color1[0] + (color2[0] - color1[0]) * factor)
    g = int(color1[1] + (color2[1] - color1[1]) * factor)
    b = int(color1[2] + (color2[2] - color1[2]) * factor)
    
    a = 255 # 기본적으로 불투명
    if is_decomposition:
        # 분해 시에는 점점 투명해지도록 alpha 값 계산 (255 -> 128)
        a = int(255 + (128 - 255) * factor) 
        
    return (r, g, b, a)


# --- 5. 그리기 함수 ---
def draw_objects(screen):
    screen.fill(WHITE)
    # 땅 그리기 (메뉴 화면에서는 보이지 않음)
    if game_state != "SEED_SELECTION" and game_state != "CREATOR_INFO":
        pygame.draw.rect(screen, BROWN, (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))

    # A. SEED_SELECTION 상태 화면 
    if game_state == "SEED_SELECTION":
        title_text = font_title.render("생분해 커피컵 씨앗 성장 시뮬레이션", True, BLACK)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))

        select_text = font_title.render("씨앗 종류를 선택하세요 (숫자 입력)", True, BLACK)
        screen.blit(select_text, (SCREEN_WIDTH//2 - select_text.get_width()//2, 170))

        y_offset = 250
        for key, profile in SEED_PROFILES.items():
            text = font_large.render(
                f"[{key}] {profile['name']} (커피 찌꺼기 효율: x{profile['coffee_multiplier']:.1f}, 최대 성장: {profile['max_height']}px)",
                True,
                BLACK
            )
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 50

        control_text = font_small.render("시작 후 M키: 메뉴로 돌아오기", True, BLACK)
        screen.blit(control_text, (SCREEN_WIDTH//2 - control_text.get_width()//2, SCREEN_HEIGHT - 100))
        
        # 제작자 정보 탭 안내
        creator_text_info = font_medium.render("[C]키를 눌러 제작자 정보를 확인하세요", True, GRAY)
        screen.blit(creator_text_info, (SCREEN_WIDTH//2 - creator_text_info.get_width()//2, SCREEN_HEIGHT - 50))
        
        return
    
    # B. CREATOR_INFO 상태 화면
    elif game_state == "CREATOR_INFO":
        title_text = font_title.render("제작자 정보 및 프로젝트 개요", True, BLACK)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))

        y_offset = 200
        for line in CREATOR_INFO_LINES:
            color = BLACK
            if line.startswith("---"):
                color = BLUE
            
            text = font_medium.render(line, True, color)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 35
            
        # "메뉴로 돌아가기" 힌트 텍스트만 추가
        hint_text = font_large.render("[M] 키를 눌러 메뉴로 돌아가세요.", True, GRAY)
        screen.blit(hint_text, (SCREEN_WIDTH//2 - hint_text.get_width()//2, SCREEN_HEIGHT - 50))

        return # 상태별 화면 출력 완료

    # C. 나머지 상태 화면 (컵 그리기)

    # 컵 몸통 (분해 상태 반영) - 투명도를 위해 Surface 사용
    cup_surface = pygame.Surface((CUP_WIDTH, CUP_HEIGHT), pygame.SRCALPHA) 
    cup_surface.fill(current_cup_color) # RGBA 색상 적용
    screen.blit(cup_surface, (CUP_X, CUP_Y))

    # 커피 잔량 그리기
    coffee_fill_height = CUP_HEIGHT * (COFFEE_AMOUNT / 100.0)
    coffee_fill_rect = pygame.Rect(CUP_X + 2, CUP_Y + CUP_HEIGHT - coffee_fill_height, CUP_WIDTH - 4, coffee_fill_height - 2)
    pygame.draw.rect(screen, DARK_BROWN, coffee_fill_rect)

    # 커피 찌꺼기 층과 씨앗 그리기
    if COFFEE_AMOUNT <= 0:
        # 찌꺼기 층 (컵 바닥을 넓게 채움)
        sediment_height = 20
        sediment_rect = pygame.Rect(CUP_X + 2, CUP_Y + CUP_HEIGHT - sediment_height, CUP_WIDTH - 4, sediment_height)
        pygame.draw.rect(screen, current_sediment_color, sediment_rect)

        # 씨앗 (찌꺼기 층 중앙에 작은 검은 점)
        pygame.draw.circle(screen, BLACK, (CUP_X + CUP_WIDTH // 2, CUP_Y + CUP_HEIGHT - sediment_height // 2), SEED_RADIUS // 2 + 1)

    # 링 (이전과 동일)
    ring_rect = pygame.Rect(CUP_X - 5, ring_y_current, CUP_WIDTH + 10, RING_HEIGHT)
    pygame.draw.rect(screen, GRAY, ring_rect, 2)

    if abs(ring_y_current - RING_TARGET_Y) < 5 and COFFEE_AMOUNT <= 0:
        tab_width = 20
        tab_height = 5
        pygame.draw.rect(screen, GRAY, (CUP_X + 10, CUP_Y - tab_height, tab_width, tab_height))
        pygame.draw.rect(screen, GRAY, (CUP_X + CUP_WIDTH - 10 - tab_width, CUP_Y - tab_height, tab_width, tab_height))


    # 식물 성장 
    if game_state in ["INITIAL_GROWING", "GROWING", "GROWTH_COMPLETE", "FERMENTING"]:
        plant_color = selected_seed['color']
        plant_base_y = GROUND_Y
        plant_top_y = plant_base_y - plant_height

        # 줄기
        pygame.draw.line(screen, plant_color, (CUP_X + CUP_WIDTH // 2, plant_base_y), (CUP_X + CUP_WIDTH // 2, plant_top_y), 5)

        # 열매/꽃
        if plant_height > selected_seed['max_height'] * 0.3:
            if selected_seed['name'] == "토마토 (Tomato)":
                pygame.draw.circle(screen, RED, (CUP_X + CUP_WIDTH // 2 + 5, plant_top_y + 10), 15)
            else:
                pygame.draw.circle(screen, (255, 200, 0), (CUP_X + CUP_WIDTH // 2, plant_top_y), 10)

    # --- 상태별 중앙 메시지/게이지 출력 ---
    
    if game_state == "DRINKING_COFFEE":
        drinking_title = font_title.render("커피를 마시는 중...", True, DARK_BROWN)
        screen.blit(drinking_title, (SCREEN_WIDTH//2 - drinking_title.get_width()//2, FERMENTATION_BAR_Y - 50))

        # 잔량 퍼센트 표시
        remaining_percent = COFFEE_AMOUNT
        percent_text = font_large.render(f"잔량: {remaining_percent:.0f}%", True, BLACK)
        screen.blit(percent_text, (SCREEN_WIDTH//2 - percent_text.get_width() // 2, FERMENTATION_BAR_Y + 30))
        

    elif game_state == "RING_MOVED":
        move_text = font_title.render("링 분리/상단 고정 중...", True, GRAY)
        screen.blit(move_text, (SCREEN_WIDTH//2 - move_text.get_width()//2, FERMENTATION_BAR_Y - 50))
        info_text = font_small.render("하단 보관 통/드리퍼를 분리하고 링을 컵 상단에 고정합니다.", True, BLACK)
        screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, FERMENTATION_BAR_Y + 50))

    elif game_state == "WAITING_FALL":
        wait_text = font_title.render("[!] 컵을 땅에 심으려면 클릭하세요 [!]", True, ORANGE)
        screen.blit(wait_text, (SCREEN_WIDTH//2 - wait_text.get_width()//2, FERMENTATION_BAR_Y - 50))
        info_text = font_small.render("커피 찌꺼기와 씨앗이 담긴 컵이 땅으로 떨어지거나 꽂힙니다.", True, BLACK)
        screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, FERMENTATION_BAR_Y + 50))

    elif game_state == "WAITING_DECOMPOSE":
        wait_text = font_title.render("[!] 컵 분해를 시작하려면 클릭하세요 [!]", True, ORANGE)
        screen.blit(wait_text, (SCREEN_WIDTH//2 - wait_text.get_width()//2, FERMENTATION_BAR_Y - 50))
        info_text = font_small.render("**생분해 컵이 분해되며 1차 영양분이 공급됩니다. (씨앗 활성화)**", True, BLACK)
        screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, FERMENTATION_BAR_Y + 50))

    # 컵 분해 진행도 출력
    elif game_state == "CUP_DECOMPOSING":
        decompose_title = font_title.render("1차 영양분 공급 (컵 분해 중)...", True, ORANGE)
        screen.blit(decompose_title, (SCREEN_WIDTH//2 - decompose_title.get_width()//2, FERMENTATION_BAR_Y - 50))

        # 분해 게이지 바 그리기 (배경)
        pygame.draw.rect(screen, GRAY, (FERMENTATION_BAR_X, FERMENTATION_BAR_Y, FERMENTATION_BAR_WIDTH, FERMENTATION_BAR_HEIGHT), 2)
        # 분해 진행도 그리기: 분해 시작 색상(GRAY)으로 채움
        progress_width = FERMENTATION_BAR_WIDTH * decomposition_progress
        pygame.draw.rect(screen, DECOMPOSE_START_COLOR, (FERMENTATION_BAR_X, FERMENTATION_BAR_Y, progress_width, FERMENTATION_BAR_HEIGHT))

        # 진행률 텍스트 추가
        percent_text = font_large.render(f"분해: {decomposition_progress * 100:.0f}%", True, BLACK)
        screen.blit(percent_text, (FERMENTATION_BAR_X + FERMENTATION_BAR_WIDTH // 2 - percent_text.get_width() // 2, FERMENTATION_BAR_Y + 30))


    # 발효 진행도 출력
    elif game_state == "FERMENTING":
        ferment_title = font_title.render("2차 영양분 발효중...", True, ORANGE)
        screen.blit(ferment_title, (SCREEN_WIDTH//2 - ferment_title.get_width()//2, FERMENTATION_BAR_Y - 50))

        # 발효 게이지 바 그리기 (배경)
        pygame.draw.rect(screen, GRAY, (FERMENTATION_BAR_X, FERMENTATION_BAR_Y, FERMENTATION_BAR_WIDTH, FERMENTATION_BAR_HEIGHT), 2)
        # 발효 진행도 그리기: 완료 시 색상(LIGHT_GREEN)으로 채움
        progress_width = FERMENTATION_BAR_WIDTH * fermentation_progress
        pygame.draw.rect(screen, LIGHT_GREEN, (FERMENTATION_BAR_X, FERMENTATION_BAR_Y, progress_width, FERMENTATION_BAR_HEIGHT))

        # 진행률 텍스트 추가
        percent_text = font_large.render(f"발효: {fermentation_progress * 100:.0f}%", True, BLACK)
        screen.blit(percent_text, (FERMENTATION_BAR_X + FERMENTATION_BAR_WIDTH // 2 - percent_text.get_width() // 2, FERMENTATION_BAR_Y + 30))


    elif game_state == "GROWTH_COMPLETE":
        complete_text = font_title.render("성장 완료!", True, (0, 100, 0))
        screen.blit(complete_text, (SCREEN_WIDTH//2 - complete_text.get_width()//2, 100))

    # --- 공통 정보 출력 ---
    current_state_name = STATE_NAMES.get(game_state, game_state)
    state_text = font_large.render(f"상태: {current_state_name} (M키: 메뉴)", True, BLACK)

    if selected_seed:
        seed_info = font_large.render(f"선택된 씨앗: {selected_seed['name']} (최대 높이: {selected_seed['max_height']}px)", True, BLACK)
        screen.blit(seed_info, (10, 40))

    screen.blit(state_text, (10, 10))

    if game_state == "INITIAL_GROWING" or game_state == "GROWING" or game_state == "FERMENTING":
        growth_factor_info = font_large.render(f"성장 배속: x{global_growth_factor:.1f} (R키/F키로 조절)", True, BLACK if global_growth_factor == 1.0 else BLUE)
        screen.blit(growth_factor_info, (10, 70))

        if game_state == "INITIAL_GROWING":
            effective_speed = selected_seed['base_speed'] * global_growth_factor
            growth_text = font_small.render(f"1차 유효 성장 속도 (컵): x{effective_speed:.2f} (목표 높이: {INITIAL_GROWTH_HEIGHT}px)", True, BLACK)
            screen.blit(growth_text, (10, 105))
        elif game_state == "GROWING":
            effective_speed = selected_seed['base_speed'] * selected_seed['coffee_multiplier'] * global_growth_factor
            growth_text = font_small.render(f"2차 유효 성장 속도 (찌꺼기): x{effective_speed:.2f}", True, BLUE)
            screen.blit(growth_text, (10, 105))


# --- 6. 메인 게임 루프 ---
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # M키는 항상 메뉴로 돌아가도록 설정 (CREATOR_INFO 상태에서도 작동)
            if event.key == pygame.K_m:
                reset_game_to_selection()

            elif game_state == "SEED_SELECTION":
                # C 키를 눌러 제작자 정보 화면으로 이동
                if event.key == pygame.K_c:
                    game_state = "CREATOR_INFO"
                    
                key_name = pygame.key.name(event.key)
                if key_name in SEED_PROFILES:
                    selected_seed = SEED_PROFILES[key_name]
                    game_state = "READY"

            elif game_state == "INITIAL_GROWING" or game_state == "GROWING" or game_state == "GROWTH_COMPLETE" or game_state == "FERMENTING":
                if event.key == pygame.K_r:
                    global_growth_factor += growth_factor_step
                    if global_growth_factor > MAX_GROWTH_FACTOR:
                        global_growth_factor = 0.5
                    global_growth_factor = round(global_growth_factor, 1)
                elif event.key == pygame.K_f:
                    global_growth_factor = MAX_GROWTH_FACTOR

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "READY":
                if COFFEE_AMOUNT > 0:
                    game_state = "DRINKING_COFFEE"
                    last_coffee_drink_time = time.time()
                else:
                    game_state = "RING_MOVED"
            
            elif game_state == "WAITING_FALL":
                game_state = "FALLING"

            # 컵 분해 시작 (1차 영양분)
            elif game_state == "WAITING_DECOMPOSE":
                game_state = "CUP_DECOMPOSING"
                decomposition_start_time = time.time()
                current_cup_color = GRAY + (255,) 
            
            # CREATOR_INFO 상태에서는 마우스 클릭 이벤트 처리 제거됨.

    # --- 상태별 업데이트 로직 ---

    if game_state == "DRINKING_COFFEE":
        time_since_drink_start = time.time() - last_coffee_drink_time
        if time_since_drink_start < COFFEE_DRINKING_DURATION:
            COFFEE_AMOUNT = max(0, 100 - (time_since_drink_start / COFFEE_DRINKING_DURATION) * 100)
        else:
            COFFEE_AMOUNT = 0
            game_state = "READY"

    elif game_state == "RING_MOVED":
        if ring_y_current > ring_y_target:
            ring_y_current -= 5
        else:
            ring_y_current = ring_y_target
            game_state = "WAITING_FALL"

    elif game_state == "FALLING":
        fall_speed += 0.5
        CUP_Y += fall_speed
        ring_y_current = CUP_Y

        if CUP_Y + CUP_HEIGHT >= GROUND_Y:
            CUP_Y = GROUND_Y - CUP_HEIGHT
            ring_y_current = CUP_Y
            game_state = "WAITING_DECOMPOSE"

    # 컵 분해 (1차 영양분 공급)
    elif game_state == "CUP_DECOMPOSING":
        time_elapsed = time.time() - decomposition_start_time
        decomposition_progress = min(1.0, time_elapsed / CUP_DECOMPOSITION_DURATION)

        # 컵 색상 업데이트 (투명도 포함)
        current_cup_color = interpolate_color(GRAY, DECOMPOSE_END_COLOR[:3], decomposition_progress, is_decomposition=True)

        if decomposition_progress >= 1.0:
            game_state = "INITIAL_GROWING"
            # 분해 완료된 컵 색상 (RGBA 튜플)을 설정
            current_cup_color = (DECOMPOSE_END_COLOR[0], DECOMPOSE_END_COLOR[1], DECOMPOSE_END_COLOR[2], DECOMPOSE_END_COLOR[3])
            growth_start_time = time.time()

    # 1차 성장 (컵 영양분)
    elif game_state == "INITIAL_GROWING":
        if selected_seed:
            time_elapsed = time.time() - growth_start_time
            effective_speed = selected_seed['base_speed'] * global_growth_factor
            plant_height = min(INITIAL_GROWTH_HEIGHT, time_elapsed * effective_speed)

            if plant_height >= INITIAL_GROWTH_HEIGHT:
                # 1차 성장이 완료되면 자동으로 발효 단계로 진입
                game_state = "FERMENTING"
                ferment_start_time = time.time()

    # 발효 (2차 영양분)
    elif game_state == "FERMENTING":
        time_elapsed = time.time() - ferment_start_time
        fermentation_progress = min(1.0, time_elapsed / FERMENTATION_DURATION)

        # 커피 찌꺼기 색상 업데이트 (발효 진행에 따라)
        current_sediment_color = interpolate_color(BROWN, LIGHT_GREEN, fermentation_progress)[:3] # RGB만 사용

        if fermentation_progress >= 1.0:
            game_state = "GROWING"
            # 발효가 완료된 후, 2차 성장은 1차 성장 완료 시점(INITIAL_GROWTH_HEIGHT)부터 이어서 시작됩니다.
            growth_start_time = time.time()

    # 2차 성장 (커피 찌꺼기 영양분)
    elif game_state == "GROWING":
        if selected_seed:
            time_elapsed = time.time() - growth_start_time
            effective_speed = selected_seed['base_speed'] * selected_seed['coffee_multiplier'] * global_growth_factor
            # plant_height는 1차 성장 높이부터 시작하여 추가로 성장
            plant_height = INITIAL_GROWTH_HEIGHT + time_elapsed * effective_speed

            if plant_height > selected_seed['max_height']:
                plant_height = selected_seed['max_height']
                game_state = "GROWTH_COMPLETE"

    # 객체 그리기 및 화면 업데이트
    draw_objects(screen)
    pygame.display.flip()

    clock.tick(60)

pygame.quit()