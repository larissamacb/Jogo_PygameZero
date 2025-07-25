import pgzrun
from pygame import Rect
from character import Character # classe criada para o personagem

music.play('get_ready_mario')

# Configurações do mapa
TILE_SIZE = 64
COLUMNS = 20
ROWS = 12
WIDTH = TILE_SIZE * COLUMNS # vemos como 20 colunas de tiles
HEIGHT = TILE_SIZE * ROWS # 12 linhas de tiles

GRAVITY = 0.8
BEE_SPEED = 2

game_state = 'menu' # menu, active, won, over
spring_timer = 0
weak_plat_state = 'idle'
lever_activated = False
frame_counter = 0
box_vy = 0
box_vx = 0
button_pressed = False
collected_gems = 0

sounds_mute = False
music_mute = False

# Música e sons de efeito
SOUNDS = {
    "bump": sounds.sfx_bump,
    "fall": sounds.sfx_throw,
    "gem_collected": sounds.sfx_gem,
    "something_activated": sounds.sfx_magic,
    "player_hurt": sounds.sfx_hurt,
    "jump": sounds.sfx_jump,
    "select": sounds.sfx_select,
}

# Elementos do menu
play_button = Actor('jogar', (WIDTH / 2, TILE_SIZE * 8))
sound_button = Actor('sound_on', (566, 654))
music_button = Actor('music_on', (710, 654))

# Criação do background e elementos estáticos de colisão
platforms = [
    "11111000000000000000",
    "00000000000000000000",
    "00000000000000000000",
    "11110111001110000011",
    "00000000000000000000",
    "00000000000000000000",
    "00000001100000001110",
    "00000000000000000000",
    "00000000111110000000",
    "00010000111110010000",
    "00000000111110000000",
    "11110000111111110000",
]

background = Actor('map')
background.topleft = (0, 0)

platform_rects = []
for row_index, row in enumerate(platforms):
    for col_index, num in enumerate(row):
        if num == "1":
            rect = Rect((col_index * TILE_SIZE, row_index * TILE_SIZE), (TILE_SIZE, TILE_SIZE))
            platform_rects.append(rect)
            
stone_rect = Rect(TILE_SIZE * 10, TILE_SIZE * 7, TILE_SIZE, TILE_SIZE)
            
# Elementos não estáticos do mapa
weak_platforms = [
    Actor('block_idle', topleft=(TILE_SIZE * 5, TILE_SIZE * 8)),
    Actor('block_idle', topleft=(TILE_SIZE * 6, TILE_SIZE * 8)),
]
weak_platforms_original_pos = [p.topleft for p in weak_platforms]

gems = [
    Actor('gem_red', topleft=(TILE_SIZE * 0, TILE_SIZE * 2)),
    Actor('gem_green', topleft=(TILE_SIZE * 18, TILE_SIZE * 2))
]

red_block = Actor('block_red', topleft=(TILE_SIZE * 4, TILE_SIZE * 1))
green_block = Actor('block_green', topleft=(TILE_SIZE * 15, TILE_SIZE * 0))
blocks = [red_block, green_block]


button = Actor('switch_green', topleft=(TILE_SIZE * 13, TILE_SIZE * 10))
button.hitbox = Rect(0, 0, TILE_SIZE, TILE_SIZE / 3)
lever = Actor('lever_left', topleft=(TILE_SIZE * 11, TILE_SIZE * 2))
box = Actor('block_plank', topleft=(TILE_SIZE * 12, TILE_SIZE * 7))
spring = Actor('spring_out', topleft=(TILE_SIZE * 9, TILE_SIZE * 7))

barnacles = [
    Actor('barnacle_attack_a', topleft=(TILE_SIZE * 4, TILE_SIZE * 11)),
    Actor('barnacle_attack_a', topleft=(TILE_SIZE * 5, TILE_SIZE * 11)),
    Actor('barnacle_attack_a', topleft=(TILE_SIZE * 6, TILE_SIZE * 11)),
    Actor('barnacle_attack_a', topleft=(TILE_SIZE * 7, TILE_SIZE * 11)),
    
    Actor('barnacle_attack_a', topleft=(TILE_SIZE * 16, TILE_SIZE * 11)),
    Actor('barnacle_attack_a', topleft=(TILE_SIZE * 17, TILE_SIZE * 11)),
    Actor('barnacle_attack_a', topleft=(TILE_SIZE * 18, TILE_SIZE * 11)),
    Actor('barnacle_attack_a', topleft=(TILE_SIZE * 19, TILE_SIZE * 11)),
]


