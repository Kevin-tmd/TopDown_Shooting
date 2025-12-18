import pygame
import random
import math
import sys
import heapq

pygame.init()
WIDTH, HEIGHT = 1080, 800  # 기존 1080, 800 → 약간 더 작게
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("AppleGothic", 24)

# --- 유틸 함수 ---
def draw_text(surf, text, pos, color=(255,255,255)):
    surf.blit(FONT.render(text, True, color), pos)

def clamp(x, a, b):
    return max(a, min(x, b))

def rects_overlap(rect, others):
    return any(rect.colliderect(o.rect) for o in others)



# 플레이어 관련 정의
class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((24,24), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0,200,255), (12,12), 12)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0,0)
        self.speed = 4
        self.hp = 100
        self.max_hp = 100
        # 무기별 탄약 및 탄창
        self.gun_type = 1
        self.ammo1 = 30 # MP5  
        self.ammo2 = 25 # UMP45
        self.ammo3 = 50 # P90
        self.ammo4 = 5 # AWP
        self.ammo5 = 10 # Scout (SSG-08)
        self.ammo6 = 30 # AK-74
        self.ammo7 = 30 # G36
        self.ammo8 = 25 # FAMAS
        self.ammo9 = 20 # Mk14EBR
        self.ammo10 = 15 #QBU-88
        self.ammo11 = 100 # M249
        self.ammo12 = 100 # MG42
        self.ammo13 = 6 # Remington 870
        self.ammo14 = 8 # Saiga-12
        self.ammo15 = 6 # Webley MK VI
        self.max_ammo1 = 30
        self.max_ammo2 = 25
        self.max_ammo3 = 50
        self.max_ammo4 = 5
        self.max_ammo5 = 10
        self.max_ammo6 = 30
        self.max_ammo7 = 30
        self.max_ammo8 = 25
        self.max_ammo9 = 20
        self.max_ammo10 = 15
        self.max_ammo11 = 100
        self.max_ammo12 = 100
        self.max_ammo13 = 6
        self.max_ammo14 = 8
        self.max_ammo15 = 6
        self.mag1 = 3
        self.mag2 = 3
        self.mag3 = 2 
        self.mag4 = 2 
        self.mag5 = 2 
        self.mag6 = 3
        self.mag7 = 3 
        self.mag8 = 3
        self.mag9 = 2
        self.mag10 = 3
        self.mag11 = 1
        self.mag12 = 1
        self.mag13 = 2
        self.mag14 = 2
        self.mag15 = float('inf')  # infinite
        # 4번총은 탄창 제한 없음
        self.reload_time = 120  # SMG, 2초
        self.reload_cnt = 0
        self.dash_cool = 0
        self.gold = 0
        self.shoot_cool = 0  # 연사 쿨타임
        self.grenade = 2         # 수류탄 개수
        self.grenade_cool = 0    # 쿨타임(프레임)

    def update(self, walls):
        if self.gun_type == 1:
            self.speed = 3.95
        elif self.gun_type == 2:
            self.speed = 3.94
        elif self.gun_type == 3:
            self.speed = 3.93
        elif self.gun_type == 4:
            self.speed = 3.5
        elif self.gun_type == 5:
            self.speed = 3.75  
        elif self.gun_type == 6:
            self.speed = 3.88
        elif self.gun_type == 7:
            self.speed = 3.91
        elif self.gun_type == 8:
            self.speed = 3.89
        elif self.gun_type == 9:
            self.speed = 3.88
        elif self.gun_type == 10:
            self.speed = 3.86
        elif self.gun_type == 11:
            self.speed = 3.7
        elif self.gun_type == 12:
            self.speed = 3.67
        elif self.gun_type == 13:
            self.speed = 3.9
        elif self.gun_type == 14:
            self.speed = 3.88
        elif self.gun_type == 15:
            self.speed = 4.0

        keys = pygame.key.get_pressed()
        move = pygame.Vector2(0,0)
        if keys[pygame.K_w]: move.y -= 1
        if keys[pygame.K_s]: move.y += 1
        if keys[pygame.K_a]: move.x -= 1
        if keys[pygame.K_d]: move.x += 1
        if move.length(): move = move.normalize() * self.speed
        self.vel = move

        # 대쉬
        if keys[pygame.K_SPACE] and self.dash_cool == 0:
            if move.length():
                self.vel = move * 3
                self.dash_cool = 60

        # --- x축 이동 ---
        self.pos.x += self.vel.x
        self.rect.centerx = self.pos.x
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if self.vel.x > 0:
                    self.rect.right = wall.rect.left
                elif self.vel.x < 0:
                    self.rect.left = wall.rect.right
                self.pos.x = self.rect.centerx
                self.vel.x = 0  # x축 이동 막힘

        # --- y축 이동 ---
        self.pos.y += self.vel.y
        self.rect.centery = self.pos.y
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if self.vel.y > 0:
                    self.rect.bottom = wall.rect.top
                elif self.vel.y < 0:
                    self.rect.top = wall.rect.bottom
                self.pos.y = self.rect.centery
                self.vel.y = 0  # y축 이동 막힘

        # 화면 밖으로 못나가게
        self.pos.x = clamp(self.pos.x, 18, WIDTH-18)
        self.pos.y = clamp(self.pos.y, 18, HEIGHT-18)
        self.rect.center = self.pos

        if self.dash_cool > 0: self.dash_cool -= 1

        # 리로드 (무기별로 탄약/최대탄약/탄창 체크)
        if keys[pygame.K_r] and self.reload_cnt == 0 :
            if self.gun_type == 1 and self.ammo1 < self.max_ammo1 and self.mag1 > 0:
                self.reload_cnt = 60*1.8  
            elif self.gun_type == 2 and self.ammo2 < self.max_ammo2 and self.mag2 > 0:
                self.reload_cnt = 60*1.9  
            elif self.gun_type == 3 and self.ammo3 < self.max_ammo3 and self.mag3 > 0:
                self.reload_cnt = 60*2.1  
            elif self.gun_type == 4 and self.ammo4 < self.max_ammo4 and self.mag4 > 0:
                self.reload_cnt = 60*3.2 
            elif self.gun_type == 5 and self.ammo5 < self.max_ammo5 and self.mag5 > 0:
                self.reload_cnt = 60*3.0  
            elif self.gun_type == 6 and self.ammo6 < self.max_ammo6:
                self.reload_cnt = 60*2.4   
            elif self.gun_type == 7 and self.ammo7 < self.max_ammo7 and self.mag7 > 0:
                self.reload_cnt = 60*2.1
            elif self.gun_type == 8 and self.ammo8 < self.max_ammo8 and self.mag8 > 0:
                self.reload_cnt = 60*2.3
            elif self.gun_type == 9 and self.ammo9 < self.max_ammo9 and self.mag9 > 0:
                self.reload_cnt = 60*2.8
            elif self.gun_type == 10 and self.ammo10 < self.max_ammo10 and self.mag10 > 0:
                self.reload_cnt = 60*2.9
            elif self.gun_type == 11 and self.ammo11 < self.max_ammo11 and self.mag11 > 0:
                self.reload_cnt = 60*5.5
            elif self.gun_type == 12 and self.ammo12 < self.max_ammo12 and self.mag12 > 0:
                self.reload_cnt = 60*5.8
            elif self.gun_type == 13 and self.ammo13 < self.max_ammo13 and self.mag13 > 0:
                self.reload_cnt = 60*3.2
            elif self.gun_type == 14 and self.ammo14 < self.max_ammo14 and self.mag14 > 0:
                self.reload_cnt = 60*3.0
            elif self.gun_type == 15 and self.ammo15 < self.max_ammo15:
                self.reload_cnt = 60*2.0 
        if self.reload_cnt > 0:
            self.reload_cnt -= 1
            if self.reload_cnt <= 0:
                if self.gun_type == 1 and self.mag1 > 0:
                    self.ammo1 = self.max_ammo1
                    self.mag1 -= 1
                elif self.gun_type == 2 and self.mag2 > 0:
                    self.ammo2 = self.max_ammo2
                    self.mag2 -= 1
                elif self.gun_type == 3 and self.mag3 > 0:
                    self.ammo3 = self.max_ammo3
                    self.mag3 -= 1
                elif self.gun_type == 4 and self.mag4 > 0:
                    self.ammo4 = self.max_ammo4
                    self.mag4 -= 1
                elif self.gun_type == 5 and self.mag5 > 0:
                    self.ammo5 = self.max_ammo5
                    self.mag5 -= 1
                elif self.gun_type == 6 and self.mag6 > 0:
                    self.ammo6 = self.max_ammo6
                    self.mag6 -= 1
                elif self.gun_type == 7 and self.mag7 > 0:
                    self.ammo7 = self.max_ammo7
                    self.mag7 -= 1
                elif self.gun_type == 8 and self.mag8 > 0:
                    self.ammo8 = self.max_ammo8
                    self.mag8 -= 1
                elif self.gun_type == 9 and self.mag9 > 0:
                    self.ammo9 = self.max_ammo9
                    self.mag9 -= 1
                elif self.gun_type == 10 and self.mag10 > 0:
                    self.ammo10 = self.max_ammo10
                    self.mag10 -= 1
                elif self.gun_type == 11 and self.mag11 > 0:
                    self.ammo11 = self.max_ammo11
                    self.mag11 -= 1
                elif self.gun_type == 12 and self.mag12 > 0:
                    self.ammo12 = self.max_ammo12
                    self.mag12 -= 1
                elif self.gun_type == 13 and self.mag13 > 0:
                    self.ammo13 = self.max_ammo13
                    self.mag13 -= 1
                elif self.gun_type == 14 and self.mag14 > 0:
                    self.ammo14 = self.max_ammo14
                    self.mag14 -= 1
                elif self.gun_type == 15:
                    self.ammo15 = self.max_ammo15

        # 연사 쿨타임 감소
        if self.shoot_cool > 0:
            self.shoot_cool -= 1

    def try_auto_shoot(self, mouse_pos, bullets, walls):
        if self.gun_type == 1:  
            if self.ammo1 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(1.2)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                smg_range = int((WIDTH**2 + HEIGHT**2)**0.5 * 2/3)
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 22, 85, 450))
                self.ammo1 -= 1
                self.shoot_cool = 5
        elif self.gun_type == 2:  
            if self.ammo2 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(1.1)
                angle += random.uniform(-spread, spread)
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 26, 78, 450))
                self.ammo2 -= 1
                self.shoot_cool = 6  
        elif self.gun_type == 3:  
            if self.ammo3 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(1.4)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 20, 90, 450))
                self.shoot_cool = 4
        elif self.gun_type == 4: 
            if self.ammo4 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(0.075)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 250, 140, 1200))
                self.ammo4 -= 1
                self.shoot_cool = 90
        elif self.gun_type == 5:  
            if self.ammo5 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(0.05)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                lmg_range = int((WIDTH**2 + HEIGHT**2)**0.5 * 2/3)
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 205, 105, 1050))
                self.ammo5 -= 1
                self.shoot_cool = 51
        elif self.gun_type == 6:  # AK-47 (조준선X, 관통X, 빨간 투명선X, 근거리)
            if self.ammo6 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(0.9)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 36, 95, 650))
                self.ammo6 -= 1
                self.shoot_cool = 6
        elif self.gun_type == 7:  # G36 (조준선, 관통X, 빨간 투명선, 중거리)
            if self.ammo7 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(1.1)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 30, 100, 650))  
                self.ammo7 -= 1
                self.shoot_cool = 5
        elif self.gun_type == 8:  # FAMAS (조준선, 관통X, 빨간 투명선, 중거리)
            if self.ammo8 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(1.0)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 28, 102, 650)) 
                self.ammo8 -= 1
                self.shoot_cool = 4
        elif self.gun_type == 9:  # Mk14 EBR (조준선, 관통O, 빨간 투명선, 장거리)
            if self.ammo9 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(0.2)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 70, 125, 1000))  
                self.ammo9 -= 1
                self.shoot_cool = 10
        elif self.gun_type == 10:  # QBU-88 (조준선, 관통O, 빨간 투명선, 장거리)
            if self.ammo10 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(0.2)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 60, 90, 950))  
                self.ammo10 -= 1
                self.shoot_cool = 11
        elif self.gun_type == 11:  # M249 (조준선, 관통X, 빨간 투명선, 중거리)
            if self.ammo11 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(2.5)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 30, 90, 700))
                self.ammo11 -= 1
                self.shoot_cool = 5
        elif self.gun_type == 12:  # MG42 (조준선, 관통X, 빨간 투명선, 중거리)
            if self.ammo12 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(2.5)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 28, 92, 700))  # 사거리 2.2배로
                self.ammo12 -= 1
                self.shoot_cool = 3
        elif self.gun_type == 13:  # Remington 870 (조준선X, 관통X, 빨간 투명선X, 근거리)
            if self.ammo13 > 0 and self.shoot_cool == 0:
                base_dir = pygame.Vector2(mouse_pos) - self.pos
                if base_dir.length(): base_dir = base_dir.normalize()
                angle0 = math.atan2(base_dir.y, base_dir.x)
                spread = math.radians(15)
                for i in range(10):
                    angle = angle0 - spread/2 + spread*i/6 + random.uniform(-math.radians(5), math.radians(5))
                    dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                    bullets.add(PlayerBullet(self.pos, dir, walls, "player", 45, 50, 180))
                self.ammo13 -= 1
                self.shoot_cool = 51
        elif self.gun_type == 14:  # Saiga-12 (조준선X, 관통X, 빨간 투명선X, 근거리)
            if self.ammo14 > 0 and self.shoot_cool == 0:
                base_dir = pygame.Vector2(mouse_pos) - self.pos
                if base_dir.length(): base_dir = base_dir.normalize()
                angle0 = math.atan2(base_dir.y, base_dir.x)
                spread = math.radians(30)
                for i in range(6):
                    angle = angle0 - spread/2 + spread*i/8 + random.uniform(-math.radians(4), math.radians(4))
                    dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                    bullets.add(PlayerBullet(self.pos, dir, walls, "player", 40, 50, 180))
                self.ammo14 -= 1
                self.shoot_cool = 20
        elif self.gun_type == 15:  # Webley MK VI (조준선, 관통X, 빨간 투명선, 중거리)
            if self.ammo15 > 0 and self.shoot_cool == 0:
                dir = pygame.Vector2(mouse_pos) - self.pos
                if dir.length(): dir = dir.normalize()
                angle = math.atan2(dir.y, dir.x)
                spread = math.radians(0.1)
                angle += random.uniform(-spread, spread)
                dir = pygame.Vector2(math.cos(angle), math.sin(angle))
                bullets.add(PlayerBullet(self.pos, dir, walls, "player", 58, 40, 350))
                self.ammo15 -= 1
                self.shoot_cool = 12

