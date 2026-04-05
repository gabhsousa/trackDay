import pygame
import sys
from config import WINDOW_WIDTH, WINDOW_HEIGHT

# Função auxiliar para textos (mantida para compatibilidade)
def draw_menu_text(surface, text, font, color, x, y, align="left"):
    surface_color = font.render(text, True, color)
    surface_outline = font.render(text, True, (0, 0, 0)) 
    rect = surface_color.get_rect()
    if align == "left": rect.x = x
    elif align == "right": rect.right = x
    elif align == "center": rect.centerx = x
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
        
        try:
            self.font = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 25)
        except:
            self.font = pygame.font.SysFont('Courier New', 40, bold=True)
            
        try: self.select_sound = pygame.mixer.Sound("sfx/Select.wav")
        except: self.select_sound = None
            
        self.fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.fade_surface.fill((0, 0, 0))
        self.fade_alpha = 255
        self.fading_in = True
        self.fading_out = False
        self.show_press_start = True
        self.blink_timer = 0

    def run(self):
        self.fade_alpha = 255
        self.fading_in = True
        self.fading_out = False
        self.clock.tick()
        
        running = True
        while running:
            dt = self.clock.tick(60)
            if self.fading_in:
                self.fade_alpha -= (255/3000) * dt # Fade in de 3s
                if self.fade_alpha <= 0: self.fade_alpha = 0; self.fading_in = False
            elif self.fading_out:
                self.fade_alpha += (255/1000) * dt # Fade out de 1s
                if self.fade_alpha >= 255: self.fade_alpha = 255; running = False

            self.blink_timer += dt
            if self.blink_timer >= (70 if self.fading_out else 500):
                self.show_press_start = not self.show_press_start
                self.blink_timer = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and not self.fading_in and not self.fading_out:
                    if event.key == pygame.K_RETURN:
                        if self.select_sound: self.select_sound.play()
                        self.fading_out = True

            self.screen.blit(self.cover_image, (0, 0))
            if self.show_press_start:
                txt = self.font.render("PRESS START", True, (255, 255, 255))
                rect = txt.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
                self.screen.blit(txt, rect)
            
            if self.fade_alpha > 0:
                self.fade_surface.set_alpha(int(self.fade_alpha))
                self.screen.blit(self.fade_surface, (0, 0))
            pygame.display.update()

