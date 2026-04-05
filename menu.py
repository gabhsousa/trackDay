import pygame
import sys
from config import WINDOW_WIDTH, WINDOW_HEIGHT

# Como a seleção de pistas precisa saber os dados da pista:
from tracks_data import get_all_tracks 

def draw_menu_text(surface, text, font, color, x, y, align="left"):
    """Função compartilhada por todos os menus para desenhar textos com borda"""
    surface_color = font.render(text, True, color)
    surface_outline = font.render(text, True, (0, 0, 0)) 
    
    rect = surface_color.get_rect()
    if align == "left":
        rect.x = x
    elif align == "right":
        rect.right = x
    elif align == "center":
        rect.centerx = x
    rect.y = y

    outline_width = 2
    for dx in [-outline_width, 0, outline_width]:
        for dy in [-outline_width, 0, outline_width]:
            if dx != 0 or dy != 0:
                surface.blit(surface_outline, (rect.x + dx, rect.y + dy))
                
    surface.blit(surface_color, rect)


class StartMenu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        try:
            self.cover_image = pygame.image.load('sprites/menus/cover.png').convert()
            self.cover_image = pygame.transform.scale(self.cover_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        except FileNotFoundError:
            self.cover_image = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.cover_image.fill((0, 0, 0))
        
        try:
            self.font = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 25)
        except FileNotFoundError:
            self.font = pygame.font.SysFont('Courier New', 40, bold=True)
            
        try:
            self.select_sound = pygame.mixer.Sound("sfx/Select.wav")
        except:
            self.select_sound = None
            
        self.has_music = False
        try:
            pygame.mixer.music.load("sfx/songs/menu.WAV") 
            self.has_music = True
        except pygame.error:
            pass
            
        self.show_press_start = True
        self.blink_timer = 0
        
        self.fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.fade_surface.fill((0, 0, 0))  
        self.fade_alpha = 255              
        self.fading_in = True              
        self.fading_out = False
        
        self.fade_in_speed = 255 / 3000   
        self.fade_out_speed = 255 / 1000   

    def draw_cover_text(self, text, color, x, y):
        text_surface = self.font.render(text, True, color)
        outline_surface = self.font.render(text, True, (0, 0, 0))
        rect = text_surface.get_rect(center=(x, y))
        
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx != 0 or dy != 0:
                    self.screen.blit(outline_surface, (rect.x + dx, rect.y + dy))
        self.screen.blit(text_surface, rect)

    def run(self):
        if self.has_music:
            pygame.mixer.music.play(loops=-1, fade_ms=3000)

        running = True
        while running:
            dt = self.clock.tick(60) 
            
            if self.fading_in:
                self.fade_alpha -= self.fade_in_speed * dt
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.fading_in = False 
            elif self.fading_out:
                self.fade_alpha += self.fade_out_speed * dt
                if self.fade_alpha >= 255:
                    self.fade_alpha = 255
                    running = False 

            self.blink_timer += dt
            limite_piscar = 70 if self.fading_out else 500
            if self.blink_timer >= limite_piscar:
                self.show_press_start = not self.show_press_start
                self.blink_timer = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and not self.fading_in and not self.fading_out:
                        if self.select_sound:
                            self.select_sound.play()
                        self.fading_out = True 
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

            self.screen.blit(self.cover_image, (0, 0))
            if self.show_press_start:
                self.draw_cover_text("PRESS START", (255, 255, 255), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

            if self.fade_alpha > 0:
                self.fade_surface.set_alpha(int(self.fade_alpha))
                self.screen.blit(self.fade_surface, (0, 0))

            pygame.display.update()

class CarSelectMenu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        # Carrega as fontes
        try:
            self.hudFont = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 20)
            self.lapFont = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 30)
        except FileNotFoundError:
            self.hudFont = pygame.font.SysFont('Courier New', 24, bold=True)
            self.lapFont = pygame.font.SysFont('Courier New', 34, bold=True)
            
        # Carrega o novo Background
        try:
            self.bg_image = pygame.image.load('sprites/menus/carSelect.png').convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        except FileNotFoundError:
            print("Aviso: Imagem carSelect.png não encontrada.")
            self.bg_image = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.bg_image.fill((0, 0, 0))

        self.carModels = ['288GTO', 'Testarossa', 'XJR15', '959']
        
        # --- EFEITOS SONOROS ---
        try:
            self.select_sound = pygame.mixer.Sound("sfx/Select.wav")
        except:
            self.select_sound = None

        self.select_sound.set_volume(0.5)
            
        try:
            # Novo som para a navegação (esq/dir)
            self.nav_sound = pygame.mixer.Sound("sfx/Ready.wav") 
        except:
            self.nav_sound = None

        self.nav_sound.set_volume(0.5)

        # --- SISTEMA DE FADE ---
        self.fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.fade_surface.fill((0, 0, 0))
        self.fade_alpha = 255              # Começa tudo preto
        self.fading_in = True              
        self.fading_out = False
        
        # Como é um menu do meio do jogo, coloquei 1 segundo (1000ms) para entrar e sair mais dinâmico
        self.fade_in_speed = 255 / 2000    
        self.fade_out_speed = 255 / 1000   

    def run(self):
        selected = 0
        posicoes_x = [132, 383, 643, 895]
        running = True
        
        while running:
            # Trocamos para 60 ticks para o fade ficar fluido
            dt = self.clock.tick(60) 
            
            # --- LÓGICA DO FADE ---
            if self.fading_in:
                self.fade_alpha -= self.fade_in_speed * dt
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.fading_in = False 
            elif self.fading_out:
                self.fade_alpha += self.fade_out_speed * dt
                if self.fade_alpha >= 255:
                    self.fade_alpha = 255
                    running = False # Encerra o loop e avança para a próxima tela!

            # --- EVENTOS ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    # Trava a navegação se estiver no meio do fade
                    if not self.fading_in and not self.fading_out:
                        if event.key == pygame.K_LEFT:
                            selected = (selected - 1) % len(self.carModels)
                            # Toca o som de navegação ao mover!
                            if self.nav_sound: self.nav_sound.play()
                        elif event.key == pygame.K_RIGHT:
                            selected = (selected + 1) % len(self.carModels)
                            if self.nav_sound: self.nav_sound.play()
                        elif event.key == pygame.K_RETURN:
                            if self.select_sound: self.select_sound.play()
                            # Em vez de retornar, iniciamos o fade out
                            self.fading_out = True 
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()

            # --- DESENHO ---
            self.screen.blit(self.bg_image, (0, 0))
            
            draw_menu_text(self.screen, "SELECT YOUR CAR", self.lapFont, (255, 255, 255), WINDOW_WIDTH // 2, 66, "center")

            for i, model in enumerate(self.carModels):
                color = (255, 255, 50) if i == selected else (150, 150, 150)
                x_atual = posicoes_x[i]

                draw_menu_text(self.screen, model.upper(), self.hudFont, color, x_atual, 690, "center")
                
                if i == selected:
                    draw_menu_text(self.screen, "^", self.hudFont, (255, 255, 50), x_atual, 725, "center")

            # Desenha a película preta por cima de tudo
            if self.fade_alpha > 0:
                self.fade_surface.set_alpha(int(self.fade_alpha))
                self.screen.blit(self.fade_surface, (0, 0))

            pygame.display.update()

        # Só retorna a escolha depois que o laço principal fechar (depois do fade out)
        return self.carModels[selected]
    
class CarInfoMenu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        # Usamos uma fonte um pouco menor para caber a descrição
        try:
            self.font = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 16) 
        except FileNotFoundError:
            self.font = pygame.font.SysFont('Courier New', 16, bold=True)
            
        try:
            self.select_sound = pygame.mixer.Sound("sfx/Select.wav")
        except:
            self.select_sound = None

        # Textos da história de cada carro (\n serve para quebrar a linha)
        self.lore = {                                                                                                     
            '288GTO': "FERRARI 288 GTO\n\nO pioneiro dos hipercarros. Um monstro V8 biturbo de\n2.8 Litros, nasceu para correr no lendario Grupo B.",
            '959': "PORSCHE 959\n\nA Maravilha tecnologica dos anos 80. Com um motor boxer\nde 2.8 Litros biturbo e tracao integral.",
            'Testarossa': "FERRARI TESTAROSSA\n\nO icone definitivo do Retro-Wave. Design inconfundivel e\nmotor flat-12 de 4.9 Litros com alma Italiana.",
            'XJR15': "JAGUAR XJR-15\n\nUm carro de corrida para as ruas. Carroceria de fibra\nde carbono e um V12 de 6.0 Litros de competicao."
        }

    def run(self, model):
        # Tenta carregar a imagem com o mesmo nome do modelo (ex: 959.png)
        try:
            bg_image = pygame.image.load(f'sprites/menus/{model}.png').convert()
            bg_image = pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        except FileNotFoundError:
            print(f"Aviso: Imagem sprites/menus/{model}.png nao encontrada.")
            bg_image = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            bg_image.fill((20, 20, 20))

        full_text = self.lore.get(model, "Informacao nao encontrada.")
        
        # Variáveis do efeito Máquina de Escrever
        char_index = 0
        text_timer = 0
        text_speed = 30 # Velocidade (milissegundos por letra)
        text_finished = False
        
        # Variáveis da Seta Piscante
        blink_timer = 0
        show_arrow = True

        running = True
        while running:
            dt = self.clock.tick(60)

            # --- LÓGICA DA MÁQUINA DE ESCREVER ---
            if not text_finished:
                text_timer += dt
                if text_timer > text_speed:
                    char_index += 1
                    text_timer = 0
                    if char_index >= len(full_text):
                        char_index = len(full_text)
                        text_finished = True
            
            # --- LÓGICA DA SETA PISCANDO ---
            if text_finished:
                blink_timer += dt
                if blink_timer > 400: # Pisca a cada 400ms
                    show_arrow = not show_arrow
                    blink_timer = 0

            # --- EVENTOS ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if not text_finished:
                            # Se o texto ainda estiver escrevendo, o ENTER pula a animação (mostra tudo)
                            char_index = len(full_text)
                            text_finished = True
                        else:
                            # Se o texto já acabou, o ENTER avança para a próxima tela
                            if self.select_sound: self.select_sound.play()
                            running = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

            # --- DESENHO ---
            self.screen.blit(bg_image, (0, 0))

            # 1. Configuração da Caixa de Texto (Fundo)
            box_width = WINDOW_WIDTH - 100
            box_height = 160
            box_x = 50
            box_y = WINDOW_HEIGHT - box_height - 30
            box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
            
            # 2. Desenha o Fundo Preto (com bordas arredondadas de 15px)
            pygame.draw.rect(self.screen, (0, 0, 0), box_rect, border_radius=15)
            
            # 3. Desenha a Borda Branca (width=3 faz ser apenas uma linha em vez de preencher)
            pygame.draw.rect(self.screen, (255, 255, 255), box_rect, width=3, border_radius=15)

            # 4. Renderiza o texto progressivo lidando com as quebras de linha (\n)
            current_text = full_text[:char_index]
            lines = current_text.split('\n')
            for i, line in enumerate(lines):
                # A altura de cada linha é multiplicada por 30 pixels para espaçamento
                text_surface = self.font.render(line, True, (255, 255, 255))
                self.screen.blit(text_surface, (box_x + 20, box_y + 20 + (i * 30)))

            # 5. Renderiza a seta piscando no canto inferior direito
            if text_finished and show_arrow:
                arrow_surface = self.font.render(">", True, (255, 255, 50)) # Seta amarela pra dar destaque
                self.screen.blit(arrow_surface, (box_x + box_width - 35, box_y + box_height - 35))

            pygame.display.update()