class PlayerBullet(pygame.sprite.Sprite):
    def __init__(self, pos, dir, walls, owner, damage, speed, max_dist):
        super().__init__()
        self.image = pygame.Surface((6,6), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255,255,0), (3,3), 3)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.dir = dir
        self.speed = speed/3
        self.owner = owner
        self.walls = walls
        self.damage = damage
        self.max_dist = max_dist
        self.travel = 0

    def update(self):
        move = self.dir * self.speed
        self.pos += move
        self.travel += move.length()
        self.rect.center = self.pos
        for wall in self.walls:
            if self.rect.colliderect(wall.rect):
                self.kill()
        if self.travel > self.max_dist:
            self.kill()






#적의 총알 관련
class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, dir, walls, owner):
        super().__init__()
        self.image = pygame.Surface((6,6), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255,255,0), (3,3), 3)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.dir = dir
        self.speed = 8 if owner == "player" else 10
        self.owner = owner
        self.walls = walls
        # 빨간/보라 적 총알 사거리: 화면 길이의 0.6
        self.max_dist = 370 if owner == "enemy" else 9999
        self.travel = 0
        self.damage = 15 if owner == "enemy" else 0  # 대미지 속성 추가

    def update(self):
        move = self.dir * self.speed
        self.pos += move
        self.travel += move.length()
        self.rect.center = self.pos
        for wall in self.walls:
            if self.rect.colliderect(wall.rect):
                self.kill()
        if self.travel > self.max_dist:
            self.kill()

# --- 핑크색 적의 총알 ---
class PinkBullet(pygame.sprite.Sprite):
    def __init__(self, pos, dir, walls, owner):
        super().__init__()
        self.image = pygame.Surface((10,10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 120, 200), (4,4), 10)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.dir = dir
        self.speed = 8
        self.owner = owner
        self.walls = walls
        self.damage = 34  # 대미지 속성 추가

    def update(self):
        self.pos += self.dir * self.speed
        self.rect.center = self.pos
        for wall in self.walls:
            if self.rect.colliderect(wall.rect):
                self.kill()

# --- GreenBullet(초록 적 총알) ---
class GreenBullet(pygame.sprite.Sprite):
    def __init__(self, pos, dir, walls, owner):
        super().__init__()
        self.image = pygame.Surface((4,4), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (80,255,80), (2,2), 2)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.dir = dir
        self.speed = 15
        self.owner = owner
        self.walls = walls
        self.max_dist = 500
        self.travel = 0
        self.damage = 8 # 대미지 속성 추가

    def update(self):
        move = self.dir * self.speed
        self.pos += move
        self.travel += move.length()
        self.rect.center = self.pos
        for wall in self.walls:
            if self.rect.colliderect(wall.rect):
                self.kill()
        if self.travel > self.max_dist:
            self.kill()

