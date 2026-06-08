import pygame
import sys
import random
import os

pygame.display.init()
pygame.events = pygame.event

# 상수
WIDTH, HEIGHT = 800, 600
FPS = 60
SPEED = 300
BG_MULT = 2.5 # 기존 5배에서 길이비로 2배 축소 (화면의 2.5배 크기)
BG_WIDTH = int(WIDTH * BG_MULT)
BG_HEIGHT = int(HEIGHT * BG_MULT)
PLAYER_SCALE = 4.0 # 플레이어 이미지 확대 배수

def create_background():
    """배경 표면을 미리 생성하여 반환 (최적화)"""
    bg = pygame.Surface((BG_WIDTH, BG_HEIGHT)).convert()
    bg.fill((0, 0, 0)) # 검정 배경
    
    star_size = 2 # 모두 같은 크기
    grid_size = 100 # 100x100 픽셀 격자
    stars_per_grid = 2 # 격자당 별의 개수
    
    # 격자 순회하며 별 배치
    for x in range(0, BG_WIDTH, grid_size):
        for y in range(0, BG_HEIGHT, grid_size):
            for _ in range(stars_per_grid):
                sx = x + random.randint(0, grid_size - star_size)
                sy = y + random.randint(0, grid_size - star_size)
                # 경계값 안전 체크
                if sx < BG_WIDTH and sy < BG_HEIGHT:
                    bg.fill((255, 255, 255), (sx, sy, star_size, star_size))
                    
    # 맵 정중앙에 MMU.png 그리기 (배경에 영구적으로 박아버려서 렌더링 최적화)
    mmu_path = "MMU.png"
    if os.path.exists(mmu_path):
        try:
            mmu_img = pygame.image.load(mmu_path).convert_alpha()
            # 픽셀 아트 본연의 딱딱 떨어지는(Nearest-Neighbor) 느낌을 살리기 위해
            # smoothscale이 아닌 일반 scale 함수 사용
            orig_w, orig_h = mmu_img.get_size()
            mmu_img = pygame.transform.scale(mmu_img, (int(orig_w * PLAYER_SCALE), int(orig_h * PLAYER_SCALE)))
            mmu_rect = mmu_img.get_rect(center=(BG_WIDTH // 2, BG_HEIGHT // 2))
            bg.blit(mmu_img, mmu_rect)
        except pygame.error:
            pass # 이미지 로드 실패 시 무시
    else:
        # MMU.png가 없을 경우 임시로 중앙에 파란색 사각형 폴백 표시
        mmu_fallback = pygame.Surface((200, 100), pygame.SRCALPHA)
        mmu_fallback.fill((0, 100, 255))
        mmu_rect = mmu_fallback.get_rect(center=(BG_WIDTH // 2, BG_HEIGHT // 2))
        bg.blit(mmu_fallback, mmu_rect)
                
    return bg

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("Fix The MMU")
    clock = pygame.time.Clock()
    
    # 배경 생성 (이 시점에 별과 중앙의 MMU.png가 모두 하나의 이미지로 합쳐짐)
    bg_surface = create_background()
    
    # 플레이어 이미지 로드 및 크기 확대
    image_path = "player.png"
    if os.path.exists(image_path):
        player_img = pygame.image.load(image_path).convert_alpha()
        orig_w, orig_h = player_img.get_size()
        player_img = pygame.transform.scale(player_img, (int(orig_w * PLAYER_SCALE), int(orig_h * PLAYER_SCALE)))
    else:
        player_img = pygame.Surface((120, 120), pygame.SRCALPHA)
        player_img.fill((255, 200, 0))
        
    img_rect = player_img.get_rect()
    
    # 플레이어의 월드 좌표를 랜덤하게 지정 (맵 내부)
    player_x = float(random.randint(0, BG_WIDTH))
    player_y = float(random.randint(0, BG_HEIGHT))
    
    # 파이썬 한정 캐싱 최적화
    event_get = pygame.event.get
    key_get_pressed = pygame.key.get_pressed
    K_w, K_s, K_a, K_d = pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d
    QUIT = pygame.QUIT
    screen_blit = screen.blit
    display_flip = pygame.display.flip
    tick = clock.tick
    
    # 카메라의 최대 범위 계산
    max_cam_x = BG_WIDTH - WIDTH
    max_cam_y = BG_HEIGHT - HEIGHT
    
    running = True
    while running:
        dt = tick(FPS) / 1000.0
        
        for event in event_get():
            if event.type == QUIT:
                running = False
                
        keys = key_get_pressed()
        dx = keys[K_d] - keys[K_a]
        dy = keys[K_s] - keys[K_w]
        
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071
            
        # 플레이어 좌표 업데이트
        player_x += dx * SPEED * dt
        player_y += dy * SPEED * dt
        
        # 플레이어가 맵 밖으로 나가지 못하게 제한
        player_x = max(0.0, min(player_x, float(BG_WIDTH)))
        player_y = max(0.0, min(player_y, float(BG_HEIGHT)))
        
        # 카메라 좌표 계산 (음수가 되지 않도록 제한)
        camera_x = max(0.0, min(player_x - WIDTH / 2, float(max_cam_x)))
        camera_y = max(0.0, min(player_y - HEIGHT / 2, float(max_cam_y)))
        
        # 배경과 플레이어 렌더링
        screen_blit(bg_surface, (-int(camera_x), -int(camera_y)))
        
        img_rect.center = (int(player_x - camera_x), int(player_y - camera_y))
        screen_blit(player_img, img_rect)
        
        display_flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