bees = [
    Actor('bee_a', topleft=(TILE_SIZE * 3, TILE_SIZE * 6)),
    Actor('bee_a', topleft=(TILE_SIZE * 11, TILE_SIZE * 4)),
]

for i, bee in enumerate(bees):
    bee.range_start_x = bee.x - 2 * TILE_SIZE
    bee.range_end_x = bee.x + 2 * TILE_SIZE # as abelhas tem um range de 5 tiles
    if i == 0: bee.direction = 1 # uma começa indo pra direita
    else: bee.direction = -1 # e a outra pra esquerda
    bee.hitbox = Rect(0, 0, bee.width * 0.6, bee.height * 0.6)
    
def play_music():
    """ Ativar/desativar a música """
    if music_mute:
        music.pause()
    else:
        music.unpause()


def play_sound(event=None):
    """ Ativar/desativar os sons de efeito """
    global SOUNDS
    if not sounds_mute and event != None:
        SOUNDS.get(event).play()
      
        
# Instanciando o jogador
player = Character(x=100, y=400, play_sound=play_sound, clock_module=clock)

def on_mouse_down(pos, button):
    """ Responde a cliques de botões do menu """
    global sound_button, sounds_mute, music_button, music_mute, game_state
    if button == mouse.LEFT and sound_button.collidepoint(pos):
        sounds_mute = not sounds_mute
        sound_button.image = 'sound_off' if sounds_mute else 'sound_on'
        play_sound()
    if button == mouse.LEFT and music_button.collidepoint(pos):
        music_mute = not music_mute
        music_button.image = 'music_off' if music_mute else 'music_on'
        play_music()
    if button == mouse.LEFT and play_button.collidepoint(pos):
        game_state = 'active'
        play_sound('select')


def catch_gem():
    """ Coleta as gemas quando o jogador passa por elas """
    global collected_gems
    
    for gem in gems[:]:
        if gem.colliderect(player.hitbox):
            gems.remove(gem)
            collected_gems += 1
            play_sound('gem_collected')


# Funções agendadas com o clock.schedule

def make_platform_fall():
    """ Função agendada para mudar o estado das plataformas instáveis para 'caindo' """
    global weak_plat_state
    weak_plat_state = 'falling'
    play_sound('fall')
    
    
def finish_lever_animation():
    """ Função agendada para finalizar a animação da alavanca """
    lever.image = 'lever_right'
    
    
def respawn_weak_platforms():
    """ Função agendada para respawnar as plataformas instáveis """
    global weak_plat_state
    for i, plat in enumerate(weak_platforms):
        plat.topleft = weak_platforms_original_pos[i]
        plat.image = 'block_idle'
    weak_plat_state = 'idle'
    
    
# Funções de atualização dos objetos interativos do cenário

def update_box():
    """ Atualiza as interações e colisões com a caixa. """
    global box_vy, button_pressed
    
    # Aplicando física
    if not button_pressed:
        box_vy += GRAVITY
        box.y += box_vy
        
    # Sendo empurrada
    if not button_pressed and player.hitbox.colliderect(box._rect):
        if player.hitbox.left > box.centerx:
            # Tentando empurrar para a esquerda
            if not box.colliderect(stone_rect):
                box.x -= player.MOVE_SPEED

        elif player.hitbox.right < box.centerx:
            box.x += player.MOVE_SPEED
    
    # Colisão com plataformas
    for plat in platform_rects:
        if box._rect.colliderect(plat):
            if box_vy > 0:
                box.bottom = plat.top
                box_vy = 0
            elif box_vy < 0:
                box.top = plat.bottom
                box_vy = 0
            else:
                play_sound('fall')
            break
        
        
def update_green_button():
    """ Verifica se a caixa pressionou o botão e move o bloco verde. """
    global box_vy, button_pressed
    
    button.hitbox.center = button.center
    if not button_pressed and box._rect.colliderect(button.hitbox):
        button_pressed = True
        button.image = 'switch_green_pressed'
        play_sound('something_activated')
        box.bottom = button.top + (button.height / 2)
        box_vy = 0
        button.hitbox.height = TILE_SIZE / 4
        button.hitbox.bottom = button.bottom
        
        # Move o bloco
        animate(green_block, pos=(green_block.x, green_block.y + TILE_SIZE * 3), duration=1.0)