# --- LimeBullet(연두 적 총알) ---
class LimeBullet(pygame.sprite.Sprite):
    def __init__(self, pos, dir, walls, owner):
        super().__init__()
        self.image = pygame.Surface((8,8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (180,255,80), (4,4), 4)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.dir = dir
        self.speed = 18
        self.owner = owner
        self.walls = walls
        self.max_dist = 1000
        self.travel = 0
        self.damage = 49  # 대미지 속성 추가

    def update(self):
        move = self.dir * self.speed
        self.pos += move
        self.travel += move.length()
        self.rect.center = self.pos
        for wall in self.walls:
            if self.rect.colliderect(wall.rect):
                self.kill()
        if self.travel > self.max_dist:
            self.kill()

# --- 회색 구체 ---
class GrayOrb(pygame.sprite.Sprite):
    def __init__(self, pos, dir, walls, player):
        super().__init__()
        self.image = pygame.Surface((18,18), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (160,160,160), (9,9), 9)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.dir = dir
        self.speed = 5
        self.walls = walls
        self.player = player
        self.travel = 0
        self.max_dist = 130
        self.damage = 5
        self.exploded = False
        self.explode_timer = 180  # 3초(60fps 기준)

    def update(self, explosions_group):
        if self.exploded:
            # 1초 대기 후 폭발 생성
            self.explode_timer -= 3
            if self.explode_timer <= 0:
                if explosions_group is not None:
                    explosions_group.add(OrangeExplosion(self.pos))
                self.kill()
            return
        move = self.dir * self.speed
        self.pos += move
        self.travel += move.length()
        self.rect.center = self.pos
        hit_wall = any(self.rect.colliderect(w.rect) for w in self.walls)
        hit_player = self.rect.colliderect(self.player.rect)
        if self.travel > self.max_dist or hit_wall or hit_player:
            if explosions_group is not None:
                explosions_group.add(OrangeExplosion(self.pos))
            self.exploded = True

# --- 주황색 폭발 ---
class OrangeExplosion(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.radius = 15  # 30x30
        self.max_radius = 90 # 150x150
        self.image = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
        self.alpha = 200
        self.color = (255, 140, 0)
        self.rect = self.image.get_rect(center=pos)
        self.timer = 0
        self.duration = 48  # 0.8초(60fps 기준)
        self.pos = pygame.Vector2(pos)
        self.damage = 60
        self.done = False
        self.damage_delay = 180  # 3초(60fps 기준) 후부터 대미지 적용

    def update(self, player):
        self.timer += 1
        progress = self.timer / self.duration
        radius = int(self.radius + (self.max_radius - self.radius) * progress)
        alpha = int(self.alpha * (1 - progress))
        self.image.fill((0,0,0,0))
        pygame.draw.circle(self.image, self.color + (alpha,), (self.max_radius, self.max_radius), radius)
        self.rect = self.image.get_rect(center=self.pos)
        # 3초가 지난 후에만 대미지 적용
        if not self.done and self.timer >= self.damage_delay and self.rect.colliderect(player.rect):
            player.hp -= self.damage
            self.done = True
        if self.timer >= self.duration:
            self.kill()



# Chasing algorithm
# --- Check player sight and enemy sight ---
def has_line_of_sight(start, end, walls):
       # start, end: Vector2
    for wall in walls:
        if wall.rect.clipline(start, end):
            return False
    return True

# --- Find path (A* Algorithm) ---
def find_path(start, goal, walls, grid_size=24):
    # convert pygame vector2 to grid coordinates
    # each grid cell becomes a node
    def pos_to_grid(pos):
        return (int(pos.x // grid_size), int(pos.y // grid_size))
    
    def grid_to_pos(grid):
        return pygame.Vector2(grid[0]*grid_size+grid_size//2, grid[1]*grid_size+grid_size//2)
    wall_rects = [w.rect for w in walls]
    start_grid = pos_to_grid(start)
    goal_grid = pos_to_grid(goal)

    # open_set = candadate nodes to explore that has not been explored yet
    # heapq => prioritise nodes that has least f_score
    # g_score => actual cost from start to current node
    # f_score => estimated cost from start to goal through current node
    open_set = []
    heapq.heappush(open_set, (0, start_grid))
    came_from = {}
    g_score = {start_grid: 0}
    # --- random probability of inefficient path
    # to make enemy movements look more natural 
    # (extra for game purpose) ---
    if random.random() < 0.45:  # 45% of making inefficient path

        def heuristic(a, b):
            return random.randint(0, 4)  # random heuristic
    else:
        def heuristic(a, b):
            return abs(a[0]-b[0]) + abs(a[1]-b[1])
    f_score = {start_grid: heuristic(start_grid, goal_grid)}
    directions = [(-1,0),(1,0),(0,-1),(0,1)]
    explored = 0
    MAX_EXPLORE = 2000  # maximum nodes to explore
    # in this code, every horizontal or vertical movement of 1 unit costs 1
    while open_set:
        explored += 1
        # limit maximum exploration to avoid infinite loop 
        # (not in A* theory but used for practical game purpose)
        if explored > MAX_EXPLORE:
            return []
        _, current = heapq.heappop(open_set)
        if current == goal_grid:
            path = []
            # when arrive, backtrack to get the path
            while current in came_from:
                path.append(grid_to_pos(current))
                current = came_from[current]
            path.reverse()
            return path
        for dx,dy in directions:
            neighbor = (current[0]+dx, current[1]+dy)
            neighbor_rect = pygame.Rect(neighbor[0]*grid_size, neighbor[1]*grid_size, grid_size, grid_size)
            # skip if it collides with wall (extra code for the game purpose)
            if any(neighbor_rect.colliderect(w) for w in wall_rects):
                continue
            tentative_g = g_score[current] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                # start exploring nodes with smaller f_score first
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal_grid)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []

# --- Wall 클래스 ---
class Wall(pygame.sprite.Sprite):
    def __init__(self, rect):
        super().__init__()
        self.image = pygame.Surface((rect[2], rect[3]))
        self.image.fill((80,80,80))
        self.rect = self.image.get_rect(topleft=(rect[0], rect[1]))

def make_L_wall(x, y, w, h, thickness=20):
    # 'ㄱ' 모양: 세로+가로
    return [
        Wall((x, y, thickness, h)),
        Wall((x, y+h-thickness, w, thickness))
    ]

def make_U_wall(x, y, w, h, thickness=20):
    # 'ㄷ' 모양: 세로+가로+세로
    return [
        Wall((x, y, thickness, h)),
        Wall((x+w-thickness, y, thickness, h)),
        Wall((x, y+h-thickness, w, thickness))
    ]

def make_walls():
    global stage
    walls = []
    tries = 0
    # 벽 개수와 크기를 화면 크기에 맞게 조정
    # 기존 4~6 → 3~5로 감소
    min_wall = int(min(WIDTH, HEIGHT) * 0.07)   # 최소 벽 크기(비율 유지)
    max_wall = int(min(WIDTH, HEIGHT) * 0.16)   # 최대 벽 크기(비율 유지)

    player_rect = pygame.Rect(WIDTH//2-36, HEIGHT-80-36, 72, 72)
    enemy_rects = [
        pygame.Rect(WIDTH//2-16, 100-16, 32, 32),
        pygame.Rect(WIDTH//2+160-16, 100-16, 32, 32),
        pygame.Rect(WIDTH//2-160-16, 100-16, 32, 32)
    ]
    avoid_rects = [player_rect] + enemy_rects

    randomvariable=random.randint(0, 100)
    if randomvariable < 20:
        num_walls_rect = random.randint(4, 4)
        num_L = random.randint(0, 0)
        num_U = random.randint(0, 0)
    elif randomvariable < 40:
        num_walls_rect = random.randint(1, 2)
        num_L = random.randint(8, 12)
        num_U = random.randint(0, 0)
    elif randomvariable < 60:
        num_walls_rect = random.randint(0, 8)
        num_L = random.randint(1, 2)
        num_U = random.randint(4, 6)
    elif randomvariable < 80:
        num_walls_rect = random.randint(1, 2)
        num_L = random.randint(1, 3)
        num_U = random.randint(8, 12)
    else:
        num_walls_rect = random.randint(0, 2)
        num_L = random.randint(4, 8)
        num_U = random.randint(3, 6)

    # 랜덤 직사각형 벽
    for _ in range(num_walls_rect):
        for _ in range(100):
            w = random.randint(min_wall, max_wall)
            h = random.randint(min_wall, max_wall)
            x = random.randint(40, WIDTH-w-40)
            y = random.randint(40, HEIGHT-h-40)
            rect = pygame.Rect(x, y, w, h)
            if not rects_overlap(rect, walls) and not any(rect.colliderect(a) for a in avoid_rects):
                wall = Wall((x, y, w, h))
                walls.append(wall)
                break

    # 'ㄱ' 벽
    
    for _ in range(num_L):
        for _ in range(100):
            w = random.randint(int(min_wall*1.1), int(max_wall*1.1))
            h = random.randint(int(min_wall*1.1), int(max_wall*1.1))
            x = random.randint(40, WIDTH-w-40)
            y = random.randint(40, HEIGHT-h-40)
            l_walls = make_L_wall(x, y, w, h)
            if (
                not any(rects_overlap(wall.rect, walls) for wall in l_walls)
                and not any(any(wall.rect.colliderect(a) for a in avoid_rects) for wall in l_walls)
            ):
                walls.extend(l_walls)
                break

    # 'ㄷ' 벽
    
    for _ in range(num_U):
        for _ in range(100):
            w = random.randint(int(min_wall*1.3), int(max_wall*1.3))
            h = random.randint(int(min_wall*1.3), int(max_wall*1.3))
            x = random.randint(40, WIDTH-w-40)
            y = random.randint(40, HEIGHT-h-40)
            u_walls = make_U_wall(x, y, w, h)
            if (
                not any(rects_overlap(wall.rect, walls) for wall in u_walls)
                and not any(any(wall.rect.colliderect(a) for a in avoid_rects) for wall in u_walls)
            ):
                walls.extend(u_walls)
                break

    return pygame.sprite.Group(walls)








#적 스폰
def make_enemies(walls, stage, player=None):
    enemies = pygame.sprite.Group()
    # (빨간, 보라, 핑크, 초록, 연두, 연보라, 갈색)
    stage_table = [
        (1, 0, 0, 0, 0, 0, 0),   # 1
        (2, 0, 0, 0, 0, 0, 0),   # 2
        (3, 0, 0, 0, 0, 0, 0),   # 3
        (5, 0, 0, 0, 0, 0, 0),   # 4
        (0, 1, 0, 0, 0, 0, 0),   # 5
        (2, 1, 0, 0, 0, 0, 0),   # 6
        (3, 1, 0, 0, 0, 0, 0),   # 7
        (0, 2, 0, 0, 0, 0, 0),   # 8
        (2, 2, 0, 0, 0, 0, 0),   # 9
        (0, 0, 1, 0, 0, 0, 0),   # 10
        (0, 3, 0, 0, 0, 0, 0),   # 11
        (2, 0, 1, 0, 0, 0, 0),   # 12
        (0, 0, 2, 0, 0, 0, 0),   # 13
        (0, 2, 2, 0, 0, 0, 0),   # 14
        (0, 0, 0, 1, 0, 0, 0),   # 15
        (3, 0, 3, 0, 0, 0, 0),   # 16
        (0, 2, 0, 1, 0, 0, 0),   # 17
        (0, 5, 0, 0, 0, 0, 0),   # 18
        (1, 1, 1, 1, 0, 0, 0),   # 19
        (0, 0, 0, 0, 1, 0, 0),   # 20
        (0, 0, 0, 2, 0, 0, 0),   # 21
        (2, 0, 0, 0, 1, 0, 0),   # 22
        (0, 2, 0, 0, 1, 0, 0),   # 23
        (2, 0, 0, 3, 0, 0, 0),   # 24
        (0, 0, 0, 0, 3, 0, 0),   # 25
        (1, 1, 1, 1, 1, 0, 0),   # 26
        (0, 2, 0, 3, 0, 0, 0),   # 27
        (0, 0, 5, 0, 0, 0, 0),   # 28
        (0, 0, 0, 5, 0, 0, 0),   # 29
        (10, 0, 0, 0, 0, 0, 0),   # 30
        (0, 0, 0, 0, 5, 0, 0),   # 31
        (3, 2, 0, 0, 2, 0, 0),  # 32
        (2, 2, 2, 2, 0, 0, 0),   # 33
        (0, 0, 4, 0, 4, 0, 0),   # 34
        (0, 0, 0, 0, 0, 1, 0),   # 35
        (5, 2, 0, 0, 0, 2, 0),   # 36
        (0, 5, 0, 0, 0, 2, 0),  # 37
        (0, 0, 5, 0, 0, 2, 0),   # 38
        (0, 0, 0, 0, 6, 2, 0),   # 39
        (0, 0, 0, 0, 0, 0, 1),   # 40
        # 41~50: 연보라 적 1마리씩
        (0, 0, 0, 5, 0, 2, 0),   # 41
        (15, 0, 0, 0, 0, 0, 2),   # 42
        (0, 15, 0, 0, 0, 0, 2),   # 43
        (5, 5, 5, 0, 0, 2, 0),   # 44
        (0, 0, 0, 5, 5, 2, 2),   # 45
        (0, 10, 0, 0, 0, 3, 0),   # 46
        (0, 0, 10, 0, 0, 4, 4),   # 47
        (0, 0, 0, 15, 0, 2, 0),   # 48
        (0, 0, 0, 0, 0, 5, 10),   # 49
        (3, 2, 5, 5, 3, 3, 5),   # 50
    ]
    if stage < len(stage_table):
        red_count, purple_count, pink_count, green_count, lime_count, lavender_count, brown_count = stage_table[stage]
    else:
        red_count, purple_count, pink_count, green_count, lime_count, lavender_count, brown_count = 0,0,0,0,0,0,0

    used_rects = []
    SPAWN_TOP = 30
    SPAWN_BOTTOM = HEIGHT // 2 - 80

    # 빨간 적
    for _ in range(red_count):
        for _ in range(100):
            x = random.randint(30, WIDTH-30)
            y = random.randint(SPAWN_TOP, SPAWN_BOTTOM)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in walls) and not any(rect.colliderect(r) for r in used_rects):
                enemies.add(Enemy((x, y), walls))
                used_rects.append(rect)
                break
    # 보라 적
    for _ in range(purple_count):
        for _ in range(100):
            x = random.randint(30, WIDTH-30)
            y = random.randint(SPAWN_TOP, SPAWN_BOTTOM)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in walls) and not any(rect.colliderect(r) for r in used_rects):
                if player is None:
                    class Dummy: max_hp = 100
                    enemies.add(PurpleEnemy((x, y), walls, Dummy()))
                else:
                    enemies.add(PurpleEnemy((x, y), walls, player))
                used_rects.append(rect)
                break
    # 핑크 적
    for _ in range(pink_count):
        for _ in range(100):
            x = random.randint(30, WIDTH-30)
            y = random.randint(SPAWN_TOP, SPAWN_BOTTOM)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in walls) and not any(rect.colliderect(r) for r in used_rects):
                enemies.add(PinkEnemy((x, y), walls))
                used_rects.append(rect)
                break
    # 초록 적
    for _ in range(green_count):
        for _ in range(100):
            x = random.randint(30, WIDTH-30)
            y = random.randint(SPAWN_TOP, SPAWN_BOTTOM)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in walls) and not any(rect.colliderect(r) for r in used_rects):
                if player is None:
                    class Dummy: max_hp = 100
                    enemies.add(GreenEnemy((x, y), walls, Dummy()))
                else:
                    enemies.add(GreenEnemy((x, y), walls, player))
                used_rects.append(rect)
                break
    # 연두 적
    for _ in range(lime_count):
        for _ in range(100):
            x = random.randint(30, WIDTH-30)
            y = random.randint(SPAWN_TOP, SPAWN_BOTTOM)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in walls) and not any(rect.colliderect(r) for r in used_rects):
                if player is None:
                    class Dummy: pass
                    enemies.add(LimeEnemy((x, y), walls, Dummy()))
                else:
                    enemies.add(LimeEnemy((x, y), walls, player))
                used_rects.append(rect)
                break
    # 연보라 적
    for _ in range(lavender_count):
        for _ in range(100):
            x = random.randint(30, WIDTH-30)
            y = random.randint(SPAWN_TOP, SPAWN_BOTTOM)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in walls) and not any(rect.colliderect(r) for r in used_rects):
                if player is None:
                    class Dummy: pass
                    enemies.add(LavenderEnemy((x, y), walls, Dummy()))
                else:
                    enemies.add(LavenderEnemy((x, y), walls, player))
                used_rects.append(rect)
                break
    # 갈색 적
    for _ in range(brown_count):
        for _ in range(100):
            x = random.randint(30, WIDTH-30)
            y = random.randint(SPAWN_TOP, SPAWN_BOTTOM)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in walls) and not any(rect.colliderect(r) for r in used_rects):
                enemies.add(BrownEnemy((x, y), walls, player))
                used_rects.append(rect)
                break
    return enemies








#적 클래스 정의
# --- 보라색 적 클래스 ---
class PurpleEnemy(pygame.sprite.Sprite):
    def __init__(self, pos, walls, player):
        super().__init__()
        self.image = pygame.Surface((20,20), pygame.SRCALPHA)  # 기존 32x32 → 20x20
        pygame.draw.circle(self.image, (180, 80, 255), (10,10), 10)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.hp = 180
        self.max_hp = 180
        self.speed = 2.5
        self.walls = walls
        self.cool = 0
        self.aim_time = 0
        self.target_dir = pygame.Vector2(0,0)
        self.detect_range = 600  # 기존 2000 → 1500
        self.shoot_range = 400
        self.stop_range = 70
        self.avoid_range = 70
        self.path = []
        self.path_timer = 0
        self.chasing = False
        self.roam_target = None
        self.roam_path = []
        self.roam_path_timer = 0

    def update(self, player, bullets, enemies):
        dist = self.pos.distance_to(player.pos)
        # 인식범위 내에서만 추적
        if dist < self.detect_range:
            self.chasing = True
        elif dist > self.detect_range + 40:
            self.chasing = False

        move = pygame.Vector2(0,0)
        move_mode = "normal"
        if self.chasing:
            self.roam_target = None  # 추격 시작 시 랜덤 목표 해제
            can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
            if dist < self.avoid_range:
                move_mode = "avoid"
            elif dist < self.stop_range and can_shoot:
                move_mode = "stop"
            else:
                move_mode = "normal"

            # 경로 재탐색(더 자주)
            self.path_timer -= 1
            if self.path_timer <= 0 or not self.path:
                can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
                target_pos = player.pos
                if not can_shoot:
                    # 시야가 트이는 위치를 찾음
                    # 플레이어 주변 8방향 40~120픽셀 거리에서 시야가 트이는 곳을 랜덤으로 시도
                    found = False
                    for r in range(0, 300, 2):
                        for angle in range(0, 360, 5):
                            offset = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * r
                            test_pos = player.pos + offset
                            if has_line_of_sight(test_pos, player.pos, self.walls):
                                target_pos = test_pos
                                found = True
                                break
                        if found:
                            break
                self.path = find_path(self.pos, target_pos, self.walls)
                self.path_timer = 15

            if move_mode == "normal":
                if self.path:
                    next_pos = self.path[0]
                    dir = next_pos - self.pos
                    if dir.length() < self.speed:
                        self.pos = next_pos
                        self.path.pop(0)
                    else:
                        move = dir.normalize() * self.speed
                else:
                    dir = player.pos - self.pos
                    if dir.length(): move = dir.normalize() * self.speed
            elif move_mode == "avoid":
                dir = self.pos - player.pos
                if dir.length(): dir = dir.normalize() * self.speed
                test_rect = self.rect.move(dir.x, dir.y)
                blocked = any(test_rect.colliderect(w.rect) for w in self.walls)
                if blocked:
                    perp = pygame.Vector2(-dir.y, dir.x)
                    test_rect1 = self.rect.move(perp.x, perp.y)
                    test_rect2 = self.rect.move(-perp.x, -perp.y)
                    if not any(test_rect1.colliderect(w.rect) for w in self.walls):
                        dir = perp
                    elif not any(test_rect2.colliderect(w.rect) for w in self.walls):
                        dir = -perp
                    else:
                        dir = pygame.Vector2(0,0)
                move = dir
            else:
                move = pygame.Vector2(0,0)

            # ...existing code...
            # 유닛 밀어내기
            for e in enemies:
                if e != self and self.rect.colliderect(e.rect):
                    away = self.pos - e.pos
                    if away.length(): away = away.normalize()
                    self.pos += away

            # --- x축 이동 ---
            self.pos.x += move.x
            self.rect.centerx = self.pos.x
            for wall in self.walls:
                if self.rect.colliderect(wall.rect):
                    if move.x > 0:
                        self.rect.right = wall.rect.left
                    elif move.x < 0:
                        self.rect.left = wall.rect.right
                    self.pos.x = self.rect.centerx

            # --- y축 이동 ---
            self.pos.y += move.y
            self.rect.centery = self.pos.y
            for wall in self.walls:
                if self.rect.colliderect(wall.rect):
                    if move.y > 0:
                        self.rect.bottom = wall.rect.top
                    elif move.y < 0:
                        self.rect.top = wall.rect.bottom
                    self.pos.y = self.rect.centery

            # 화면 밖 보정
            self.pos.x = clamp(self.pos.x, 10, WIDTH-10)
            self.pos.y = clamp(self.pos.y, 10, HEIGHT-10)
            self.rect.center = self.pos
            # ...existing code...

        # 총알 발사 조건: 사거리 내, 벽 없음
        if dist < self.shoot_range and has_line_of_sight(self.pos, player.pos, self.walls):
            if self.aim_time > 50-20 and self.aim_time < 50-10:
                self.target_dir = (player.pos - self.pos).normalize() if (player.pos - self.pos).length() else pygame.Vector2(1,0)
            self.aim_time += 1
            #쌍권총
            if (self.aim_time >= 50 and self.aim_time <55) or (self.aim_time >= 63):  # 더 빠른 조준
                bullets.add(Bullet(self.pos, self.target_dir, self.walls, "enemy"))
                if self.aim_time < 55:
                    self.aim_time = 55
                else:
                    self.aim_time = 0
        else:
            self.aim_time = 0

# --- 연두색 적 클래스 (장거리 저격, 아주 빠른 총알, 별도 LimeSniperBullet 사용) ---
class LimeEnemy(pygame.sprite.Sprite):
    def __init__(self, pos, walls, player):
        super().__init__()
        self.image = pygame.Surface((20,20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (180, 255, 80), (10,10), 10)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.hp = 140
        self.max_hp = 140
        self.speed = 0.7
        self.walls = walls
        self.cool = 0
        self.aim_time = 0
        self.target_dir = pygame.Vector2(0,0)
        self.detect_range = 1300  # 1300 + 300
        self.shoot_range = 1000   # 900 + 100
        self.stop_range = 800
        self.avoid_range = 300
        self.path = []
        self.path_timer = 0
        self.chasing = False
        self.roam_target = None
        self.roam_path = []
        self.roam_path_timer = 0

    def update(self, player, bullets, enemies):
        dist = self.pos.distance_to(player.pos)
        # 인식범위 내에서만 추적
        if dist < self.detect_range:
            self.chasing = True
        elif dist > self.detect_range + 40:
            self.chasing = False

        move = pygame.Vector2(0,0)
        move_mode = "normal"
        if self.chasing:
            self.roam_target = None  # 추격 시작 시 랜덤 목표 해제
            can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
            if dist < self.avoid_range:
                move_mode = "avoid"
            elif dist < self.stop_range and can_shoot:
                move_mode = "stop"
            else:
                move_mode = "normal"

            self.path_timer -= 1
            if self.path_timer <= 0 or not self.path:
                can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
                target_pos = player.pos
                if not can_shoot:
                    # 시야가 트이는 위치를 찾음
                    # 플레이어 주변 8방향 40~120픽셀 거리에서 시야가 트이는 곳을 랜덤으로 시도
                    found = False
                    for r in range(0, 300, 2):
                        for angle in range(0, 360, 15):
                            offset = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * r
                            test_pos = player.pos + offset
                            if has_line_of_sight(test_pos, player.pos, self.walls):
                                target_pos = test_pos
                                found = True
                                break
                        if found:
                            break
                self.path = find_path(self.pos, target_pos, self.walls)
                self.path_timer = 5

            if move_mode == "normal":
                if self.path:
                    next_pos = self.path[0]
                    dir = next_pos - self.pos
                    if dir.length() < self.speed:
                        self.pos = next_pos
                        self.path.pop(0)
                    else:
                        move = dir.normalize() * self.speed
                else:
                    dir = player.pos - self.pos
                    if dir.length(): move = dir.normalize() * self.speed
            elif move_mode == "avoid":
                dir = self.pos - player.pos
                if dir.length(): dir = dir.normalize() * self.speed
                test_rect = self.rect.move(dir.x, dir.y)
                blocked = any(test_rect.colliderect(w.rect) for w in self.walls)
                if blocked:
                    perp = pygame.Vector2(-dir.y, dir.x)
                    test_rect1 = self.rect.move(perp.x, perp.y)
                    test_rect2 = self.rect.move(-perp.x, -perp.y)
                    if not any(test_rect1.colliderect(w.rect) for w in self.walls):
                        dir = perp
                    elif not any(test_rect2.colliderect(w.rect) for w in self.walls):
                        dir = -perp
                    else:
                        dir = pygame.Vector2(0,0)
                move = dir
            else:
                move = pygame.Vector2(0,0)
        else:
            # --- 인식범위 밖: 자기 주변 80x80 내 랜덤 좌표로 이동 ---
            if self.roam_target is None or (self.pos.distance_to(self.roam_target) < 5):
                self.roam_target = self.get_local_roam_pos()
                self.roam_path = []
                self.roam_path_timer = 0

            self.roam_path_timer -= 1
            if self.roam_path_timer <= 0 or not self.roam_path:
                self.roam_path = find_path(self.pos, self.roam_target, self.walls)
                self.roam_path_timer = 30

            if self.roam_path:
                next_pos = self.roam_path[0]
                dir = next_pos - self.pos
                if dir.length() < self.speed:
                    self.pos = next_pos
                    self.roam_path.pop(0)
                else:
                    move = dir.normalize() * self.speed
            else:
                dir = self.roam_target - self.pos
                if dir.length(): move = dir.normalize() * self.speed

            if self.pos.distance_to(self.roam_target) < 5:
                self.roam_target = self.get_local_roam_pos()
                self.roam_path = []
                self.roam_path_timer = 0

        # --- 이동 전 위치 저장 ---
        prev_pos = pygame.Vector2(self.pos)
        for e in enemies:
            if e != self and self.rect.colliderect(e.rect):
                away = self.pos - e.pos
                if away.length(): away = away.normalize()
                self.pos += away
        self.pos += move
        self.rect.center = self.pos

        # --- 벽/화면 밖 보정 ---
        if any(self.rect.colliderect(w.rect) for w in self.walls):
            self.pos = prev_pos
            self.rect.center = self.pos
        self.pos.x = clamp(self.pos.x, 10, WIDTH-10)
        self.pos.y = clamp(self.pos.y, 10, HEIGHT-10)
        self.rect.center = self.pos

        # --- 저격 총알 발사 ---
        if self.chasing and dist < self.shoot_range and has_line_of_sight(self.pos, player.pos, self.walls):
            if self.aim_time > 60*6-15 and self.aim_time < 60*6-10:
                self.target_dir = (player.pos - self.pos).normalize() if (player.pos - self.pos).length() else pygame.Vector2(1,0)
            self.aim_time += 1
            if self.aim_time >= 360:  # 6초마다 저격
                bullets.add(LimeBullet(self.pos, self.target_dir, self.walls, "enemy"))
                self.aim_time = 0
        else:
            self.aim_time = 300

    def get_local_roam_pos(self):
        for _ in range(30):
            x = random.randint(int(self.pos.x-40), int(self.pos.x+40))
            y = random.randint(int(self.pos.y-40), int(self.pos.y+40))
            x = clamp(x, 20, WIDTH-20)
            y = clamp(y, 20, HEIGHT-20)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in self.walls):
                return pygame.Vector2(x, y)
        return pygame.Vector2(self.pos)



# --- 모든 적들의 인식/공격 범위 300, 100씩 증가 (아래 예시: 빨간 적) ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, walls):
        super().__init__()
        self.image = pygame.Surface((20,20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255,80,80), (10,10), 10)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.hp = 110
        self.max_hp = 110
        self.speed = 3
        self.walls = walls
        self.cool = 0
        self.aim_time = 0
        self.target_dir = pygame.Vector2(0,0)
        self.detect_range = 500  # 300 + 300
        self.shoot_range = 330   # 220 + 100
        self.stop_range = 70
        self.avoid_range = 60
        self.path = []
        self.path_timer = 0
        self.chasing = False
        # --- 랜덤 이동 관련 ---
        self.roam_target = None
        self.roam_path = []
        self.roam_path_timer = 0

    def get_random_roam_pos(self):
        # 화면 내에서 랜덤 좌표 반환 (벽과 겹치지 않게)
        for _ in range(30):
            x = random.randint(40, WIDTH-40)
            y = random.randint(40, HEIGHT-40)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in self.walls):
                return pygame.Vector2(x, y)
        return pygame.Vector2(self.pos)  # 실패시 제자리

    # --- 모든 적 공통: 80x80 내 랜덤 이동 함수 추가 ---
    def get_local_roam_pos(self):
        # 자기 중심 80x80 이내 랜덤 좌표 반환 (벽과 겹치지 않게)
        for _ in range(30):
            x = random.randint(int(self.pos.x-40), int(self.pos.x+40))
            y = random.randint(int(self.pos.y-40), int(self.pos.y+40))
            x = clamp(x, 20, WIDTH-20)
            y = clamp(y, 20, HEIGHT-20)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in self.walls):
                return pygame.Vector2(x, y)
        return pygame.Vector2(self.pos)  # 실패시 제자리

    def update(self, player, bullets, enemies):
        dist = self.pos.distance_to(player.pos)
        # 인식범위 내에서만 추적
        if dist < self.detect_range:
            self.chasing = True
        elif dist > self.detect_range + 40:
            self.chasing = False

        move = pygame.Vector2(0,0)
        should_move = True
        move_mode = "normal"

        if self.chasing:
            self.roam_target = None  # 추격 시작 시 랜덤 목표 해제
            can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
            if dist < self.avoid_range:
                move_mode = "avoid"
            elif dist < self.stop_range and can_shoot:
                move_mode = "stop"
            else:
                move_mode = "normal"

            # 경로 재탐색(0.5초마다)
            self.path_timer -= 1
            if self.path_timer <= 0 or not self.path:
                can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
                target_pos = player.pos
                if not can_shoot:
                    # 시야가 트이는 위치를 찾음
                    # 플레이어 주변 8방향 40~240픽셀 거리에서 시야가 트이는 곳을 랜덤으로 시도
                    found = False
                    for r in range(0, 300, 2):
                        for angle in range(0, 360, 5):
                            offset = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * r
                            test_pos = player.pos + offset
                            if has_line_of_sight(test_pos, player.pos, self.walls):
                                target_pos = test_pos
                                found = True
                                break
                        if found:
                            break
                self.path = find_path(self.pos, target_pos, self.walls)
                self.path_timer = 30

            if move_mode == "normal":
                if self.path:
                    next_pos = self.path[0]
                    dir = next_pos - self.pos
                    if dir.length() < self.speed:
                        self.pos = next_pos
                        self.path.pop(0)
                    else:
                        move = dir.normalize() * self.speed
                else:
                    dir = player.pos - self.pos
                    if dir.length(): move = dir.normalize() * self.speed
            elif move_mode == "avoid":
                dir = self.pos - player.pos
                if dir.length(): dir = dir.normalize() * self.speed
                test_rect = self.rect.move(dir.x, dir.y)
                blocked = any(test_rect.colliderect(w.rect) for w in self.walls)
                if blocked:
                    perp = pygame.Vector2(-dir.y, dir.x)
                    test_rect1 = self.rect.move(perp.x, perp.y)
                    test_rect2 = self.rect.move(-perp.x, -perp.y)
                    if not any(test_rect1.colliderect(w.rect) for w in self.walls):
                        dir = perp
                    elif not any(test_rect2.colliderect(w.rect) for w in self.walls):
                        dir = -perp
                    else:
                        dir = pygame.Vector2(0,0)
                move = dir
            else:
                move = pygame.Vector2(0,0)
        else:
            # --- 인식범위 밖: 자기 주변 80x80 내 랜덤 좌표로 이동 ---
            if self.roam_target is None or (self.pos.distance_to(self.roam_target) < 5):
                self.roam_target = self.get_local_roam_pos()
                self.roam_path = []
                self.roam_path_timer = 0

            # 목표까지 가는 경로가 없거나, 일정 주기마다 재탐색
            self.roam_path_timer -= 1
            if self.roam_path_timer <= 0 or not self.roam_path:
                self.roam_path = find_path(self.pos, self.roam_target, self.walls)
                self.roam_path_timer = 30

            if self.roam_path:
                next_pos = self.roam_path[0]
                dir = next_pos - self.pos
                if dir.length() < self.speed:
                    self.pos = next_pos
                    self.roam_path.pop(0)
                else:
                    move = dir.normalize() * self.speed
            else:
                dir = self.roam_target - self.pos
                if dir.length(): move = dir.normalize() * self.speed

            # 목표에 도달했는데 아직 플레이어가 인식범위 밖이면 새로운 랜덤 목표 설정
            if self.pos.distance_to(self.roam_target) < 5:
                self.roam_target = self.get_local_roam_pos()
                self.roam_path = []
                self.roam_path_timer = 0

        # 이동 전 위치 저장
        prev_pos = pygame.Vector2(self.pos)

        #실수로 인덴테이션 안함
        if self.shoot_range == self.shoot_range:
        # ...existing code...
            # 유닛 밀어내기
            for e in enemies:
                if e != self and self.rect.colliderect(e.rect):
                    away = self.pos - e.pos
                    if away.length(): away = away.normalize()
                    self.pos += away

            # --- x축 이동 ---
            self.pos.x += move.x
            self.rect.centerx = self.pos.x
            for wall in self.walls:
                if self.rect.colliderect(wall.rect):
                    if move.x > 0:
                        self.rect.right = wall.rect.left
                    elif move.x < 0:
                        self.rect.left = wall.rect.right
                    self.pos.x = self.rect.centerx

            # --- y축 이동 ---
            self.pos.y += move.y
            self.rect.centery = self.pos.y
            for wall in self.walls:
                if self.rect.colliderect(wall.rect):
                    if move.y > 0:
                        self.rect.bottom = wall.rect.top
                    elif move.y < 0:
                        self.rect.top = wall.rect.bottom
                    self.pos.y = self.rect.centery

            # 화면 밖 보정
            self.pos.x = clamp(self.pos.x, 10, WIDTH-10)
            self.pos.y = clamp(self.pos.y, 10, HEIGHT-10)
            self.rect.center = self.pos
            # ...existing code...

        # 총알 발사 조건: 사거리 내, 벽 없음
        if self.chasing and dist < self.shoot_range and has_line_of_sight(self.pos, player.pos, self.walls):
            if self.aim_time > 60-20 and self.aim_time < 60-10:
                self.target_dir = (player.pos - self.pos).normalize() if (player.pos - self.pos).length() else pygame.Vector2(1,0)
            self.aim_time += 1
            if self.aim_time >= 60:  # 매우 빠른 연사
                bullets.add(Bullet(self.pos, self.target_dir, self.walls, "enemy"))
                self.aim_time = 0
        else:
            self.aim_time = 0

