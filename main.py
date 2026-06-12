import pygame
import sys
import random
import os

pygame.display.init()
pygame.font.init()
pygame.events = pygame.event

# 상수
WIDTH, HEIGHT = 800, 600
FPS = 60
SPEED = 300
BG_WIDTH = 2000
BG_HEIGHT = 1500

class Note:
    """메모리 및 속도 향상을 위해 __slots__를 적용한 클래스 정의"""
    __slots__ = ('idx', 'bit', 'x', 'y', 'render_x', 'render_y', 'img', 'dimmed_img', 'clear_rect')
    def __init__(self, idx, bit, x, y, render_x, render_y, img, dimmed_img, clear_rect):
        self.idx = idx
        self.bit = bit
        self.x = x
        self.y = y
        self.render_x = render_x
        self.render_y = render_y
        self.img = img
        self.dimmed_img = dimmed_img
        self.clear_rect = clear_rect

def create_background():
    """배경 표면을 미리 생성하여 반환 (최적화)"""
    bg = pygame.Surface((2000, 1500)).convert()
    bg.fill((0, 0, 0))
    
    for x in range(0, 2000, 100):
        for y in range(0, 1500, 100):
            for _ in range(2):
                sx = x + random.randint(0, 98)
                sy = y + random.randint(0, 98)
                # 경계값 안전 체크
                if sx < 2000 and sy < 1500:
                    bg.fill((255, 255, 255), (sx, sy, 2, 2))
                    
    return bg

