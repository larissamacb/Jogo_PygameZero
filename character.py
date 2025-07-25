from pgzero.actor import Actor
from pygame import Rect

class Character:
    def __init__(self, x, y, play_sound, clock_module):
        self.GRAVITY = 0.8
        self.JUMP_STRENGTH = -17
        self.MOVE_SPEED = 4
        
        self.play_sound = play_sound
        self.clock = clock_module

        self.actor = Actor('character_beige_front', (x, y))
        self.actor.anchor = ('center', 'bottom')
        self.hitbox = Rect(0, 0, self.actor.width * 0.4, self.actor.height * 0.75)
        #self.hitbox.center = self.actor.center

        self.vy = 0
        self.vx = 0
        self.lives = 3
        self.on_ground = False
        self.facing_right = True
        self.invincible_and_teleporting = False
        
        self.last_safe_position = (self.actor.x, self.actor.y)

        self.invincibility_timer = 0
        self.teleport_timer = 0
        self.teleport_duration = 30  # frames

        self.animation_timer = 0
        self.animation_frame = 0
        self.animations = {
            'idle': ['character_beige_front', 'character_beige_front_breath'],
            'walk_right': ['character_beige_walk_a', 'character_beige_walk_b'],
            'walk_left': ['character_beige_walk_a_left', 'character_beige_walk_b_left'],
            'jump_right': 'character_beige_jump',
            'jump_left': 'character_beige_jump_left',
            'fall_right': 'character_beige_duck',
            'fall_left': 'character_beige_duck_left',
            'hit_right': 'character_beige_hit',
            'hit_left': 'character_beige_hit_left'
        }


    def take_damage(self, knockback_direction):
        """ Dá dano ao personagem, tirando uma vida e o deixando momentaneamente invencível """
        if self.invincibility_timer > 0:
            return
        self.lives -= 1
        self.invincibility_timer = 60
        self.vy = -5
        self.vx = 6 * knockback_direction


    def teleport_to_safe(self):
        """ Teleporta o personagem para um local seguro caso caia nos barnacles """
        self.actor.pos = self.last_safe_position
        #self.hitbox.center = self.last_safe_position
        self.vx = 0
        self.vy = 0
        self.invincible_and_teleporting = True
        self.teleport_timer = self.teleport_duration


    def check_enemy_collisions(self, enemies):
        """ Checa se houve colisão com inimigos """
        if self.invincibility_timer == 0:

            for enemy in enemies:
                if hasattr(enemy, 'hitbox'): # é abelha
                    enemy.hitbox.center = enemy.center
                    rect_to_check = enemy.hitbox
                else: # é barnacle
                    rect_to_check = enemy._rect

                if self.hitbox.colliderect(rect_to_check):
                    knockback_direction = -1 if self.actor.centerx < enemy.centerx else 1
                    self.take_damage(knockback_direction)
                    self.play_sound('player_hurt')

                    if not hasattr(enemy, 'hitbox'):
                        self.teleport_to_safe()
                    break


    def handle_horizontal_collision(self, dx, platforms):
        """ Lida com colisões horizontais """
        self.actor.x += dx
        self.hitbox.centerx = self.actor.centerx # evita bugs
        for plat in platforms:
            if self.hitbox.colliderect(plat):
                if dx > 0: self.hitbox.right = plat.left 
                elif dx < 0: self.hitbox.left = plat.right
                self.actor.centerx = self.hitbox.centerx
                #self.vx = 0
                break


    def handle_vertical_collision(self, platforms, weak_platforms):
        """ Lida com colisões verticais e retorna se o personagem está em uma plataforma instável """
        landed_on_weak = False
        self.on_ground = False
        self.actor.y += self.vy
        #self.hitbox.centery = self.actor.y - self.hitbox.height / 2
        self.hitbox.bottom = self.actor.bottom

        for plat in platforms:
            if self.hitbox.colliderect(plat):
                if self.vy > 0: # se estava caindo
                    for weak_plat in weak_platforms: # verifica se foi na plataforma instável
                        if weak_plat._rect == plat:
                            landed_on_weak = True
                    if not landed_on_weak: # se não foi, é uma posição segura (para futuro respawn)
                        self.last_safe_position = (self.actor.x, self.actor.y)
                    self.hitbox.bottom = plat.top
                    self.on_ground = True
                    self.vy = 0
                elif self.vy < 0: # se estava pulando
                    self.hitbox.top = plat.bottom
                    self.vy = 0
                self.actor.bottom = self.hitbox.bottom
                break
        return landed_on_weak
    
    
    def set_animation(self, horizontal_movement):
        """ Gerencia as animações do personagem """
        
        # Invencível (levou dano)
        if self.invincibility_timer > 0:
            if self.invincibility_timer % 10 < 5:
                self.actor.image = self.animations['hit_right'] if self.facing_right else self.animations['hit_left']
            else:
                self.actor.image = 'empty'
            return

        if not self.on_ground:
            # Pulando
            if self.vy < 0:
                self.actor.image = self.animations['jump_right'] if self.facing_right else self.animations['jump_left']
            # Caindo
            else:
                self.actor.image = self.animations['fall_right'] if self.facing_right else self.animations['fall_left']
        
        # Andando
        elif horizontal_movement != 0:
            self.animation_timer += 1
            if self.animation_timer > 8:
                self.animation_timer = 0
                self.animation_frame = 1 - self.animation_frame
            key = 'walk_right' if self.facing_right else 'walk_left'
            self.actor.image = self.animations[key][self.animation_frame]
        # Parado
        else:
            self.animation_timer += 1
            if self.animation_timer > 20:
                self.animation_timer = 0
                self.animation_frame = 1 - self.animation_frame
            self.actor.image = self.animations['idle'][self.animation_frame]


    def set_screen_limits(self, WIDTH, HEIGHT):
        """ Impede que o personagem saia dos limites da tela """
        
        self.hitbox.centerx = self.actor.centerx
        self.hitbox.bottom = self.actor.bottom
        
        if self.hitbox.left < 0:
            self.hitbox.left = 0
        if self.hitbox.right > WIDTH:
            self.hitbox.right = WIDTH
        if self.hitbox.bottom > HEIGHT:
            self.hitbox.bottom = HEIGHT
            self.vy = 0
            
        self.actor.centerx = self.hitbox.centerx
        self.actor.bottom = self.hitbox.bottom


    def update(self, keyboard, all_solid_platforms, weak_platforms, all_enemies):
        """ Faz as atualizações gerais do personagem """
        
        #self.hitbox.centerx = self.actor.centerx
        #self.hitbox.bottom = self.actor.bottom
        
        # Aplica gravidade
        self.vy += self.GRAVITY

        if self.invincible_and_teleporting:
            self.teleport_timer -= 1
            self.vx = 0
            self.vy = 0
            self.actor.pos = self.last_safe_position
            self.hitbox.center = self.last_safe_position
            if self.teleport_timer <= 0:
                self.invincible_and_teleporting = False
                self.invincibility_timer = 60
            return False

        self.check_enemy_collisions(all_enemies)

        dx = 0

        # Responde a inputs do teclado caso o personagem não tenha tomado dano
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1
            self.vx *= 0.9
            dx = self.vx
        else:
            if keyboard.left:
                dx = -self.MOVE_SPEED
                self.facing_right = False
            if keyboard.right:
                dx = self.MOVE_SPEED
                self.facing_right = True

            if (keyboard.up or keyboard.space) and self.on_ground:
                self.vy = self.JUMP_STRENGTH
                self.on_ground = False
                self.play_sound('jump')

        self.handle_horizontal_collision(dx, all_solid_platforms)
        self.set_animation(dx)
        
        landed_on_weak = self.handle_vertical_collision(all_solid_platforms, weak_platforms)
        
        return landed_on_weak


    def draw(self):
        self.actor.draw()