# --- 핑크색 적 클래스 ---
class PinkEnemy(pygame.sprite.Sprite):
    def __init__(self, pos, walls):
        super().__init__()
        self.image = pygame.Surface((20,20), pygame.SRCALPHA)  # 기존 32x32 → 20x20
        pygame.draw.circle(self.image, (255, 120, 200), (10,10), 10)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.hp = 250
        self.max_hp = 250
        self.speed = 3.5
        self.walls = walls
        self.cool = 0
        self.aim_time = 0
        self.target_dir = pygame.Vector2(0,0)
        self.detect_range = 700  # 기존 2400 → 1800
        self.shoot_range = 500
        self.stop_range = 90
        self.avoid_range = 30
        self.path = []
        self.path_timer = 0
        self.chasing = False
        self.roam_target = None
        self.roam_path = []
        self.roam_path_timer = 0
        self.reload_time = 0  # 재장전 시간
        self.ammo = 10

    def update(self, player, bullets, enemies):
        dist = self.pos.distance_to(player.pos)
        if dist < self.detect_range:
            self.chasing = True
        elif dist > self.detect_range + 40:
            self.chasing = False

        move = pygame.Vector2(0,0)
        move_mode = "normal"
        if self.chasing:
            self.roam_target = None  # 추격 시작 시 랜덤 목표 해제
            can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
            if dist < self.avoid_range:
                move_mode = "avoid"
            elif dist < self.stop_range and can_shoot:
                move_mode = "stop"
            else:
                move_mode = "normal"

            self.path_timer -= 1
            if self.path_timer <= 0 or not self.path:
                can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
                target_pos = player.pos
                if not can_shoot:
                    # 시야가 트이는 위치를 찾음
                    # 플레이어 주변 8방향 40~120픽셀 거리에서 시야가 트이는 곳을 랜덤으로 시도
                    found = False
                    for r in range(0, 300, 2):
                        for angle in range(0, 360, 3):
                            offset = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * r
                            test_pos = player.pos + offset
                            if has_line_of_sight(test_pos, player.pos, self.walls):
                                target_pos = test_pos
                                found = True
                                break
                        if found:
                            break
                self.path = find_path(self.pos, target_pos, self.walls)
                self.path_timer = 30

            if move_mode == "normal":
                if self.path:
                    next_pos = self.path[0]
                    dir = next_pos - self.pos
                    if dir.length() < self.speed:
                        self.pos = next_pos
                        self.path.pop(0)
                    else:
                        move = dir.normalize() * self.speed
                else:
                    dir = player.pos - self.pos
                    if dir.length(): move = dir.normalize() * self.speed
            elif move_mode == "avoid":
                dir = self.pos - player.pos
                if dir.length(): dir = dir.normalize() * self.speed
                test_rect = self.rect.move(dir.x, dir.y)
                blocked = any(test_rect.colliderect(w.rect) for w in self.walls)
                if blocked:
                    perp = pygame.Vector2(-dir.y, dir.x)
                    test_rect1 = self.rect.move(perp.x, perp.y)
                    test_rect2 = self.rect.move(-perp.x, -perp.y)
                    if not any(test_rect1.colliderect(w.rect) for w in self.walls):
                        dir = perp
                    elif not any(test_rect2.colliderect(w.rect) for w in self.walls):
                        dir = -perp
                    else:
                        dir = pygame.Vector2(0,0)
                move = dir
            else:
                move = pygame.Vector2(0,0)

            # 유닛 밀어내기
            for e in enemies:
                if e != self and self.rect.colliderect(e.rect):
                    away = self.pos - e.pos
                    if away.length(): away = away.normalize()
                    self.pos += away
            self.pos += move
            self.rect.center = self.pos

        # 총알 발사 조건: 사거리 내, 벽 없음
        if dist < self.shoot_range and has_line_of_sight(self.pos, player.pos, self.walls):
            if self.aim_time > 20 and self.aim_time < 25:
                self.target_dir = (player.pos - self.pos).normalize() if (player.pos - self.pos).length() else pygame.Vector2(1,0)
            if self.ammo > 0:
                self.aim_time += 1
            else:
                self.aim_time = 0
            if self.ammo <= 0:
                self.reload_time += 1
                if self.reload_time >= 60*2:
                    self.ammo = 10
                    self.reload_time = 0
            if self.aim_time >= 30 and self.ammo > 0:  # 빠른 조준
                # 핑크색 총알 발사
                bullets.add(PinkBullet(self.pos, self.target_dir, self.walls, "enemy"))
                self.aim_time = 0
                self.ammo -= 1  # 발사 시 탄약 감소
        else:
            self.aim_time = 0