def update_spring():
    """ Faz a interação com a mola e sua animação. """
    global spring_timer
    
    if player.hitbox.colliderect(spring._rect) and player.vy > 0:
        player.vy = -25
        player.on_ground = False
        spring.image = 'spring'
        play_sound('bump')
        spring_timer = 0
    
    spring_timer += 1
    if spring_timer > 5:
        spring.image = 'spring_out'


def update_lever():
    """ Verifica se a alavanca foi ativada e move o bloco vermelho. """
    global lever_activated
    
    if not lever_activated and player.hitbox.colliderect(lever._rect):
        lever_activated = True
        play_sound('something_activated')
        lever.image = 'lever'
        animate(lever, angle=lever.angle, duration=0.2, on_finished=finish_lever_animation)
        
        # Move o bloco
        animate(red_block, pos=(red_block.x, red_block.y + TILE_SIZE * 2), duration=1.0)


def update_weak_platforms(landed_on_weak):
    """ Gerencia os estados das plataformas instáveis. """
    global weak_plat_state
    
    # Se o jogador pisa na plataforma
    if weak_plat_state == 'idle' and landed_on_weak:
        weak_plat_state = 'cracking'
        for plat in weak_platforms:
            plat.image = 'block_fall'
        clock.schedule_unique(make_platform_fall, 2.0)

    # Queda da plataforma e respawn
    if weak_plat_state == 'falling':
        
        all_off_screen = True
        for plat in weak_platforms:
            plat.image = 'block_fall'
            plat.y += 15
            if plat.top < HEIGHT:
                 all_off_screen = False

        if all_off_screen:
            weak_plat_state = 'destroyed'
            clock.schedule_unique(respawn_weak_platforms, 2.0)


def update_enemies_animation():
    """ Atualiza a animação e movimento dos inimigos. """
    global frame_counter
    frame_counter += 1

    # Animação dos barnacles
    if frame_counter % 30 == 0:
        for barnacle in barnacles:
            if barnacle.image == 'barnacle_attack_a':
                barnacle.image = 'barnacle_attack_b'
            else:
                barnacle.image = 'barnacle_attack_a'
    
    # Movimento e animação das abelhas
    for bee in bees:
        bee.x += BEE_SPEED * bee.direction
        if bee.x > bee.range_end_x or bee.x < bee.range_start_x:
            bee.direction *= -1
        
        frame_index = (frame_counter // 10) % 2
        if bee.direction > 0:
            images = ['bee_a', 'bee_b']
            bee.image = images[frame_index]
        else:
            images = ['bee_a_left', 'bee_b_left']
            bee.image = images[frame_index]


def update_game_state():
    """ Atualiza o estado do jogo de acordo com as condições de vitória e derrota. """
    global game_state
    if collected_gems == 2:
        game_state = 'won'
    if player.lives == 0:
        game_state = 'over'


# Funções principais do Pygame Zero

def draw():
    """ Desenha os elementos na tela. """
    global screen, game_state
    
    if game_state == 'menu':
        screen.blit('menu', (0, 0))
        play_button.draw()
        sound_button.draw()
        music_button.draw()
    elif game_state == 'won':
        screen.blit('game_won', (0, 0))
    elif game_state == 'over':
        screen.blit('game_over', (0, 0))
    else:
    
        background.draw()
        
        for gem in gems:
            gem.draw()
        for plat in weak_platforms:
            plat.draw()
        for barnacle in barnacles:
            barnacle.draw()
        for bee in bees:
            bee.draw()
            
        red_block.draw()
        green_block.draw()
        lever.draw()
        button.draw()
        spring.draw()
        box.draw()
        
        player.draw()
        
       # Vidas do jogador
        for i in range(player.lives):
            x = WIDTH - 80 - (i * 40)
            screen.blit('heart', (x, 20))


def update():
    """ Função de atualização que executa as outras """
    
    update_game_state()
    
    player.set_screen_limits(WIDTH, HEIGHT)
    
    catch_gem()
    
    # Cria a lista das possíveis colisões para o jogador
    all_platforms = platform_rects[:]
    if weak_plat_state != 'falling':
        all_platforms.extend([p._rect for p in weak_platforms])
    all_platforms.extend([b._rect for b in blocks]) 
    all_enemies = barnacles + bees
    
    landed_on_weak = player.update(keyboard, all_platforms, weak_platforms, all_enemies)
    
    update_box()
    update_green_button()
    update_spring()
    update_lever()
    update_weak_platforms(landed_on_weak)
    update_enemies_animation()


pgzrun.go()