class TrackSelectMenu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        try:
            self.hudFont = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 20)
            self.lapFont = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 30)
        except FileNotFoundError:
            self.hudFont = pygame.font.SysFont('Courier New', 24, bold=True)
            self.lapFont = pygame.font.SysFont('Courier New', 34, bold=True)
            
        try:
            self.select_sound = pygame.mixer.Sound("sfx/Select.wav")
        except:
            self.select_sound = None

    def run(self):
        tracks = get_all_tracks()
        selected = 0
        while True:
            self.screen.fill((0, 0, 0))
            draw_menu_text(self.screen, "TRACK SELECT", self.lapFont, (255, 255, 255), WINDOW_WIDTH // 2, 100, "center")

            for i, track in enumerate(tracks):
                color = (255, 255, 50) if i == selected else (150, 150, 150)
                draw_menu_text(self.screen, track['name'].upper(), self.hudFont, color, WINDOW_WIDTH // 2, 280 + i * 80, "center")
                if i == selected:
                    draw_menu_text(self.screen, ">", self.hudFont, (255, 255, 50), WINDOW_WIDTH // 2 - 140, 280 + i * 80, "left")

            draw_menu_text(self.screen, "ENTER TO RACE", self.hudFont, (100, 100, 100), WINDOW_WIDTH // 2, WINDOW_HEIGHT - 80, "center")

            pygame.display.update()
            self.clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected = (selected - 1) % len(tracks)
                    elif event.key == pygame.K_DOWN:
                        selected = (selected + 1) % len(tracks)
                    elif event.key == pygame.K_RETURN:
                        if self.select_sound: self.select_sound.play()
                        return tracks[selected]['id']
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()