# --- 초록색 적 클래스 ---
class GreenEnemy(pygame.sprite.Sprite):
    def __init__(self, pos, walls, player):
        super().__init__()
        self.image = pygame.Surface((20,20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (80,255,80), (10,10), 10)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.hp = 220
        self.max_hp = 220
        self.speed = 2.5
        self.walls = walls
        self.cool = 0
        self.aim_time = 0
        self.target_dir = pygame.Vector2(0,0)
        self.detect_range = 800  # 300 + 300
        self.shoot_range = 620   # 150 + 100
        self.stop_range = 100
        self.avoid_range = 70
        self.path = []
        self.path_timer = 0
        self.chasing = False
        self.dodge_cool = 0
        self.last_player_shot = 0
        self.roam_target = None
        self.roam_path = []
        self.roam_path_timer = 0
        self.reload_time = 0  # 재장전 시간
        self.ammo = 30  # 초기 탄약

    def get_local_roam_pos(self):
        # 자기 중심 80x80 이내 랜덤 좌표 반환 (벽과 겹치지 않게)
        for _ in range(30):
            x = random.randint(int(self.pos.x-40), int(self.pos.x+40))
            y = random.randint(int(self.pos.y-40), int(self.pos.y+40))
            x = clamp(x, 20, WIDTH-20)
            y = clamp(y, 20, HEIGHT-20)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in self.walls):
                return pygame.Vector2(x, y)
        return pygame.Vector2(self.pos)  # 실패시 제자리

    def update(self, player, bullets, enemies):
        dist = self.pos.distance_to(player.pos)
        # 인식범위 내에서만 추적
        if dist < self.detect_range:
            self.chasing = True
        elif dist > self.detect_range + 40:
            self.chasing = False

        move = pygame.Vector2(0,0)
        move_mode = "normal"
        # 플레이어가 최근에 총을 쏘면 가끔 피하기
        if hasattr(player, "shoot_cool") and player.shoot_cool == 8 and self.dodge_cool == 0 and random.random() < 0.001:
            perp = pygame.Vector2(-(player.pos - self.pos).y, (player.pos - self.pos).x)
            if perp.length(): perp = perp.normalize()
            dodge_dist = 40
            test_pos = self.pos + perp * dodge_dist
            test_rect = self.rect.copy()
            test_rect.center = test_pos
            if not any(test_rect.colliderect(w.rect) for w in self.walls):
                self.pos = test_pos
                self.rect.center = self.pos
                self.dodge_cool = 90
        if self.dodge_cool > 0:
            self.dodge_cool -= 1

        if self.chasing:
            self.roam_target = None  # 추격 시작 시 랜덤 목표 해제
            can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
            if dist < self.avoid_range:
                move_mode = "avoid"
            elif dist < self.stop_range and can_shoot:
                move_mode = "stop"
            else:
                move_mode = "normal"

            self.path_timer -= 1
            if self.path_timer <= 0 or not self.path:
                can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
                target_pos = player.pos
                if not can_shoot:
                    # 시야가 트이는 위치를 찾음
                    # 플레이어 주변 8방향 40~240픽셀 거리에서 시야가 트이는 곳을 랜덤으로 시도
                    found = False
                    for r in range(0, 300, 2):
                        for angle in range(0, 360, 5):
                            offset = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * r
                            test_pos = player.pos + offset
                            if has_line_of_sight(test_pos, player.pos, self.walls):
                                target_pos = test_pos
                                found = True
                                break
                        if found:
                            break
                self.path = find_path(self.pos, target_pos, self.walls)
                self.path_timer = 30

            if move_mode == "normal":
                if self.path:
                    next_pos = self.path[0]
                    dir = next_pos - self.pos
                    if dir.length() < self.speed:
                        self.pos = next_pos
                        self.path.pop(0)
                    else:
                        move = dir.normalize() * self.speed
                else:
                    dir = player.pos - self.pos
                    if dir.length(): move = dir.normalize() * self.speed
            elif move_mode == "avoid":
                dir = self.pos - player.pos
                if dir.length(): dir = dir.normalize() * self.speed
                test_rect = self.rect.move(dir.x, dir.y)
                blocked = any(test_rect.colliderect(w.rect) for w in self.walls)
                if blocked:
                    perp = pygame.Vector2(-dir.y, dir.x)
                    test_rect1 = self.rect.move(perp.x, perp.y)
                    test_rect2 = self.rect.move(-perp.x, -perp.y)
                    if not any(test_rect1.colliderect(w.rect) for w in self.walls):
                        dir = perp
                    elif not any(test_rect2.colliderect(w.rect) for w in self.walls):
                        dir = -perp
                    else:
                        dir = pygame.Vector2(0,0)
                move = dir
            else:
                move = pygame.Vector2(0,0)
        else:
            # --- 인식범위 밖: 자기 주변 80x80 내 랜덤 좌표로 이동 ---
            if self.roam_target is None or (self.pos.distance_to(self.roam_target) < 5):
                self.roam_target = self.get_local_roam_pos()
                self.roam_path = []
                self.roam_path_timer = 0

            # 목표까지 가는 경로가 없거나, 일정 주기마다 재탐색
            self.roam_path_timer -= 1
            if self.roam_path_timer <= 0 or not self.roam_path:
                self.roam_path = find_path(self.pos, self.roam_target, self.walls)
                self.roam_path_timer = 30

            if self.roam_path:
                next_pos = self.roam_path[0]
                dir = next_pos - self.pos
                if dir.length() < self.speed:
                    self.pos = next_pos
                    self.roam_path.pop(0)
                else:
                    move = dir.normalize() * self.speed
            else:
                dir = self.roam_target - self.pos
                if dir.length(): move = dir.normalize() * self.speed

            # 목표에 도달했는데 아직 플레이어가 인식범위 밖이면 새로운 랜덤 목표 설정
            if self.pos.distance_to(self.roam_target) < 5:
                self.roam_target = self.get_local_roam_pos()
                self.roam_path = []
                self.roam_path_timer = 0

        # --- 이동 전 위치 저장 ---
        prev_pos = pygame.Vector2(self.pos)

        # 유닛 밀어내기
        for e in enemies:
            if e != self and self.rect.colliderect(e.rect):
                away = self.pos - e.pos
                if away.length(): away = away.normalize()
                self.pos += away
        self.pos += move
        self.rect.center = self.pos

        # --- 벽/화면 밖 보정 ---
        # 벽과 겹치면 이동 취소
        if any(self.rect.colliderect(w.rect) for w in self.walls):
            self.pos = prev_pos
            self.rect.center = self.pos
        # 화면 밖으로 나가면 보정
        self.pos.x = clamp(self.pos.x, 10, WIDTH-10)
        self.pos.y = clamp(self.pos.y, 10, HEIGHT-10)
        self.rect.center = self.pos

        # 총알 발사 조건: 사거리 내, 벽 없음
        if self.chasing and dist < self.shoot_range and has_line_of_sight(self.pos, player.pos, self.walls):
            self.target_dir = (player.pos - self.pos).normalize() if (player.pos - self.pos).length() else pygame.Vector2(1,0)
            if self.ammo > 0:
                self.aim_time += 1
            else:
                self.aim_time = 0
            if self.ammo <= 0:
                self.reload_time += 1
                if self.reload_time >= 60*4:
                    self.ammo = 30
                    self.reload_time = 0
            if self.aim_time >= 7 and self.ammo > 0:  # 빠른 연사
                bullets.add(GreenBullet(self.pos, self.target_dir, self.walls, "enemy"))
                self.aim_time = 0
                self.ammo -= 1  # 발사 시 탄약 감소
        elif self.aim_time > 0:
            self.aim_time -= 1
    
    

