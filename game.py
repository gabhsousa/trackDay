import pygame
import sys
import os
import random

# Importações dos outros módulos
from config import *
from utils import drawQuad, drawStripedSky
from track import Track

class GameWindow:
    """
    Classe principal que gere o estado do jogo, o loop principal, 
    a renderização e a lógica da Inteligência Artificial (IA).
    """
    def __init__(self):
        # Inicialização da janela principal do Pygame
        self.windowSurface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("TrackDay")
        self.clock = pygame.time.Clock()
        
        # Configuração das fontes para o HUD
        pygame.font.init()
        self.hudFont = pygame.font.SysFont('Arial', 30, bold=True)
        self.lapFont = pygame.font.SysFont('Arial', 40, bold=True)
        
        # Configurações do motor de renderização pseudo-3D
        self.roadWidth = 2000
        self.segmentLength = 200
        self.cameraDepth = 0.84
        self.showSegments = 300
        
        self.track = Track(self.segmentLength)
        self._loadAssets()

    def _loadAssets(self):
        # --- CARREGAR FUNDO ---
        try:
            bgOriginal = pygame.image.load("sprites/bg/L1.png").convert_alpha()
            escala = 6
            novoW = bgOriginal.get_width() * escala
            novoH = bgOriginal.get_height() * escala
            self.backgroundImage = pygame.transform.scale(bgOriginal, (novoW, novoH))
        except FileNotFoundError:
            self.backgroundImage = pygame.Surface((WINDOW_WIDTH, 128), pygame.SRCALPHA)

        self.bgWidth = self.backgroundImage.get_width()
        bgHeight = self.backgroundImage.get_height()

        self.backgroundSurface = pygame.Surface((self.bgWidth * 3, bgHeight), pygame.SRCALPHA)
        self.backgroundSurface.blit(self.backgroundImage, (0, 0))
        self.backgroundSurface.blit(self.backgroundImage, (self.bgWidth, 0))
        self.backgroundSurface.blit(self.backgroundImage, (self.bgWidth * 2, 0))
        self.backgroundRect = self.backgroundSurface.get_rect(topleft=(-self.bgWidth, 0))
        self.bgOffsetX = 0.0

        # --- CARREGAR SPRITES DOS CARROS ---
        self.rawCarSprites = {}
        diretorioAtual = os.path.dirname(os.path.abspath(__file__))
        basePath = os.path.join(diretorioAtual, "sprites", "cars", "280GTO")

        try:
            self.rawCarSprites = {
                'S':  [pygame.image.load(os.path.join(basePath, 'S.png')).convert_alpha(),   pygame.image.load(os.path.join(basePath, 'S2.png')).convert_alpha()],
                'L':  [pygame.image.load(os.path.join(basePath, 'L.png')).convert_alpha(),   pygame.image.load(os.path.join(basePath, 'L2.png')).convert_alpha()],
                'SL': [pygame.image.load(os.path.join(basePath, 'SL.png')).convert_alpha(),  pygame.image.load(os.path.join(basePath, 'SL2.png')).convert_alpha()],
                'R':  [pygame.image.load(os.path.join(basePath, 'R.png')).convert_alpha(),   pygame.image.load(os.path.join(basePath, 'R2.png')).convert_alpha()],
                'SR': [pygame.image.load(os.path.join(basePath, 'SR.png')).convert_alpha(),  pygame.image.load(os.path.join(basePath, 'SR2.png')).convert_alpha()]
            }
        except FileNotFoundError:
            surface = pygame.Surface((150, 80))
            surface.fill((255, 0, 0))
            self.rawCarSprites = {k: [surface, surface] for k in ['S', 'L', 'SL', 'R', 'SR']}

        carTargetWidth = 300
        imagemReta = self.rawCarSprites['S'][0]
        fatorEscala = carTargetWidth / imagemReta.get_width()

        self.carSprites = {}
        for state, images in self.rawCarSprites.items():
            self.carSprites[state] = []
            for img in images:
                nW = int(img.get_width() * fatorEscala)
                nH = int(img.get_height() * fatorEscala)
                self.carSprites[state].append(pygame.transform.scale(img, (nW, nH)))

    def draw_hud(self, text, font, color, x, y, align="left"):
        """Função auxiliar para desenhar o texto com o fundo preto padronizado"""
        surface = font.render(text, True, color)
        rect = pygame.Rect(0, y - 5, surface.get_width() + 20, surface.get_height() + 10)
        
        if align == "left":
            rect.x = x - 10
            text_x = x
        elif align == "right":
            rect.right = x + 10
            text_x = x - surface.get_width()
        elif align == "center":
            rect.centerx = x
            text_x = x - surface.get_width() // 2
            
        pygame.draw.rect(self.windowSurface, (0, 0, 0), rect)
        self.windowSurface.blit(surface, (text_x, y))

    def run(self):
        self.track.buildTrack()
        lines = self.track.lines
        totalSegments = len(lines)
        trackLength = totalSegments * self.segmentLength

        # Variáveis de estado do Jogador e Corrida
        absolutePos = 0.0
        maxLaps = 5  # Alterado para 5 voltas
        playerX = 0.0
        playerY = 1250
        playerPitchBase = 150
        smoothPitch = 0.0
        
        speed = 0.0
        basePlayerMaxSpeed = 260 
        maxSpeed = basePlayerMaxSpeed
        draftBonus = 0.0
        
        animTimer = 0
        turnTimer = 0

        # Máquina de Estado da Corrida
        self.raceState = 'COUNTDOWN' # Pode ser 'COUNTDOWN', 'RACING', 'FINISHED'
        self.countdownStartTick = pygame.time.get_ticks()
        self.finishStartTick = 0
        countdown_text = None

        # --- INICIALIZAÇÃO DOS OPONENTES ---
        self.opponents = []
        for i in range(9):
            baseSpeed = 240 + (i * 3)
            start_z = (i + 1) * 1500.0
            self.opponents.append({
                'id': i, 
                'z': start_z,
                'totalZ': start_z, # Para calcular posições corretamente
                'x': (i % 3) * 1.2 - 1.2,
                'targetX': (i % 3) * 1.2 - 1.2,
                'speed': 0.0, 
                'baseMaxSpeed': baseSpeed, 
                'maxSpeed': baseSpeed,
                'decisionTimer': random.randint(0, 100),
                'lateralDelta': 0.0
            })

        # ==========================================
        # GAME LOOP PRINCIPAL
        # ==========================================
        while True:
            currentTick = pygame.time.get_ticks()
            
            for event in pygame.event.get([pygame.QUIT]):
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            keys = pygame.key.get_pressed()
            
            # Variáveis de comando que podemos manipular na Largada e no Autopilot
            cmd_up = keys[pygame.K_UP]
            cmd_down = keys[pygame.K_DOWN]
            cmd_left = keys[pygame.K_LEFT]
            cmd_right = keys[pygame.K_RIGHT]
            
            # Descobre em que parte do circuito o jogador está
            pos = absolutePos % trackLength 
            currentLap = int(absolutePos // trackLength) + 1

            startPos = int(pos // self.segmentLength)
            startSegment = lines[startPos % totalSegments]
            rawCurve = startSegment.curve
            absCurve = abs(rawCurve)
            
            # --- GESTÃO DE ESTADOS (LARGADA E FINAL) ---
            if self.raceState == 'COUNTDOWN':
                # Bloqueia os controles do jogador
                cmd_up = cmd_down = cmd_left = cmd_right = False
                
                elapsed = currentTick - self.countdownStartTick
                if elapsed < 1000: countdown_text = "3"
                elif elapsed < 2000: countdown_text = "2"
                elif elapsed < 3000: countdown_text = "1"
                elif elapsed < 4000: countdown_text = "GO!"
                else: 
                    self.raceState = 'RACING'
                    countdown_text = None
                    
            elif self.raceState == 'RACING':
                if currentLap > maxLaps:
                    self.raceState = 'FINISHED'
                    self.finishStartTick = currentTick
                    
            elif self.raceState == 'FINISHED':
                # Inteligência Artificial pilota o carro do jogador
                cmd_up = speed < 220
                cmd_down = speed > 220
                cmd_left = playerX > 0.1
                cmd_right = playerX < -0.1
                
                # Desliga após 5 segundos
                if currentTick - self.finishStartTick > 5000:
                    pygame.quit()
                    sys.exit()

            # --- SISTEMA DE VÁCUO (SLIPSTREAM) ---
            isDrafting = False
            playerVisualZ = 780
            playerVirtualZ = pos + playerVisualZ 

            if absCurve <= 2.0 and speed >= 240:
                for opp in self.opponents:
                    dz = opp['z'] - playerVirtualZ
                    if dz < 0: dz += trackLength 
                    if 50 < dz < 6000 and abs(opp['x'] - playerX) < 0.3:
                        isDrafting = True
                        break
            
            if isDrafting: draftBonus = min(10.0, draftBonus + 0.15)
            else: draftBonus = max(0.0, draftBonus - 0.10)
            maxSpeed = basePlayerMaxSpeed + draftBonus

            # --- FÍSICA: FORÇA CENTRÍFUGA ---
            trackDriftForce = (absCurve ** 0.6) * 0.015
            currentCentrifugal = trackDriftForce * (speed / maxSpeed)

            isOffroad = abs(playerX) > 2.3
            currentMaxSpeed = maxSpeed * 0.4 if isOffroad else maxSpeed

            # --- CONTROLOS (AFETADOS PELA IA NO FINISH) ---
            if cmd_up: speed += 3
            elif cmd_down: speed -= 8
            else:
                if speed > 0: speed -= 2
                elif speed < 0: speed += 2

            steerState = 'S'
            baseSteer = 0.045
            steerCap = 0.09
            steerAmount = 0.0
            isTurning = False

            if cmd_left and speed > 0:
                isTurning = True
                if rawCurve < -1.0: steerAmount = min(max(baseSteer * 0.6, currentCentrifugal + 0.002), steerCap)
                else: steerAmount = baseSteer
                playerX -= steerAmount
                turnTimer = max(0, turnTimer) + 1 
                steerState = 'L' if turnTimer > 5 else 'SL'
                    
            elif cmd_right and speed > 0:
                isTurning = True
                if rawCurve > 1.0: steerAmount = min(max(baseSteer * 0.6, currentCentrifugal + 0.002), steerCap)
                else: steerAmount = baseSteer
                playerX += steerAmount
                turnTimer = min(0, turnTimer) - 1 
                steerState = 'R' if turnTimer < -5 else 'SR'
            else:
                turnTimer = 0 

            trackDrift = currentCentrifugal if rawCurve > 0 else (-currentCentrifugal if rawCurve < 0 else 0.0)
            playerX -= trackDrift

            if isOffroad and speed > currentMaxSpeed: speed -= 6 
            if isTurning and trackDriftForce > 0.015:
                targetSpeed = currentMaxSpeed - (trackDriftForce * 900)
                if speed > targetSpeed: speed -= 5.0

            playerX = max(-5.0, min(playerX, 5.0))
            
            # ==========================================
            # INTELIGÊNCIA ARTIFICIAL (BOTS)
            # ==========================================
            for opp in self.opponents:
                if self.raceState == 'COUNTDOWN':
                    opp['speed'] = 0
                    opp['lateralDelta'] = 0.0
                else:
                    distFromPlayer = opp['z'] - pos
                    if distFromPlayer > trackLength / 2: distFromPlayer -= trackLength
                    elif distFromPlayer < -trackLength / 2: distFromPlayer += trackLength
                    
                    if distFromPlayer < -10000: opp['maxSpeed'] = opp['baseMaxSpeed'] + 6
                    elif distFromPlayer > 1200: opp['maxSpeed'] = opp['baseMaxSpeed'] - 3
                    else: opp['maxSpeed'] = opp['baseMaxSpeed']

                    if opp['speed'] < opp['maxSpeed']: opp['speed'] += 2.5
                    elif opp['speed'] > opp['maxSpeed']: opp['speed'] -= 1.0 
                
                    oppSeg = lines[int(opp['z'] // self.segmentLength) % totalSegments]
                    oppCurve = oppSeg.curve
                    oppAbsCurve = abs(oppCurve)
                    
                    opp['decisionTimer'] -= 1
                    if opp['decisionTimer'] <= 0:
                        opp['decisionTimer'] = random.randint(60, 120)
                        if oppAbsCurve < 0.5: opp['targetX'] = random.choice([-1.2, -0.6, 0.0, 0.6, 1.2])
                    
                    for other in self.opponents:
                        if other is opp: continue 
                        distZ = other['z'] - opp['z']
                        if distZ < 0: distZ += trackLength 
                        
                        if 0 < distZ < 400 and abs(other['x'] - opp['x']) < 0.8: 
                            opp['targetX'] = 1.2 if opp['x'] >= other['x'] else -1.2
                            if distZ < 150 and opp['speed'] > other['speed'] and abs(other['x'] - opp['x']) < 0.4:
                                opp['speed'] = other['speed']

                    distToPlayer = playerVirtualZ - opp['z']
                    if distToPlayer > trackLength / 2: distToPlayer -= trackLength
                    elif distToPlayer < -trackLength / 2: distToPlayer += trackLength
                    
                    if -400 < distToPlayer < 800 and abs(playerX - opp['x']) < 0.9: 
                        opp['targetX'] = 1.2 if opp['x'] >= playerX else -1.2
                        if 0 < distToPlayer < 100 and opp['speed'] > speed and abs(playerX - opp['x']) < 0.4:
                            opp['speed'] = speed 
                    
                    oppDriftForce = 0.0
                    isOppTurning = False
                    oppCentrifugal = 0.0
                    lateralDelta = 0.0 
                    
                    if oppAbsCurve > 0:
                        oppDriftForce = (oppAbsCurve ** 0.6) * 0.015
                        oppCentrifugal = oppDriftForce * (opp['speed'] / maxSpeed) if maxSpeed > 0 else 0
                        opp['x'] += oppCentrifugal if oppCurve < 0 else -oppCentrifugal

                    dynamicBotSteer = max(0.04, oppCentrifugal + 0.015) 
                    
                    if opp['x'] < opp['targetX']:
                        step = min(dynamicBotSteer, opp['targetX'] - opp['x'])
                        opp['x'] += step
                        lateralDelta = step 
                        isOppTurning = True
                    elif opp['x'] > opp['targetX']:
                        step = min(dynamicBotSteer, opp['x'] - opp['targetX'])
                        opp['x'] -= step
                        lateralDelta = -step 
                        isOppTurning = True

                    opp['lateralDelta'] = lateralDelta 
                        
                    if isOppTurning and oppDriftForce > 0.015:
                        targetOppSpeed = opp['maxSpeed'] - (oppDriftForce * 850)
                        if opp['speed'] > targetOppSpeed: opp['speed'] -= 4.5

                    opp['x'] = max(-1.8, min(opp['x'], 1.8))
                
                opp['z'] = (opp['z'] + opp['speed']) % trackLength
                opp['totalZ'] += opp['speed']
                dzOpp = opp['z'] - pos
                if dzOpp < 0: dzOpp += trackLength 
                opp['dz'] = dzOpp 
                
                if self.raceState != 'COUNTDOWN':
                    if playerVisualZ < dzOpp < playerVisualZ + 400 and abs(playerX - opp['x']) < 0.50:
                        speed *= 0.3

            speed = max(0, min(speed, currentMaxSpeed))
            absolutePos += speed
            pos = absolutePos % trackLength 

            self.opponents.sort(key=lambda o: o['dz'], reverse=True)

            # Câmera
            lookahead = 3
            segmentoFrente = (startPos + lookahead) % totalSegments
            dy = lines[segmentoFrente].y - lines[startPos].y
            pitchAlvo = playerPitchBase + (-dy * 0.5)
            smoothPitch += (pitchAlvo - smoothPitch) * 0.1 

            camHeight = lines[startPos].y + playerY
            maxY = WINDOW_HEIGHT

            self.bgOffsetX += rawCurve * speed * 0.0005
            self.backgroundRect.x = -(int(self.bgOffsetX) % self.bgWidth)

            farNode = startPos + self.showSegments - 1
            farLine = lines[farNode % totalSegments]
            farCamZ = pos - (totalSegments * self.segmentLength if farNode >= totalSegments else 0)
            
            if farLine.z - farCamZ > 0.1:
                farScale = self.cameraDepth / (farLine.z - farCamZ)
                farY = ((1 - farScale * (farLine.y - camHeight)) * WINDOW_HEIGHT / 2) - smoothPitch
            else:
                farY = WINDOW_HEIGHT / 2
            
            drawStripedSky(self.windowSurface, SKY_COLOR_TOP, SKY_COLOR_BOTTOM, SKY_BAND_HEIGHT, farY)
            self.backgroundRect.bottom = int(farY) + 1 
            self.windowSurface.blit(self.backgroundSurface, self.backgroundRect)

            worldX = 0.0  
            dx = 0.0  
            playerXWorld = playerX * 1000

            # --- RENDERIZAÇÃO DA PISTA ---
            for n in range(startPos, startPos + self.showSegments):
                currentLine = lines[n % totalSegments]
                currentLine.project(playerXWorld - worldX, camHeight, pos - (totalSegments * self.segmentLength if n >= totalSegments else 0), smoothPitch, self.cameraDepth, self.roadWidth)
                
                worldX += dx
                dx += currentLine.curve
                currentLine.clip = maxY 

                if currentLine.Y >= maxY: continue 
                maxY = currentLine.Y
                prevLine = lines[(n - 1) % totalSegments]  

                drawQuad(self.windowSurface, currentLine.grassColor, 0, prevLine.Y, WINDOW_WIDTH, 0, currentLine.Y, WINDOW_WIDTH)
                drawQuad(self.windowSurface, currentLine.rumbleColor, prevLine.X, prevLine.Y, prevLine.W * 1.2, currentLine.X, currentLine.Y, currentLine.W * 1.2)
                drawQuad(self.windowSurface, currentLine.roadColor, prevLine.X, prevLine.Y, prevLine.W, currentLine.X, currentLine.Y, currentLine.W)

            # --- RENDERIZAÇÃO DOS OPONENTES ---
            for opp in self.opponents:
                dz = opp['dz']
                if 0 < dz < (self.showSegments - 2) * self.segmentLength:
                    segIdx = int(opp['z'] // self.segmentLength) % totalSegments
                    
                    line1 = lines[segIdx]
                    line2 = lines[(segIdx + 1) % totalSegments]
                    
                    if line1.scale == 0 or line2.scale == 0: continue
                    
                    percent = (opp['z'] % self.segmentLength) / self.segmentLength
                    destX = line1.X + (line2.X - line1.X) * percent
                    destY = line1.Y + (line2.Y - line1.Y) * percent
                    destW = line1.W + (line2.W - line1.W) * percent
                    
                    baseTargetW = destW * 0.28
                    baseSpriteW = self.rawCarSprites['S'][0].get_width()
                    escalaDistancia = baseTargetW / baseSpriteW

                    turnForce = line1.curve + (opp.get('lateralDelta', 0.0) * 80.0)
                    oppSteer = 'S'
                    
                    if turnForce < -1.0: oppSteer = 'L' if turnForce < -3.0 else 'SL'
                    elif turnForce > 1.0: oppSteer = 'R' if turnForce > 3.0 else 'SR'
                    
                    oppFrame = 0 if (int(opp['z']) % 400) < 200 else 1
                    currentOppSprite = self.rawCarSprites[oppSteer][oppFrame]
                    
                    finalW = currentOppSprite.get_width() * escalaDistancia
                    finalH = currentOppSprite.get_height() * escalaDistancia
                    oppBounce = (baseTargetW * 0.02) if (opp['speed'] > 0 and (int(opp['z']) % 300) < 150) else 0
                    
                    renderX = destX + (opp['x'] * destW * 0.5) - (finalW / 2)
                    renderY = destY - finalH - oppBounce 
                    
                    clipH = renderY + finalH - line1.clip
                    if clipH < 0: clipH = 0
                    if clipH >= finalH: continue 
                    if finalW > WINDOW_WIDTH * 1.5 or finalW <= 0 or finalH <= 0: continue 
                    
                    try:
                        scaledSprite = pygame.transform.scale(currentOppSprite, (int(finalW), int(finalH)))
                        cropSurface = scaledSprite.subsurface(0, 0, int(finalW), int(finalH - clipH))
                        self.windowSurface.blit(cropSurface, (int(renderX), int(renderY)))
                    except ValueError:
                        pass 

            # --- RENDERIZAÇÃO DO JOGADOR ---
            if speed > 0: animTimer = (animTimer + speed) % 1500
            
            animFrame = 0 if animTimer < 750 else 1  
            carImage = self.carSprites[steerState][animFrame]
            carRect = carImage.get_rect()
            
            bounceOffset = 0
            if speed > 0:
                bounceOffset = 2 if (int(pos) % 400) < 200 else 0
                if isOffroad: bounceOffset *= 3 
                    
            carRect.centerx = WINDOW_WIDTH // 2 
            carRect.bottom = (WINDOW_HEIGHT - 30) - bounceOffset
            self.windowSurface.blit(carImage, carRect)

            # ==========================================
            # UI (HUD - INTERFACE DO UTILIZADOR)
            # ==========================================
            # 1. Velocímetro
            speedColor = (0, 255, 255) if draftBonus > 0.5 else (255, 255, 255)
            self.draw_hud(f"{int(speed)} KM/H", self.hudFont, speedColor, 25, 20, "left")
            
            # 2. Voltas
            displayLap = min(currentLap, maxLaps)
            self.draw_hud(f"LAP {displayLap}/{maxLaps}", self.lapFont, (255, 200, 0), WINDOW_WIDTH - 25, 20, "right")
            
            # 3. Posição (Cálculo via Distância Total Absoluta)
            distances = [absolutePos] + [o['totalZ'] for o in self.opponents]
            distances.sort(reverse=True)
            player_pos = distances.index(absolutePos) + 1
            
            sufixos = {1: "ST", 2: "ND", 3: "RD"}
            pos_suffix = sufixos.get(player_pos, "TH")
            self.draw_hud(f"POS {player_pos}{pos_suffix}", self.lapFont, (255, 255, 255), WINDOW_WIDTH - 25, 75, "right")

            # 4. Mensagens Centrais
            if self.raceState == 'COUNTDOWN' and countdown_text:
                cor_timer = (255, 0, 0) if countdown_text != "GO!" else (0, 255, 0)
                self.draw_hud(countdown_text, self.lapFont, cor_timer, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50, "center")

            if self.raceState == 'FINISHED':
                self.draw_hud("FINISH!", self.lapFont, (0, 255, 0), WINDOW_WIDTH // 2, 100, "center")
                self.draw_hud("AUTOPILOT ENGAGED", self.hudFont, (200, 200, 200), WINDOW_WIDTH // 2, 160, "center")

            pygame.display.update()
            self.clock.tick(60)