class CarSelectMenu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        try:
            self.hudFont = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 20)
            self.lapFont = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 30)
        except:
            self.hudFont = pygame.font.SysFont('Arial', 20); self.lapFont = pygame.font.SysFont('Arial', 30)
        
        try: self.bg_image = pygame.image.load('sprites/menus/carSelect.png').convert()
        except: self.bg_image = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        
        self.carModels = ['288GTO', 'Testarossa', 'XJR15', '959']
        try: self.nav_sound = pygame.mixer.Sound("sfx/Ready.wav"); self.sel_sound = pygame.mixer.Sound("sfx/Select.wav")
        except: self.nav_sound = self.sel_sound = None

        self.fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.fade_surface.fill((0, 0, 0))
        self.fade_alpha = 255
        self.fading_in = True
        self.fading_out = False

    def run(self):
        self.fade_alpha = 255
        self.fading_in = True
        self.fading_out = False
        self.clock.tick()

        selected = 0
        pos_x = [132, 383, 643, 895]
        running = True
        while running:
            dt = self.clock.tick(60)
            if self.fading_in:
                self.fade_alpha -= (255/1000) * dt
                if self.fade_alpha <= 0: self.fade_alpha = 0; self.fading_in = False
            elif self.fading_out:
                self.fade_alpha += (255/1000) * dt
                if self.fade_alpha >= 255: self.fade_alpha = 255; running = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and not self.fading_in and not self.fading_out:
                    if event.key == pygame.K_LEFT:
                        selected = (selected - 1) % 4
                        if self.nav_sound: self.nav_sound.play()
                    elif event.key == pygame.K_RIGHT:
                        selected = (selected + 1) % 4
                        if self.nav_sound: self.nav_sound.play()
                    elif event.key == pygame.K_RETURN:
                        if self.sel_sound: self.sel_sound.play()
                        self.fading_out = True

            self.screen.blit(pygame.transform.scale(self.bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT)), (0, 0))
            draw_menu_text(self.screen, "CHOOSE YOUR CAR", self.lapFont, (255,255,255), WINDOW_WIDTH//2, 66, "center")
            for i, model in enumerate(self.carModels):
                color = (255,255,50) if i == selected else (150,150,150)
                draw_menu_text(self.screen, model, self.hudFont, color, pos_x[i], 690, "center")
                if i == selected: draw_menu_text(self.screen, "^", self.hudFont, (255,255,50), pos_x[i], 725, "center")

            if self.fade_alpha > 0:
                self.fade_surface.set_alpha(int(self.fade_alpha))
                self.screen.blit(self.fade_surface, (0,0))
            pygame.display.update()
        return self.carModels[selected]

class LoreMenu:
    """Classe base para informações de Carro e Pista com caixa de texto e fade"""
    def __init__(self, screen, is_track=False):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.is_track = is_track
        try: self.font = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 16)
        except: self.font = pygame.font.SysFont('Arial', 16)
        try: self.sel_sound = pygame.mixer.Sound("sfx/Select.wav")
        except: self.sel_sound = None

        self.lore_data = {
            '288GTO': "FERRARI 288 GTO\n\nA pioneira dos hipercarros. Um monstro V8 biturbo de\n2.8 Litros, nasceu para correr no lendario Grupo B,\ncategoria encerrada antes mesmo da estreira da 288.",
            '959': "PORSCHE 959\n\nA Maravilha tecnologica dos anos 80. Com um motor boxer\nde 2.8 Litros biturbo e tracao integral. Nasceu tambem\npara o Grupo B, mas virou um icone tecnologico de rua",
            'Testarossa': "FERRARI TESTAROSSA\n\nO icone definitivo do Retro-Wave. Design inconfundivel e\nmotor V12 de 4.9 Litros carregando a alma Italiana. Foi\nlancada em 1984, um simbolo de luxo e esportividade.",
            'XJR15': "JAGUAR XJR-15\n\nUm carro de corrida para as ruas. Carroceria de fibra\nde carbono e um V12 de 6.0 Litros de competicao. Fazem\ndo XJR-15 um dos supercarros mais raros que existem.",
            'ITA': "AUTODROMO DI MONZA\n\nNossa primeira parada, o Templo da Velocidade. Esse\ncircuito centenário com 5.7km de extensao conta com\nlongas retas e chicanes desafiadoras. Aqui, o vacuo\nsera seu melhor amigo para alcancar os lideres. Mas\ntome muito cuidado com a lendaria chicane Ascari.",
            'AUS': "RED BULL RING\n\nEstamos nas montanhas da Austria, casa do lendario Niki\nLauda. As subidas e descidas extremas do Red Bull Ring\nexigem muita coragem e velocidade. A dinamica peculiar\ndesse circuito faz o piloto prestar muita atencao com\ncolisoes. Nunca subestime a sua simplicidade.",
            'BRA': "AUTODROMO DE INTERLAGOS\n\nNossa ultima parada, o Autodromo de Interlagos. Sua\nultima grande reforma contou com consultoria de Ayrton\nSenna. Em 1991, Senna venceu seu primeiro Grande Premio\ndo Brasil nesse solo sagrado, tome bastante cuidado com\na subida do lago e aproveite o vacuo nas longas retas!"
        }
        
    def run(self, obj_id):
        img_id = {'ITA':'MON'}.get(obj_id, obj_id)
        try:
            bg = pygame.image.load(f'sprites/menus/{img_id}.png').convert()
            bg = pygame.transform.scale(bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
        except:
            bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT)); bg.fill((20,20,20))

        text = self.lore_data.get(obj_id, "")
        char_idx = 0; timer = 0; finished = False; alpha = 255; f_out = False
        fade_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT)); fade_surf.fill((0,0,0))

        # 1. Limpa o tempo acumulado de carregamento da imagem antes do loop!
        self.clock.tick() 

        while True:
            dt = self.clock.tick(60)
            
            # 2. Trava de segurança: se o PC engasgar, o dt não passa de 50ms
            if dt > 50: dt = 50 
            
            if not f_out:
                alpha = max(0, alpha - (255/1000) * dt)
                if alpha == 0 and not finished:
                    timer += dt
                    if timer > 30: char_idx += 1; timer = 0
                    if char_idx >= len(text): finished = True
            else:
                alpha += (255/1000) * dt
                if alpha >= 255: return

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and alpha < 50:
                    if event.key == pygame.K_RETURN:
                        if not finished: char_idx = len(text); finished = True
                        else: 
                            if self.sel_sound: self.sel_sound.play()
                            f_out = True

            self.screen.blit(bg, (0,0))
            
            h = 220 if self.is_track else 160
            box = pygame.Rect(50, WINDOW_HEIGHT - h - 30, WINDOW_WIDTH - 100, h)
            pygame.draw.rect(self.screen, (0,0,0), box, border_radius=15)
            pygame.draw.rect(self.screen, (255,255,255), box, width=3, border_radius=15)

            lines = text[:char_idx].split('\n')
            for i, line in enumerate(lines):
                self.screen.blit(self.font.render(line, True, (255,255,255)), (box.x+20, box.y+20+(i*25)))
            
            if finished and (pygame.time.get_ticks() // 400) % 2:
                self.screen.blit(self.font.render(">", True, (255,255,50)), (box.right-30, box.bottom-30))

            if alpha > 0:
                fade_surf.set_alpha(int(alpha)); self.screen.blit(fade_surf, (0,0))
            pygame.display.update()

# Aliases mantidos
CarInfoMenu = LoreMenu
TrackInfoMenu = lambda screen: LoreMenu(screen, is_track=True)