#신추가, 연보라색 적 관련
# --- 연보라색 적의 연막탄 ---
class SmokeBomb(pygame.sprite.Sprite):
    def __init__(self, pos, dir, walls, player):
        super().__init__()
        self.image = pygame.Surface((14,14), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (180,180,220,180), (7,7), 7)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.dir = dir
        self.speed = 8
        self.walls = walls
        self.player = player
        self.travel = 0
        self.max_dist = 100
        self.smoke_created = False

    def update(self, smokes_group=None):
        if self.smoke_created:
            self.kill()
            return
        move = self.dir * self.speed
        self.pos += move
        self.travel += move.length()
        self.rect.center = self.pos
        # 플레이어에 닿거나, 벽에 닿거나, 최대 이동거리 초과 시 연막 생성
        hit_wall = any(self.rect.colliderect(w.rect) for w in self.walls)
        hit_player = self.rect.colliderect(self.player.rect)
        if self.travel > self.max_dist or hit_wall or hit_player:
            if smokes_group is not None:
                for _ in range(6):
                    offset = pygame.Vector2(random.randint(-140,140), random.randint(-140,140))
                    smokes_group.add(SmokeEffect(self.pos + offset))
            self.smoke_created = True

# --- 연막 효과 ---
class SmokeEffect(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.radius = 100  # 200x200 크기(반지름 100)
        self.image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        self.alpha = 200
        self.color = (230, 230, 230)  # 밝은 회색
        pygame.draw.circle(self.image, self.color + (self.alpha,), (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect(center=pos)
        self.fade_speed = self.alpha / (60 * 10)  # 10초간 페이드(60fps 기준)

    def update(self):
        self.alpha -= self.fade_speed
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.fill((0,0,0,0))
            pygame.draw.circle(self.image, self.color + (int(self.alpha),), (self.radius, self.radius), self.radius)

# --- 연보라색 적 클래스 ---
class LavenderEnemy(pygame.sprite.Sprite):
    def __init__(self, pos, walls, player):
        super().__init__()
        self.image = pygame.Surface((20,20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (200,160,255), (10,10), 10)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.hp = 80
        self.max_hp = 80
        self.speed = 2
        self.walls = walls
        self.player = player
        self.detect_range = 750
        self.shoot_range = 230
        self.stop_range = 130
        self.avoid_range = 40
        self.path = []
        self.path_timer = 0
        self.chasing = False
        self.roam_target = None
        self.roam_path = []
        self.roam_path_timer = 0
        self.smoke_cool = 0  # 연막탄 쿨타임(프레임)
        self.smoke_group = None  # 외부에서 할당 필요

    def update(self, player, bullets, enemies, smokes_group):
        dist = self.pos.distance_to(player.pos)
        # 인식범위 내에서만 추적
        if dist < self.detect_range:
            self.chasing = True
        elif dist > self.detect_range + 40:
            self.chasing = False

        move = pygame.Vector2(0,0)
        move_mode = "normal"
        # 60% 확률로 비효율 경로 사용
        use_bad_path = random.random() < 0.6

        if self.chasing:
            self.roam_target = None  # 추격 시작 시 랜덤 목표 해제
            can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
            if dist < self.avoid_range:
                move_mode = "avoid"
            elif dist < self.stop_range and can_shoot:
                move_mode = "stop"
            else:
                move_mode = "normal"

            self.path_timer -= 1
            if self.path_timer <= 0 or not self.path:
                can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
                target_pos = player.pos
                if not can_shoot:
                    # 시야가 트이는 위치를 찾음
                    # 플레이어 주변 8방향 40~120픽셀 거리에서 시야가 트이는 곳을 랜덤으로 시도
                    found = False
                    for r in range(40, 121, 20):
                        for angle in range(0, 360, 45):
                            offset = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * r
                            test_pos = player.pos + offset
                            if has_line_of_sight(test_pos, player.pos, self.walls):
                                target_pos = test_pos
                                found = True
                                break
                        if found:
                            break
                self.path = find_path(self.pos, target_pos, self.walls)
                self.path_timer = 20

            if move_mode == "normal":
                if self.path:
                    next_pos = self.path[0]
                    dir = next_pos - self.pos
                    if dir.length() < self.speed:
                        self.pos = next_pos
                        self.path.pop(0)
                    else:
                        move = dir.normalize() * self.speed
                else:
                    dir = player.pos - self.pos
                    if dir.length(): move = dir.normalize() * self.speed
            elif move_mode == "avoid":
                dir = self.pos - player.pos
                if dir.length(): dir = dir.normalize() * self.speed
                test_rect = self.rect.move(dir.x, dir.y)
                blocked = any(test_rect.colliderect(w.rect) for w in self.walls)
                if blocked:
                    perp = pygame.Vector2(-dir.y, dir.x)
                    test_rect1 = self.rect.move(perp.x, perp.y)
                    test_rect2 = self.rect.move(-perp.x, -perp.y)
                    if not any(test_rect1.colliderect(w.rect) for w in self.walls):
                        dir = perp
                    elif not any(test_rect2.colliderect(w.rect) for w in self.walls):
                        dir = -perp
                    else:
                        dir = pygame.Vector2(0,0)
                move = dir
            else:
                move = pygame.Vector2(0,0)
        else:
            # 랜덤 이동
            if self.roam_target is None or (self.pos.distance_to(self.roam_target) < 5):
                self.roam_target = self.get_local_roam_pos()
                self.roam_path = []
                self.roam_path_timer = 0

            self.roam_path_timer -= 1
            if self.roam_path_timer <= 0 or not self.roam_path:
                self.roam_path = find_path(self.pos, self.roam_target, self.walls)
                self.roam_path_timer = 30

            if self.roam_path:
                next_pos = self.roam_path[0]
                dir = next_pos - self.pos
                if dir.length() < self.speed:
                    self.pos = next_pos
                    self.roam_path.pop(0)
                else:
                    move = dir.normalize() * self.speed
            else:
                dir = self.roam_target - self.pos
                if dir.length(): move = dir.normalize() * self.speed

            # 목표에 도달했는데 아직 플레이어가 인식범위 밖이면 새로운 랜덤 목표 설정
            if self.pos.distance_to(self.roam_target) < 5:
                self.roam_target = self.get_local_roam_pos()
                self.roam_path = []
                self.roam_path_timer = 0

        prev_pos = pygame.Vector2(self.pos)
        # 유닛 밀어내기
        for e in enemies:
            if e != self and self.rect.colliderect(e.rect):
                away = self.pos - e.pos
                if away.length(): away = away.normalize()
                self.pos += away
        self.pos += move
        self.rect.center = self.pos

        # 벽/화면 밖 보정
        if any(self.rect.colliderect(w.rect) for w in self.walls):
            self.pos = prev_pos
            self.rect.center = self.pos
        self.pos.x = clamp(self.pos.x, 10, WIDTH-10)
        self.pos.y = clamp(self.pos.y, 10, HEIGHT-10)
        self.rect.center = self.pos

        # 연막탄 던지기 (5초 쿨타임)
        if self.chasing and dist < self.shoot_range and self.smoke_cool == 0:
            dir = (player.pos - self.pos)
            if dir.length(): dir = dir.normalize()
            if smokes_group is not None:
                smokes_group.add(SmokeBomb(self.pos, dir, self.walls, player))
            self.smoke_cool = 60*20  # 20초(60fps 기준)
        if self.smoke_cool > 0:
            self.smoke_cool -= 1

    def get_local_roam_pos(self):
        for _ in range(30):
            x = random.randint(int(self.pos.x-40), int(self.pos.x+40))
            y = random.randint(int(self.pos.y-40), int(self.pos.y+40))
            x = clamp(x, 20, WIDTH-20)
            y = clamp(y, 20, HEIGHT-20)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in self.walls):
                return pygame.Vector2(x, y)

        return pygame.Vector2(self.pos)

# --- 갈색 적 클래스 ---
class BrownEnemy(pygame.sprite.Sprite):
    def __init__(self, pos, walls, player):
        super().__init__()
        self.image = pygame.Surface((20,20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (120, 80, 40), (10,10), 10)  # 갈색
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.hp = 90
        self.max_hp = 90
        self.speed = 3
        self.walls = walls
        self.player = player
        self.detect_range = 800
        self.shoot_range = 180
        self.stop_range = 80
        self.avoid_range = 50
        self.path = []
        self.path_timer = 0
        self.chasing = False
        self.roam_target = None
        self.roam_path = []
        self.roam_path_timer = 0
        self.cool = 0  # 발사 쿨타임

    def update(self, player, bullets, enemies, orbs_group):
        dist = self.pos.distance_to(player.pos)
        # 인식범위 내에서만 추적
        if dist < self.detect_range:
            self.chasing = True
        elif dist > self.detect_range + 40:
            self.chasing = False

        move = pygame.Vector2(0,0)
        move_mode = "normal"
        if self.chasing:
            self.roam_target = None  # 추격 시작 시 랜덤 목표 해제
            can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
            if dist < self.avoid_range:
                move_mode = "avoid"
            elif dist < self.stop_range and can_shoot:
                move_mode = "stop"
            else:
                move_mode = "normal"

            self.path_timer -= 1
            if self.path_timer <= 0 or not self.path:
                can_shoot = has_line_of_sight(self.pos, player.pos, self.walls)
                target_pos = player.pos
                if not can_shoot:
                    # 시야가 트이는 위치를 찾음
                    # 플레이어 주변 8방향 40~120픽셀 거리에서 시야가 트이는 곳을 랜덤으로 시도
                    found = False
                    for r in range(40, 121, 20):
                        for angle in range(0, 360, 45):
                            offset = pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle))) * r
                            test_pos = player.pos + offset
                            if has_line_of_sight(test_pos, player.pos, self.walls):
                                target_pos = test_pos
                                found = True
                                break
                        if found:
                            break
                self.path = find_path(self.pos, target_pos, self.walls)
                self.path_timer = 30

            if move_mode == "normal":
                if self.path:
                    next_pos = self.path[0]
                    dir = next_pos - self.pos
                    if dir.length() < self.speed:
                        self.pos = next_pos
                        self.path.pop(0)
                    else:
                        move = dir.normalize() * self.speed
                else:
                    dir = player.pos - self.pos
                    if dir.length(): move = dir.normalize() * self.speed
            elif move_mode == "avoid":
                dir = self.pos - player.pos
                if dir.length(): dir = dir.normalize() * self.speed
                test_rect = self.rect.move(dir.x, dir.y)
                blocked = any(test_rect.colliderect(w.rect) for w in self.walls)
                if blocked:
                    perp = pygame.Vector2(-dir.y, dir.x)
                    test_rect1 = self.rect.move(perp.x, perp.y)
                    test_rect2 = self.rect.move(-perp.x, -perp.y)
                    if not any(test_rect1.colliderect(w.rect) for w in self.walls):
                        dir = perp
                    elif not any(test_rect2.colliderect(w.rect) for w in self.walls):
                        dir = -perp
                    else:
                        dir = pygame.Vector2(0,0)
                move = dir
            else:
                move = pygame.Vector2(0,0)
        else:
            # --- 인식범위 밖: 자기 주변 80x80 내 랜덤 좌표로 이동 ---
            if self.roam_target is None or (self.pos.distance_to(self.roam_target) < 5):
                self.roam_target = self.get_local_roam_pos()
                self.roam_path = []
                self.roam_path_timer = 0

            self.roam_path_timer -= 1
            if self.roam_path_timer <= 0 or not self.roam_path:
                self.roam_path = find_path(self.pos, self.roam_target, self.walls)
                self.roam_path_timer = 30

            if self.roam_path:
                next_pos = self.roam_path[0]
                dir = next_pos - self.pos
                if dir.length() < self.speed:
                    self.pos = next_pos
                    self.roam_path.pop(0)
                else:
                    move = dir.normalize() * self.speed
            else:
                dir = self.roam_target - self.pos
                if dir.length(): move = dir.normalize() * self.speed

            # 목표에 도달했는데 아직 플레이어가 인식범위 밖이면 새로운 랜덤 목표 설정
            if self.pos.distance_to(self.roam_target) < 5:
                self.roam_target = self.get_local_roam_pos()
                self.roam_path = []
                self.roam_path_timer = 0

        prev_pos = pygame.Vector2(self.pos)
        for e in enemies:
            if e != self and self.rect.colliderect(e.rect):
                away = self.pos - e.pos
                if away.length(): away = away.normalize()
                self.pos += away
        self.pos += move
        self.rect.center = self.pos
        self.rect.center = self.pos
        self.pos.x = clamp(self.pos.x, 10, WIDTH-10)
        self.pos.y = clamp(self.pos.y, 10, HEIGHT-10)
        self.rect.center = self.pos

        # 회색 구체 발사 (5초 쿨타임)
        if self.chasing and dist < self.shoot_range and self.cool == 0:
            dir = (player.pos - self.pos)
            if dir.length(): dir = dir.normalize()
            if orbs_group is not None:
                orbs_group.add(GrayOrb(self.pos, dir, self.walls, player))
            self.cool = 720  # 12초(60fps 기준)
        if self.cool > 0:
            self.cool -= 1

    def get_local_roam_pos(self):
        for _ in range(30):
            x = random.randint(int(self.pos.x-40), int(self.pos.x+40))
            y = random.randint(int(self.pos.y-40), int(self.pos.y+40))
            x = clamp(x, 20, WIDTH-20)
            y = clamp(y, 20, HEIGHT-20)
            rect = pygame.Rect(x-10, y-10, 20, 20)
            if not any(rect.colliderect(w.rect) for w in self.walls):
                return pygame.Vector2(x, y)
        return pygame.Vector2(self.pos)

# --- UI ---
def draw_player_ui(player):
    pygame.draw.rect(screen, (0,0,0), (10,10,260,80))
   
    pygame.draw.rect(screen, (255,0,0), (20,20,player.hp*1.6,16))
    draw_text(screen, f"HP: {player.hp}/{player.max_hp}", (22,18))
    # 무기별 탄약 및 탄창 표시
    if player.gun_type == 1:
        ammo = player.ammo1
        max_ammo = player.max_ammo1
        mag = player.mag1
    elif player.gun_type == 2:
        ammo = player.ammo2
        max_ammo = player.max_ammo2
        mag = player.mag2
    elif player.gun_type == 3:
        ammo = player.ammo3
        max_ammo = player.max_ammo3
        mag = player.mag3
    elif player.gun_type == 4:
        ammo = player.ammo4
        max_ammo = player.max_ammo4
        mag = player.mag4
    elif player.gun_type == 5:
        ammo = player.ammo5
        max_ammo = player.max_ammo5
        mag = player.mag5
    elif player.gun_type == 7:
        ammo = player.ammo7
        max_ammo = player.max_ammo7
        mag = player.mag7
    elif player.gun_type == 6:
        ammo = player.ammo6
        max_ammo = player.max_ammo6
        mag = "∞"
    else:
        ammo = 0
        max_ammo = 0
        mag = 0
    draw_text(screen, f"AMMO: {ammo}/{max_ammo} | MAG: {mag}", (22,38))
    draw_text(screen, f"GOLD: {player.gold}", (22,58))

def draw_enemy_hp(enemy):
    x, y = enemy.rect.centerx-16, enemy.rect.top-10
    pygame.draw.rect(screen, (0,0,0), (x, y, 32, 6))
    pygame.draw.rect(screen, (255,0,0), (x+1, y+1, int(30*enemy.hp/enemy.max_hp), 4))

# --- 인게임 중앙 하단 총 정보 표시 함수 ---
def draw_gun_info(player):
    # 중앙 하단에 총 이름, 탄약수, 탄창수 표시
    if player.gun_type == 1:
        name = "MP5"
        ammo = player.ammo1
        mag = player.mag1
    elif player.gun_type == 2:
        name = "UMP45"
        ammo = player.ammo2
        mag = player.mag2
    elif player.gun_type == 3:
        name = "P90"
        ammo = player.ammo3
        mag = player.mag3
    elif player.gun_type == 4:
        name = "AWP"
        ammo = player.ammo4
        mag = player.mag4
    elif player.gun_type == 5:
        name = "Scout (SSG-08)"
        ammo = player.ammo5
        mag = player.mag5
    elif player.gun_type == 6:
        name = "AK-47"
        ammo = player.ammo6
        mag = player.mag6
    elif player.gun_type == 7:
        name = "G36"
        ammo = player.ammo7
        mag = player.mag7
    elif player.gun_type == 8:
        name = "FAMAR"
        ammo = player.ammo8
        mag = player.mag8
    elif player.gun_type == 9:
        name = "Mk14 EBR"
        ammo = player.ammo9
        mag = player.mag9
    elif player.gun_type == 10:
        name = "QBU-88"
        ammo = player.ammo10
        mag = player.mag10
    elif player.gun_type == 11:
        name = "M249"
        ammo = player.ammo11
        mag = player.mag11
    elif player.gun_type == 12:
        name = "MG42"
        ammo = player.ammo12
        mag = player.mag12
    elif player.gun_type == 13:
        name = "Remington 870"
        ammo = player.ammo13
        mag = player.mag13
    elif player.gun_type == 14:
        name = "Saiga-12"
        ammo = player.ammo14
        mag = player.mag14
    elif player.gun_type == 15:
        name = "Webley Mk VI"
        ammo = player.ammo15
        mag = "∞"
    else:
        name = "Unknown"
        ammo = 0
        mag = 0
    txt = f"{name} | ammo: {ammo} | mag: {mag}"
    draw_text(screen, txt, (WIDTH//2 - 80, HEIGHT - 60), (255,255,255))

# --- 게임 루프 ---
def main():
    # --- 디버깅용: 모든 스테이지 해금 ---
    DEBUG_UNLOCK_ALL_STAGE = True  # False로 바꾸면 원래대로

    if DEBUG_UNLOCK_ALL_STAGE:
        stage_unlocked = [True] * 50  # 50스테이지까지 해금
    else:
        stage_unlocked = [True] + [False]*49

    stage = 0
    game_state = "menu"
    player = None
    walls = None
    enemies = None
    bullets = pygame.sprite.Group()
    smokes = pygame.sprite.Group()  # 연막 효과 그룹 추가
    select_idx = 0
    page = 0
    mouse_down = False
    #no_ammo_time = 0
    orbs = pygame.sprite.Group()
    explosions = pygame.sprite.Group()

    menu_gun_select = 0
    gun_select = [0, 1, 2]

    # --- gun_names, gun_types, gun_desc에 DMR 추가 ---
    gun_names = ["MP5", "UMP45", "P90", "AWP", "Scout (SSG-08)", "AK-47", "G36", "FAMAR", "Mk14 EBR", "QBU-88", "M249", "MG42", "Remington 870", "Saiga-12"]
    gun_types = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]  # 7: DMR

    gun_desc = [
        {
            "이름": "MP5 (SMG)",
            "탄약": "30",
            "탄창": "3",
            "대미지": "22",
            "연사속도": "800",
            "총알속도": "850",
            "장전속도": "1.8s",
            "무게": "-5%",
            "반동": "medium",
            "거리": "short"
        },
        {
            "이름": "UMP45 (SMG)",
            "탄약": "25",
            "탄창": "3",
            "대미지": "26",
            "연사속도": "650",
            "총알속도": "780",
            "장전속도": "1.9s",
            "무게": "-6%",
            "반동": "medium",
            "거리": "short"
        },
        {
            "이름": "P90 (SMG)",
            "탄약": "50",
            "탄창": "2",
            "대미지": "20",
            "연사속도": "900",
            "총알속도": "900",
            "장전속도": "2.1s",
            "무게": "-7%",
            "반동": "medium",
            "거리": "short"
        },
        {
            "이름": "AWP (Sniper Riffle)",
            "탄약": "5",
            "탄창": "1",
            "대미지": "250",
            "연사속도": "40",
            "총알속도": "1400",
            "장전속도": "3.6s",
            "무게": "-20%",
            "반동": "small",
            "거리": "1200"
        },
        {
            "이름": "Scout (SSG-08) (Sniper Riffle)",
            "탄약": "10",
            "탄창": "2",
            "대미지": "205",
            "연사속도": "70",
            "총알속도": "1350",
            "장전속도": "2.8 sec",
            "무게": "-10%",
            "반동": "small",
            "거리": "1050"
        },
        {
            "이름": "AK-47 (AR)",
            "탄약": "30",
            "탄창": "3",
            "대미지": "36",
            "연사속도": "650",
            "총알속도": "950",
            "장전속도": "2.4s",
            "무게": "-12%",
            "반동": "medium",
            "거리": "650"
        },
        {
            "이름": "G36 (AR)",
            "탄약": "30",
            "탄창": "3",
            "대미지": "30",
            "연사속도": "720",
            "총알속도": "1000",
            "장전속도": "2.1s",
            "무게": "-9%",
            "반동": "medium",
            "거리": "650"
        },
        {
            "이름": "FAMAS (AR)",
            "탄약": "25",
            "탄창": "3",
            "대미지": "28",
            "연사속도": "900",
            "총알속도": "1020",
            "장전속도": "2.3s",
            "무게": "-11%",
            "반동": "medium",
            "거리": "650"
        },
        {
            "이름": "Mk14 EBR (DMR)",
            "탄약": "20",
            "탄창": "2",
            "대미지": "70",
            "연사속도": "350",
            "총알속도": "1250",
            "장전속도": "2.9s",
            "무게": "-14%",
            "반동": "medium",
            "거리": "1000"
        },
        {
            "이름": "QBU-88 (DMR)",
            "탄약": "15",
            "탄창": "3",
            "대미지": "60",
            "연사속도": "320",
            "총알속도": "11800",
            "장전속도": "2.6s",
            "무게": "-11%",
            "반동": "medium",
            "거리": "1000"
        },
        {
            "이름": "M249 (LMG)",
            "탄약": "100",
            "탄창": "1",
            "대미지": "30",
            "연사속도": "800",
            "총알속도": "900",
            "장전속도": "5.5s",
            "무게": "-30%",
            "반동": "lot",
            "거리": "700"
        },
        {
            "이름": "MG42 (LMG)",
            "탄약": "100",
            "탄창": "1",
            "대미지": "28",
            "연사속도": "1100",
            "총알속도": "920",
            "장전속도": "5.8s",
            "무게": "-33%",
            "반동": "lot",
            "거리": "700"
        },
        {
            "이름": "Remington 870 (Shotgun)",
            "탄약": "6",
            "탄창": "2",
            "대미지": "45 x 8",
            "연사속도": "70",
            "총알속도": "600",
            "장전속도": "3.2 sec",
            "무게": "-10%",
            "반동": "lot",
            "거리": "180"
        },
        {
            "이름": "Saiga-12 (Shotgun)",
            "탄약": "8",
            "탄창": "2",
            "대미지": "40 x 6",
            "연사속도": "180",
            "총알속도": "650",
            "장전속도": "3.0 sec",
            "무게": "-12%",
            "반동": "lot",
            "거리": "180"
        }
    ]

    while True:
        screen.fill((30,30,40))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if game_state == "menu":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        game_state = "stage_select"
                    elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                        menu_gun_select = event.key - pygame.K_1
                    elif event.key == pygame.K_LEFT:
                        for _ in range(len(gun_names)):
                            gun_select[menu_gun_select] = (gun_select[menu_gun_select] - 1) % len(gun_names)
                            if gun_select.count(gun_select[menu_gun_select]) == 1:
                                break
                    elif event.key == pygame.K_RIGHT:
                        for _ in range(len(gun_names)):
                            gun_select[menu_gun_select] = (gun_select[menu_gun_select] + 1) % len(gun_names)
                            if gun_select.count(gun_select[menu_gun_select]) == 1:
                                break
            elif game_state == "stage_select":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        page = (page -  1) % 5  # 5페이지로 변경
                        select_idx =  0
                    elif event.key == pygame.K_RIGHT:
                        page = (page + 1) % 5  # 5페이지로 변경
                        select_idx = 0
                    elif event.key == pygame.K_UP:
                        select_idx = (select_idx - 1) % 10
                    elif event.key == pygame.K_DOWN:
                        select_idx = (select_idx + 1) % 10
                    elif event.key == pygame.K_RETURN:
                        idx = page*10 + select_idx
                        if stage_unlocked[idx]:
                            stage = idx
                            game_state = "game"
                    elif event.key == pygame.K_ESCAPE:
                        game_state = "menu"
            elif game_state == "game":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_down = True
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_down = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        player.gun_type = gun_types[gun_select[0]]  
                    elif event.key == pygame.K_2:
                        player.gun_type = gun_types[gun_select[1]]
                    elif event.key == pygame.K_3:
                        player.gun_type = gun_types[gun_select[2]]
                    if event.key == pygame.K_4:
                        player.gun_type = 15  # 기본 권총(리볼버)

        # 메뉴/스테이지 선택 화면 그리기
        if game_state == "menu":
            draw_text(screen, "Top-Down_Shooting v.11", (WIDTH//2-120, HEIGHT//2-120))
            draw_text(screen, "STAGE SELECT: ENTER", (WIDTH//2-100, HEIGHT//2-40))
            draw_text(screen, "CHANGE SLOT: 1/2/3, CHANGE WEAPON: ←/→", (WIDTH//2-200, HEIGHT//2-10))
            for i in range(3):
                color = (255,255,0) if i == menu_gun_select else (200,200,200)
                gun_name = gun_names[gun_select[i]]
                draw_text(screen, f"SLOT {i+1}: {gun_name}", (WIDTH//2-80, HEIGHT//2+30+30*i), color)
            draw_text(screen, "SLOT 4: Webley Mk VI (PINNED)", (WIDTH//2-80, HEIGHT//2+120), (200,200,200))
            # --- 왼쪽 하단에 총 설명 ---
            desc_idx = gun_select[menu_gun_select]
            desc = gun_desc[desc_idx]
            y0 = HEIGHT-310  # 기존보다 100픽셀 위로 올림
            draw_text(screen, f"* WHEN START, CLICK ONCE TO ACTIVATE GUN", (380, y0-390), (255,0,0))
            draw_text(screen, f"SHOOT: CLICK", (20, y0-390), (255,255,255))
            draw_text(screen, f"MOVE: W, A, S, D", (20, y0-360), (255,255,255))
            draw_text(screen, f"RELOAD: R", (20, y0-330), (255,255,255))
            draw_text(screen, f"SWAP: 1, 2, 3, 4", (20, y0-300), (255,255,255))
            draw_text(screen, f"GUN INFO", (20, y0), (255,255,255))
            draw_text(screen, f"TYPE: {desc['이름']}", (20, y0+30))
            draw_text(screen, f"AMMO: {desc['탄약']} | MAG: {desc['탄창']}", (20, y0+60))
            draw_text(screen, f"DMG: {desc['대미지']}", (20, y0+90))
            draw_text(screen, f"RANGE: {desc['거리']}", (20, y0+120))
            draw_text(screen, f"RPM: {desc['연사속도']}", (20, y0+150))
            draw_text(screen, f"BULLET SPEED: {desc['총알속도']}", (20, y0+180))
            draw_text(screen, f"RELOAD TIME: {desc['장전속도']}", (20, y0+210))
            draw_text(screen, f"RECOIL: {desc['반동']}", (20, y0+240))
            draw_text(screen, f"MOVE SPEED: {desc['무게']}", (20, y0+270))
        elif game_state == "stage_select":
            draw_text(screen, f"STAGE SELECT (←→, ↑↓, ENTER, ESC:menu)", (WIDTH//2-180, HEIGHT//2-120))
            draw_text(screen, f"PAGE {page+1}/5", (WIDTH//2-40, HEIGHT//2-80))  # 5페이지로 변경
            for i in range(10):
                idx = page*10 + i
                if idx >= 50:
                    continue  # 50스테이지까지만 표시
                txt = f"STAGE {idx+1} {'(UNLOCKED)' if stage_unlocked[idx] else '(LOCKED)'}"
                color = (255,255,0) if i == select_idx else (255,255,255)
                draw_text(screen, txt, (WIDTH//2-80, HEIGHT//2-40+40*i), color)
        elif game_state == "game":
            if player is None:
                player = Player((WIDTH//2, HEIGHT-80))
                player.gun_type = gun_types[gun_select[0]]
                reset_shoot = False
                gamestart = True
                walls = make_walls()
                enemies = make_enemies(walls, stage, player)
                bullets.empty()
                smokes.empty()
            player.update(walls)
            bullets.update()
            # --- LavenderEnemy만 smokes 넘겨주기 ---
            for enemy in enemies:
                if isinstance(enemy, LavenderEnemy):
                    enemy.update(player, bullets, enemies, smokes)
                elif isinstance(enemy, BrownEnemy):
                    enemy.update(player, bullets, enemies, orbs)
                else:
                    enemy.update(player, bullets, enemies)
            # smokes.update()
            for smoke in list(smokes):
                if isinstance(smoke, SmokeBomb):
                    smoke.update(smokes)
                else:
                    smoke.update()
            # 총알-적 충돌
            for bullet in list(bullets):
                if bullet.owner == "player":
                    hit = pygame.sprite.spritecollideany(bullet, enemies)
                    if hit:
                        hit.hp -= bullet.damage
                        bullet.kill()
                elif bullet.owner == "enemy":
                    if player.rect.colliderect(bullet.rect):
                        player.hp -= getattr(bullet, "damage", 20)
                        bullet.kill()
            # 적 사망
            for enemy in list(enemies):
                if enemy.hp <= 0:
                    enemies.remove(enemy)
                    player.gold += 20
            # 클리어/게임오버 처리
            if player.hp <= 0:
                gamestart = False
                reset_shoot = False
                draw_text(screen, "GAME OVER", (WIDTH//2-80, HEIGHT//2))
                pygame.display.flip(); pygame.time.wait(1500)
                player = None; game_state = "menu"
            if len(enemies) == 0:
                gamestart = False
                reset_shoot = False
                draw_text(screen, "STAGE CLEAR!", (WIDTH//2-80, HEIGHT//2))
                if stage+1 < len(stage_unlocked):
                    stage_unlocked[stage+1] = True
                player.gold += 100
                pygame.display.flip(); pygame.time.wait(1500)
                player = None; game_state = "stage_select"

            # 그리기
            walls.draw(screen)
            for enemy in enemies:
                screen.blit(enemy.image, enemy.rect)
                draw_enemy_hp(enemy)
            bullets.draw(screen)
            orbs.draw(screen)        
            explosions.draw(screen)   

            if player is not None:
                screen.blit(player.image, player.rect)

            # --- BrownEnemy의 회색 구체(GrayOrb) 업데이트 ---
            for orb in list(orbs):
                orb.update(explosions)
                if player is not None and orb.rect.colliderect(player.rect):
                    player.hp -= orb.damage
                    orb.exploded = True

            # --- 주황색 폭발(OrangeExplosion) 업데이트 ---
            for exp in list(explosions):
                exp.update(player)
            
            smokes.draw(screen)  # 연막 효과를 UI보다 아래에 그리기

            if player is not None:
                draw_player_ui(player)
                draw_gun_info(player)  # 중앙 하단 총 정보 표시

                # --- 조준선 표시 (SR, DMR) ---
                if player.gun_type in [4, 5, 8, 9]:
                    mx, my = pygame.mouse.get_pos()
                    px, py = int(player.pos.x), int(player.pos.y)
                    dir = pygame.Vector2(mx - px, my - py)
                    if dir.length():
                        dir = dir.normalize()
                        # SR: 무한, DMR: 800픽셀
                        max_len = 1200 if player.gun_type == 2 else 900
                        end_x = px + dir.x * max_len
                        end_y = py + dir.y * max_len
                        # 벽에 막히면 거기서 멈춤
                        for wall in walls:
                            hit = wall.rect.clipline((px, py), (end_x, end_y))
                            if hit:
                                end_x, end_y = hit[0]
                                break
                        # 알파값 적용(투명) 조준선 그리기
                        aim_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        pygame.draw.line(aim_surface, (255,0,0,120), (px, py), (end_x, end_y), 4)
                        screen.blit(aim_surface, (0,0))

        if game_state == "game" and not(mouse_down) and gamestart==True:
            reset_shoot = True

        # --- 마우스 왼쪽 버튼 누르고 있을 때 자동 발사 ---
        if game_state == "game" and mouse_down and reset_shoot==True:
            player.try_auto_shoot(pygame.mouse.get_pos(), bullets, walls)

        pygame.display.flip()
        clock.tick(60)
if __name__ == "__main__":
    main()