def change_color(surface, color):
    """지정된 색상으로 흰색 이미지를 염색 (알파 채널 보존) - 고성능 내장 블렌딩 모드 사용"""
    colored = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    colored.fill(color)
    colored.blit(surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return colored

def main():
    screen = pygame.display.set_mode((800, 600), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("Fix The MMU")
    clock = pygame.time.Clock()
    
    mmu_img = None
    player_img = None
    note_img = None
    fire_img = None
    spritesheet_path = "spritesheet.png"
    if os.path.exists(spritesheet_path):
        try:
            sheet = pygame.image.load(spritesheet_path).convert_alpha()
            # Rect 객체 대신 튜플을 전달하여 객체 생성 비용 제거
            mmu_img = sheet.subsurface((0, 0, 40, 20))
            player_img = sheet.subsurface((40, 10, 15, 16))
            note_img = sheet.subsurface((40, 0, 15, 10))
            fire_img = sheet.subsurface((26, 20, 14, 6))
        except pygame.error:
            pass
            
    # 배경 생성
    bg_surface = create_background()
    
    # 플레이어 이미지 크기 확대 및 크기 정보 캐싱 (스케일 연산 하드코딩)
    if player_img is not None:
        player_img = pygame.transform.scale(player_img, (60, 64))
        player_half_w = 30
        player_half_h = 32
    else:
        player_img = pygame.Surface((120, 120), pygame.SRCALPHA)
        player_img.fill((255, 200, 0))
        player_half_w = 60
        player_half_h = 60
        
    # MMU 이미지 크기 확대 및 고정 그리기 좌표 연산 미리 하드코딩
    if mmu_img is not None:
        mmu_img = pygame.transform.scale(mmu_img, (160, 80))
        mmu_const_x = 920   # 1000 - 80
        mmu_const_y = 710   # 750 - 40
    else:
        mmu_img = pygame.Surface((200, 100), pygame.SRCALPHA)
        mmu_img.fill((0, 100, 255))
        mmu_const_x = 900   # 1000 - 100
        mmu_const_y = 700   # 750 - 50
        
    # 불꽃 이미지 크기 확대 및 고정 그리기 좌표 연산 미리 하드코딩
    if fire_img is not None:
        fire_img = pygame.transform.scale(fire_img, (56, 24))
    else:
        fire_img = pygame.Surface((36, 24), pygame.SRCALPHA)
        fire_img.fill((255, 0, 0))
    fire_const_x = 872      # 1000 - 80 - 48
    fire_const_y = 738      # 750 - 12
        
    # 각 색상별 노트 생성 및 랜덤 배치 (음표 크기는 확대하지 않음)
    note_colors = [
        (137, 207, 240),
        (255, 255, 255),
        (0, 51, 153),
        (255, 255, 0),
        (255, 0, 0),
        (255, 105, 180)
    ]
    
    notes = []
    for i, rgb in enumerate(note_colors):
        colored_note = change_color(note_img, rgb) if note_img is not None else None
        if colored_note is None:
            colored_note = pygame.Surface((15, 10), pygame.SRCALPHA)
            colored_note.fill(rgb)
            
        # 어두운 버전의 노트 이미지 생성 (최소 밝기 35 보장)
        dimmed_rgb = (max(35, int(rgb[0] * 0.25)), max(35, int(rgb[1] * 0.25)), max(35, int(rgb[2] * 0.25)))
        dimmed_note = change_color(note_img, dimmed_rgb) if note_img is not None else None
        if dimmed_note is None:
            dimmed_note = pygame.Surface((15, 10), pygame.SRCALPHA)
            dimmed_note.fill(dimmed_rgb)
        
        nx = float(random.randint(50, 1950))
        ny = float(random.randint(50, 1450))
        
        # 15x10 고정 크기이므로 오프셋 및 지우기 영역도 튜플로 대체하여 Rect 객체 생성 배제
        nx_int = int(nx)
        ny_int = int(ny)
        rx = nx_int - 7
        ry = ny_int - 5
        
        notes.append(Note(
            idx=i,
            bit=1 << i,
            x=nx,
            y=ny,
            render_x=rx,
            render_y=ry,
            img=colored_note,
            dimmed_img=dimmed_note,
            clear_rect=(rx, ry, 15, 10)
        ))

    collected_mask = 0
    ending_state = False
    shake_frames = 0
    shake_triggered = False
    
    # 엔딩용 폰트 생성
    font_large = pygame.font.SysFont(None, 60)
    font_medium = pygame.font.SysFont(None, 30)
    font_small = pygame.font.SysFont(None, 24)
    
    # UI용 이미지 리스트 (변화할 때만 업데이트하여 매프레임 연산 회피)
    ui_slots = [note.dimmed_img for note in notes]
    
    # 플레이어의 월드 좌표를 랜덤하게 지정 (맵 내부)
    player_x = float(random.randint(0, 2000))
    player_y = float(random.randint(0, 1500))
    
    # 파이썬 한정 캐싱 최적화
    event_get = pygame.event.get
    key_get_pressed = pygame.key.get_pressed
    K_w, K_s, K_a, K_d, K_c, K_ESCAPE = pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, pygame.K_c, pygame.K_ESCAPE
    QUIT = pygame.QUIT
    screen_blit = screen.blit
    display_flip = pygame.display.flip
    tick = clock.tick
    int_cast = int
    randint = random.randint
    
    # 각종 상수값 외부 변수로 캐싱 (연산 제거)
    bg_width_float = 2000.0
    bg_height_float = 1500.0
    max_cam_x = 1200.0
    max_cam_y = 900.0
    
    running = True
    while running:
        if ending_state:
            # 엔딩 상태 이벤트 처리 (ESC 키 또는 창 닫기로 종료)
            for event in event_get():
                if event.type == QUIT:
                    running = False
            
            keys = key_get_pressed()
            if keys[K_ESCAPE]:
                running = False
                
            # 엔딩 연출 렌더링 (다크 네이비 테두리 및 프리미엄 블랙 배경)
            screen.fill((10, 10, 15))
            pygame.draw.rect(screen, (0, 100, 255), (20, 20, 760, 560), 2)
            
            # MMU, 엔진 화염, 플레이어를 센터에 고정 렌더링
            screen_blit(fire_img, (272, 208))
            screen_blit(mmu_img, (320, 180))
            screen_blit(player_img, (460, 188))
            
            # 텍스트 부드러운 펄싱(Pulsing) 효과 계산
            pulse = (pygame.time.get_ticks() // 8) % 200
            glow_val = pulse if pulse < 100 else 200 - pulse
            glow_color = (int(137 + glow_val * 1.18), int(207 + glow_val * 0.48), 240)
            
            text_title = font_large.render("MISSION SUCCESS!", True, glow_color)
            text_sub = font_medium.render("The MMU is repaired! Now we can head to MIXXTOPIA.", True, (200, 200, 200))
            text_exit = font_small.render("Press [ESC] to Quit", True, (120, 120, 120))
            
            screen_blit(text_title, text_title.get_rect(center=(400, 360)))
            screen_blit(text_sub, text_sub.get_rect(center=(400, 410)))
            screen_blit(text_exit, text_exit.get_rect(center=(400, 470)))
            
            display_flip()
            tick(60)
            continue
            
        # 나누기 대신 곱하기를 통해 dt 계산 단축 (300 / 1000 = 0.3)
        speed_dt = tick(60) * 0.3
        
        for event in event_get():
            if event.type == QUIT:
                running = False
                
        keys = key_get_pressed()
        
        # 'C' 키 치트키 (누르면 모든 음표가 수집된 상태로 처리되고 맵에서 블랙아웃됨)
        if keys[K_c] and collected_mask != 63:
            for note in notes:
                if not (collected_mask & note.bit):
                    bg_surface.fill((0, 0, 0), note.clear_rect)
                    ui_slots[note.idx] = note.img
            collected_mask = 63
            
        # 흔들림 프레임이 있는 경우 조작 차단 및 흔들림 연산 진행
        shake_x = 0
        shake_y = 0
        if shake_frames > 0:
            shake_frames -= 1
            shake_x = randint(-6, 6)
            shake_y = randint(-6, 6)
            dx = 0
            dy = 0
            if shake_frames == 0:
                ending_state = True
        else:
            dx = keys[K_d] - keys[K_a]
            dy = keys[K_s] - keys[K_w]
            if dx and dy:
                speed_dt *= 0.7071
            
        # 플레이어 좌표 업데이트 및 경계값 검사 (움직일 때만 계산 및 내장 함수 제거)
        if dx:
            player_x += dx * speed_dt
            if player_x < 0.0:
                player_x = 0.0
            elif player_x > bg_width_float:
                player_x = bg_width_float
        if dy:
            player_y += dy * speed_dt
            if player_y < 0.0:
                player_y = 0.0
            elif player_y > bg_height_float:
                player_y = bg_height_float
        
        # 플레이어와 노트 간의 접근(충돌) 체크 (Broadphase 적용하여 불필요한 곱셈 연산 방지)
        if collected_mask != 63:
            for note in notes:
                note_bit = note.bit
                if not (collected_mask & note_bit):
                    dx_note = player_x - note.x
                    if -40.0 < dx_note < 40.0:
                        dy_note = player_y - note.y
                        if -40.0 < dy_note < 40.0 and dx_note * dx_note + dy_note * dy_note < 1600.0:
                            collected_mask |= note_bit
                            ui_slots[note.idx] = note.img
                            bg_surface.fill((0, 0, 0), note.clear_rect)
                            
        # 음표를 모두 모은 상태에서 MMU와의 충돌(접근) 체크 -> 화면 흔들림(엔진 시동) 연출 진입
        elif collected_mask == 63 and not shake_triggered:
            dx_mmu = player_x - 1000.0
            if -80.0 < dx_mmu < 80.0:
                dy_mmu = player_y - 750.0
                if -80.0 < dy_mmu < 80.0 and dx_mmu * dx_mmu + dy_mmu * dy_mmu < 6400.0:
                    shake_frames = 90  # 1.5초 동안 화면 흔들림 연출
                    shake_triggered = True
        
        # 카메라 좌표 계산 (max/min 내장 함수를 제거하고 분기문으로 최적화)
        cam_x = player_x - 400.0
        if cam_x < 0.0:
            cam_x = 0.0
        elif cam_x > max_cam_x:
            cam_x = max_cam_x
            
        cam_y = player_y - 300.0
        if cam_y < 0.0:
            cam_y = 0.0
        elif cam_y > max_cam_y:
            cam_y = max_cam_y
            
        cam_x_int = int_cast(cam_x)
        cam_y_int = int_cast(cam_y)
        
        # 배경 렌더링
        screen_blit(bg_surface, (-cam_x_int + shake_x, -cam_y_int + shake_y))
        
        # 6개 노트를 모두 모은 경우 MMU 뒤에 엔진 화염(fire_img) 렌더링
        if collected_mask == 63:
            screen_blit(fire_img, (fire_const_x - cam_x_int + shake_x, fire_const_y - cam_y_int + shake_y))
                
        # MMU 렌더링
        screen_blit(mmu_img, (mmu_const_x - cam_x_int + shake_x, mmu_const_y - cam_y_int + shake_y))
        
        # 노트 렌더링 (모두 모았을 시 루프를 타지 않도록 감싸고, 오프셋 연산 최소화)
        if collected_mask != 63:
            for note in notes:
                if not (collected_mask & note.bit):
                    screen_blit(note.img, (note.render_x - cam_x_int + shake_x, note.render_y - cam_y_int + shake_y))
            
        screen_blit(player_img, (int_cast(player_x) - cam_x_int - player_half_w + shake_x, int_cast(player_y) - cam_y_int - player_half_h + shake_y))
        
        # UI 렌더링 (루프나 조건문 없이 최적화된 리스트 슬롯 직접 렌더링)
        screen_blit(ui_slots[0], (10, 10))
        screen_blit(ui_slots[1], (30, 10))
        screen_blit(ui_slots[2], (50, 10))
        screen_blit(ui_slots[3], (70, 10))
        screen_blit(ui_slots[4], (90, 10))
        screen_blit(ui_slots[5], (110, 10))
        
        display_flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()