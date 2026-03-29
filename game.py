import pygame
import sys
import os
import random

# Importações dos outros módulos do nosso projeto multi-ficheiro
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
        pygame.display.set_caption("TrackDay - Arcade Bots com Efeito Estilingue")
        self.clock = pygame.time.Clock() # Utilizado para trancar os FPS
        
        # Configuração das fontes para o HUD (Velocidade, Voltas, etc.)
        pygame.font.init()
        self.hudFont = pygame.font.SysFont('Arial', 30, bold=True)
        self.lapFont = pygame.font.SysFont('Arial', 40, bold=True)
        
        # Configurações do motor de renderização pseudo-3D
        self.roadWidth = 2000     # Largura virtual da pista
        self.segmentLength = 200  # Comprimento de cada segmento da pista
        self.cameraDepth = 0.84   # Profundidade da câmara (Aprofunda o FoV/Campo de Visão)
        self.showSegments = 300   # Quantos segmentos desenhar à frente do jogador (Draw Distance)
        
        # Instancia a pista num objeto separado (lógica importada de track.py)
        self.track = Track(self.segmentLength)

        # Carrega todas as imagens e sprites necessários para a memória
        self._loadAssets()

    def _loadAssets(self):
        """
        Carrega e prepara os recursos visuais (fundo e sprites dos carros).
        """
        # --- CARREGAR FUNDO (CÉU E MONTANHAS) ---
        try:
            bgOriginal = pygame.image.load("sprites/bg/L1.png").convert_alpha()
            escala = 6
            novoW = bgOriginal.get_width() * escala
            novoH = bgOriginal.get_height() * escala
            self.backgroundImage = pygame.transform.scale(bgOriginal, (novoW, novoH))
        except FileNotFoundError:
            # Fallback caso a imagem não exista
            self.backgroundImage = pygame.Surface((WINDOW_WIDTH, 128), pygame.SRCALPHA)

        self.bgWidth = self.backgroundImage.get_width()
        bgHeight = self.backgroundImage.get_height()

        # Criamos uma superfície tripla para o fundo para fazer o efeito de "parallax" (scroll infinito)
        self.backgroundSurface = pygame.Surface((self.bgWidth * 3, bgHeight), pygame.SRCALPHA)
        self.backgroundSurface.blit(self.backgroundImage, (0, 0))
        self.backgroundSurface.blit(self.backgroundImage, (self.bgWidth, 0))
        self.backgroundSurface.blit(self.backgroundImage, (self.bgWidth * 2, 0))
        self.backgroundRect = self.backgroundSurface.get_rect(topleft=(-self.bgWidth, 0))
        self.bgOffsetX = 0.0 # Controla o deslocamento horizontal do fundo

        # --- CARREGAR SPRITES DO JOGADOR E BOTS ---
        self.rawCarSprites = {}
        diretorioAtual = os.path.dirname(os.path.abspath(__file__))
        basePath = os.path.join(diretorioAtual, "sprites", "cars", "280GTO")

        try:
            # Carrega os sprites base para as 5 direções (S=Straight, L=Left, R=Right)
            # Cada direção tem 2 frames para a animação da roda
            self.rawCarSprites = {
                'S':  [pygame.image.load(os.path.join(basePath, 'S.png')).convert_alpha(),   pygame.image.load(os.path.join(basePath, 'S2.png')).convert_alpha()],
                'L':  [pygame.image.load(os.path.join(basePath, 'L.png')).convert_alpha(),   pygame.image.load(os.path.join(basePath, 'L2.png')).convert_alpha()],
                'SL': [pygame.image.load(os.path.join(basePath, 'SL.png')).convert_alpha(),  pygame.image.load(os.path.join(basePath, 'SL2.png')).convert_alpha()],
                'R':  [pygame.image.load(os.path.join(basePath, 'R.png')).convert_alpha(),   pygame.image.load(os.path.join(basePath, 'R2.png')).convert_alpha()],
                'SR': [pygame.image.load(os.path.join(basePath, 'SR.png')).convert_alpha(),  pygame.image.load(os.path.join(basePath, 'SR2.png')).convert_alpha()]
            }
        except FileNotFoundError:
            # Fallback (retângulo vermelho) se faltarem ficheiros
            surface = pygame.Surface((150, 80))
            surface.fill((255, 0, 0))
            self.rawCarSprites = {k: [surface, surface] for k in ['S', 'L', 'SL', 'R', 'SR']}

        # Prepara os sprites redimensionados específicos para o jogador (escala fixa)
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

    def run(self):
        """
        O Loop principal do jogo. Contém a física, a IA e a renderização frame a frame.
        """
        # Constrói o traçado matemático da pista
        self.track.buildTrack()
        lines = self.track.lines
        totalSegments = len(lines)
        trackLength = totalSegments * self.segmentLength # Comprimento total da volta

        # Variáveis de estado do Jogador
        absolutePos = 0.0     # Posição global no circuito em Z
        maxLaps = 3           # Número de voltas da corrida
        playerX = 0.0         # Posição horizontal do jogador (-1 a 1 é a pista)
        playerY = 1250        # Altura da câmara
        playerPitchBase = 150 # Inclinação base da câmara
        smoothPitch = 0.0     # Usado para suavizar o movimento de subida/descida (colinas)
        
        # Variáveis de Velocidade
        speed = 0.0
        basePlayerMaxSpeed = 260 
        maxSpeed = basePlayerMaxSpeed
        draftBonus = 0.0      # Bónus ganho por ir no vácuo de outro carro
        
        # Timers para animação
        animTimer = 0
        turnTimer = 0

        # --- INICIALIZAÇÃO DOS OPONENTES (BOTS) ---
        self.opponents = []
        for i in range(9):
            baseSpeed = 240 + (i * 3) # Cada bot tem uma velocidade ligeiramente diferente
            self.opponents.append({
                'id': i, 
                'z': (i + 1) * 1500.0,            # Posição inicial no circuito
                'x': (i % 3) * 1.2 - 1.2,         # Espalhados por 3 faixas (-1.2, 0.0, 1.2)
                'targetX': (i % 3) * 1.2 - 1.2,   # Faixa para onde o bot quer ir
                'speed': 0.0, 
                'baseMaxSpeed': baseSpeed, 
                'maxSpeed': baseSpeed,
                'decisionTimer': random.randint(0, 100), # Timer para mudar de faixa aleatoriamente
                'lateralDelta': 0.0               # Indica a força da curva visual que o bot está a fazer
            })

        # ==========================================
        # GAME LOOP PRINCIPAL
        # ==========================================
        while True:
            # 1. PROCESSAR EVENTOS (Fechar janela)
            for event in pygame.event.get([pygame.QUIT]):
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            keys = pygame.key.get_pressed()

            # Descobre em que parte do circuito o jogador está
            pos = absolutePos % trackLength 
            currentLap = int(absolutePos // trackLength) + 1

            startPos = int(pos // self.segmentLength)
            startSegment = lines[startPos % totalSegments]
            rawCurve = startSegment.curve # Curvatura real do segmento atual
            absCurve = abs(rawCurve)
            
            # --- SISTEMA DE VÁCUO (SLIPSTREAM) ---
            # Se formos atrás de um carro, ganhamos velocidade extra
            isDrafting = False
            playerVisualZ = 780 # Onde o carro do jogador parece estar no ecrã
            playerVirtualZ = pos + playerVisualZ 

            # Só funciona em retas ou curvas muito suaves, e se já estivermos rápidos
            if absCurve <= 2.0 and speed >= 240:
                for opp in self.opponents:
                    dz = opp['z'] - playerVirtualZ
                    if dz < 0: dz += trackLength # Corrige o cálculo perto da meta
                    # Se o bot estiver perto à nossa frente e na mesma faixa
                    if 50 < dz < 6000 and abs(opp['x'] - playerX) < 0.3:
                        isDrafting = True
                        break
            
            # Aplica o bónus gradualmente (efeito estilingue)
            if isDrafting:
                draftBonus = min(10.0, draftBonus + 0.15)
            else:
                draftBonus = max(0.0, draftBonus - 0.10)
                    
            maxSpeed = basePlayerMaxSpeed + draftBonus

            # --- FÍSICA: FORÇA CENTRÍFUGA ---
            # Empurra o carro para fora nas curvas, dependendo da velocidade
            trackDriftForce = (absCurve ** 0.6) * 0.015
            currentCentrifugal = trackDriftForce * (speed / maxSpeed)

            isOffroad = abs(playerX) > 2.3 # Mais que 2.3 = o carro está na relva
            currentMaxSpeed = maxSpeed * 0.4 if isOffroad else maxSpeed

            # --- CONTROLOS DO JOGADOR ---
            if keys[pygame.K_UP]: speed += 3       # Acelerar
            elif keys[pygame.K_DOWN]: speed -= 8   # Travar
            else:
                if speed > 0: speed -= 2           # Atrito natural
                elif speed < 0: speed += 2

            steerState = 'S'      # Sprite base do carro
            baseSteer = 0.045     # Força de viragem do comando
            steerCap = 0.09
            steerAmount = 0.0
            isTurning = False

            # Lógica para virar à esquerda
            if keys[pygame.K_LEFT] and speed > 0:
                isTurning = True
                if rawCurve < -1.0: # Ajudar a virar se a curva for para o mesmo lado
                    steerAmount = min(max(baseSteer * 0.6, currentCentrifugal + 0.002), steerCap)
                else: 
                    steerAmount = baseSteer
                    
                playerX -= steerAmount
                turnTimer = max(0, turnTimer) + 1 
                steerState = 'L' if turnTimer > 5 else 'SL'
                    
            # Lógica para virar à direita
            elif keys[pygame.K_RIGHT] and speed > 0:
                isTurning = True
                if rawCurve > 1.0: 
                    steerAmount = min(max(baseSteer * 0.6, currentCentrifugal + 0.002), steerCap)
                else: 
                    steerAmount = baseSteer
                    
                playerX += steerAmount
                turnTimer = min(0, turnTimer) - 1 
                steerState = 'R' if turnTimer < -5 else 'SR'
            else:
                turnTimer = 0 # Carro endireita-se

            # Aplica a derrapagem (força centrífuga) na posição X do jogador
            trackDrift = currentCentrifugal if rawCurve > 0 else (-currentCentrifugal if rawCurve < 0 else 0.0)
            playerX -= trackDrift

            # Punições de velocidade por erros
            if isOffroad and speed > currentMaxSpeed: 
                speed -= 6 # Desacelera muito na relva
            if isTurning and trackDriftForce > 0.015:
                # Perde velocidade se curvar com demasiada força
                targetSpeed = currentMaxSpeed - (trackDriftForce * 900)
                if speed > targetSpeed: speed -= 5.0

            # Impede o jogador de sair do limite do mundo
            playerX = max(-5.0, min(playerX, 5.0))
            
            # ==========================================
            # INTELIGÊNCIA ARTIFICIAL (BOTS)
            # ==========================================
            for opp in self.opponents:
                # 1. Rubberbanding (Efeito elástico para manter os bots competitivos)
                distFromPlayer = opp['z'] - pos
                if distFromPlayer > trackLength / 2: distFromPlayer -= trackLength
                elif distFromPlayer < -trackLength / 2: distFromPlayer += trackLength
                
                # Acelera bots que ficaram muito para trás, abranda os muito avançados
                if distFromPlayer < -10000: opp['maxSpeed'] = opp['baseMaxSpeed'] + 6
                elif distFromPlayer > 1200: opp['maxSpeed'] = opp['baseMaxSpeed'] - 3
                else: opp['maxSpeed'] = opp['baseMaxSpeed']

                # Lógica de aceleração básica do bot
                if opp['speed'] < opp['maxSpeed']: opp['speed'] += 2.5
                elif opp['speed'] > opp['maxSpeed']: opp['speed'] -= 1.0 
                
                # Curva atual onde o bot se encontra
                oppSeg = lines[int(opp['z'] // self.segmentLength) % totalSegments]
                oppCurve = oppSeg.curve
                oppAbsCurve = abs(oppCurve)
                
                # 2. Tomada de Decisão (Mudar de faixa aleatoriamente nas retas)
                opp['decisionTimer'] -= 1
                if opp['decisionTimer'] <= 0:
                    opp['decisionTimer'] = random.randint(60, 120)
                    if oppAbsCurve < 0.5:
                        opp['targetX'] = random.choice([-1.2, -0.6, 0.0, 0.6, 1.2])
                
                # 3. Radar Anticolisão: Bot contra Bot
                for other in self.opponents:
                    if other is opp: continue 
                    distZ = other['z'] - opp['z']
                    if distZ < 0: distZ += trackLength 
                    
                    if 0 < distZ < 400 and abs(other['x'] - opp['x']) < 0.8: 
                        # Foge para a faixa oposta
                        opp['targetX'] = 1.2 if opp['x'] >= other['x'] else -1.2
                        # Trava se estiver iminente
                        if distZ < 150 and opp['speed'] > other['speed'] and abs(other['x'] - opp['x']) < 0.4:
                            opp['speed'] = other['speed']

                # 4. Radar Anticolisão Aprimorado: Bot contra Jogador
                # Usa distToPlayer para considerar "retrovisores" (pontos cegos)
                distToPlayer = playerVirtualZ - opp['z']
                if distToPlayer > trackLength / 2: distToPlayer -= trackLength
                elif distToPlayer < -trackLength / 2: distToPlayer += trackLength
                
                # O bot deteta o jogador 400m atrás dele e 800m à frente
                if -400 < distToPlayer < 800 and abs(playerX - opp['x']) < 0.9: 
                    # Cancela mudança de faixa e afasta-se
                    opp['targetX'] = 1.2 if opp['x'] >= playerX else -1.2
                    # O Bot só puxa o travão de emergência se o jogador estiver BEM À FRENTE dele
                    if 0 < distToPlayer < 100 and opp['speed'] > speed and abs(playerX - opp['x']) < 0.4:
                        opp['speed'] = speed 
                
                # 5. Física do Bot (Força centrífuga o afeta também)
                oppDriftForce = 0.0
                isOppTurning = False
                oppCentrifugal = 0.0
                lateralDelta = 0.0 
                
                if oppAbsCurve > 0:
                    oppDriftForce = (oppAbsCurve ** 0.6) * 0.015
                    oppCentrifugal = oppDriftForce * (opp['speed'] / maxSpeed)
                    opp['x'] += oppCentrifugal if oppCurve < 0 else -oppCentrifugal

                dynamicBotSteer = max(0.04, oppCentrifugal + 0.015) 
                
                # Move visualmente o bot para o targetX selecionado
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

                opp['lateralDelta'] = lateralDelta # Usado para escolher o sprite de viragem
                    
                # Perde velocidade ao curvar muito, tal como o jogador
                if isOppTurning and oppDriftForce > 0.015:
                    targetOppSpeed = opp['maxSpeed'] - (oppDriftForce * 850)
                    if opp['speed'] > targetOppSpeed: opp['speed'] -= 4.5

                opp['x'] = max(-1.8, min(opp['x'], 1.8)) # Limita na pista
                opp['z'] = (opp['z'] + opp['speed']) % trackLength

                # 6. Colisão Jogador bate no Bot por trás (Punição para o jogador)
                dzOpp = opp['z'] - pos
                if dzOpp < 0: dzOpp += trackLength 
                opp['dz'] = dzOpp 
                
                if playerVisualZ < dzOpp < playerVisualZ + 400 and abs(playerX - opp['x']) < 0.50:
                    speed *= 0.3 # Jogador bateu, a velocidade cai drasticamente
            
            # --- FIM IA ---

            # Atualiza a posição do jogador no mundo
            speed = max(0, min(speed, currentMaxSpeed))
            absolutePos += speed
            pos = absolutePos % trackLength 

            # Ordena os bots do mais distante ao mais próximo para renderizar corretamente (Painter's Algorithm)
            self.opponents.sort(key=lambda o: o['dz'], reverse=True)

            # Câmara Debug (opcional)
            if keys[pygame.K_w]: playerY += 100
            if keys[pygame.K_s]: playerY -= 100
            if keys[pygame.K_q]: playerPitchBase += 10 
            if keys[pygame.K_e]: playerPitchBase -= 10 
            if playerY < 500: playerY = 500

            # --- PREPARAÇÃO DA CÂMARA (COLINAS E CURVAS) ---
            # O Lookahead analisa os segmentos à frente para inclinar a câmara nas subidas/descidas
            lookahead = 3
            segmentoFrente = (startPos + lookahead) % totalSegments
            dy = lines[segmentoFrente].y - lines[startPos].y
            pitchAlvo = playerPitchBase + (-dy * 0.5)
            smoothPitch += (pitchAlvo - smoothPitch) * 0.1 # Transição suave do movimento de colina

            camHeight = lines[startPos].y + playerY
            maxY = WINDOW_HEIGHT

            # Deslocamento do fundo (Céu a mover na direção oposta à curva)
            self.bgOffsetX += rawCurve * speed * 0.0005
            self.backgroundRect.x = -(int(self.bgOffsetX) % self.bgWidth)

            # Projeta o horizonte (onde o chão se encontra com o céu)
            farNode = startPos + self.showSegments - 1
            farLine = lines[farNode % totalSegments]
            farCamZ = pos - (totalSegments * self.segmentLength if farNode >= totalSegments else 0)
            
            if farLine.z - farCamZ > 0.1:
                farScale = self.cameraDepth / (farLine.z - farCamZ)
                farY = ((1 - farScale * (farLine.y - camHeight)) * WINDOW_HEIGHT / 2) - smoothPitch
            else:
                farY = WINDOW_HEIGHT / 2
            
            # Renderiza o céu degradê e a imagem de fundo das montanhas/cidade
            drawStripedSky(self.windowSurface, SKY_COLOR_TOP, SKY_COLOR_BOTTOM, SKY_BAND_HEIGHT, farY)
            self.backgroundRect.bottom = int(farY) + 1 
            self.windowSurface.blit(self.backgroundSurface, self.backgroundRect)

            worldX = 0.0  
            dx = 0.0  
            playerXWorld = playerX * 1000

            # ==========================================
            # RENDERIZAÇÃO 3D (DESENHAR A PISTA)
            # ==========================================
            for n in range(startPos, startPos + self.showSegments):
                currentLine = lines[n % totalSegments]
                
                # Converte as coordenadas 3D para o ecrã 2D
                currentLine.project(playerXWorld - worldX, camHeight, pos - (totalSegments * self.segmentLength if n >= totalSegments else 0), smoothPitch, self.cameraDepth, self.roadWidth)
                
                worldX += dx
                dx += currentLine.curve
                currentLine.clip = maxY # Salva o limite inferior visível para não desenhar carros que estejam atrás das colinas

                if currentLine.Y >= maxY: continue # Se o segmento está atrás de uma colina, não desenha
                maxY = currentLine.Y
                prevLine = lines[(n - 1) % totalSegments]  

                # Desenha Relva, Zebra (Rumble) e Asfalto
                drawQuad(self.windowSurface, currentLine.grassColor, 0, prevLine.Y, WINDOW_WIDTH, 0, currentLine.Y, WINDOW_WIDTH)
                drawQuad(self.windowSurface, currentLine.rumbleColor, prevLine.X, prevLine.Y, prevLine.W * 1.2, currentLine.X, currentLine.Y, currentLine.W * 1.2)
                drawQuad(self.windowSurface, currentLine.roadColor, prevLine.X, prevLine.Y, prevLine.W, currentLine.X, currentLine.Y, currentLine.W)

            # ==========================================
            # RENDERIZAÇÃO DOS OPONENTES (BOTS)
            # ==========================================
            for opp in self.opponents:
                dz = opp['dz']
                # Só desenha se estiver dentro do raio de visão da câmara
                if 0 < dz < (self.showSegments - 2) * self.segmentLength:
                    segIdx = int(opp['z'] // self.segmentLength) % totalSegments
                    
                    line1 = lines[segIdx]
                    line2 = lines[(segIdx + 1) % totalSegments]
                    
                    if line1.scale == 0 or line2.scale == 0: continue
                    
                    # Interpolação para colocar o carro suavemente entre dois segmentos
                    percent = (opp['z'] % self.segmentLength) / self.segmentLength
                    destX = line1.X + (line2.X - line1.X) * percent
                    destY = line1.Y + (line2.Y - line1.Y) * percent
                    destW = line1.W + (line2.W - line1.W) * percent
                    
                    # --- CORREÇÃO DE ESCALA DOS BOTS (Mantém a proporção real) ---
                    # A largura de referência na pista
                    baseTargetW = destW * 0.28
                    # A largura original do sprite recto serve de âncora
                    baseSpriteW = self.rawCarSprites['S'][0].get_width()
                    # Qual deve ser a escala deste sprite nesta distância específica
                    escalaDistancia = baseTargetW / baseSpriteW

                    # Escolhe o Sprite de direção com base na força da curva e no movimento lateral
                    turnForce = line1.curve + (opp.get('lateralDelta', 0.0) * 80.0)
                    oppSteer = 'S'
                    
                    # Lógica corrigida das janelas de curva
                    if turnForce < -1.0: 
                        oppSteer = 'L' if turnForce < -3.0 else 'SL'
                    elif turnForce > 1.0: 
                        oppSteer = 'R' if turnForce > 3.0 else 'SR'
                    
                    # Alterna entre os 2 frames para simular a rotação do pneu/movimento
                    oppFrame = 0 if (int(opp['z']) % 400) < 200 else 1
                    currentOppSprite = self.rawCarSprites[oppSteer][oppFrame]
                    
                    # Aplica a escala exata e proporcional, evitando o "encolhimento"
                    finalW = currentOppSprite.get_width() * escalaDistancia
                    finalH = currentOppSprite.get_height() * escalaDistancia
                    
                    # Simula os solavancos do carro em alta velocidade
                    oppBounce = (baseTargetW * 0.02) if (opp['speed'] > 0 and (int(opp['z']) % 300) < 150) else 0
                    
                    # Posição final no ecrã
                    renderX = destX + (opp['x'] * destW * 0.5) - (finalW / 2)
                    renderY = destY - finalH - oppBounce 
                    
                    # Corta a imagem (Crop) se parte do carro estiver atrás de uma colina
                    clipH = renderY + finalH - line1.clip
                    if clipH < 0: clipH = 0
                    if clipH >= finalH: continue # Carro 100% escondido
                    if finalW > WINDOW_WIDTH * 1.5 or finalW <= 0 or finalH <= 0: continue 
                    
                    try:
                        scaledSprite = pygame.transform.scale(currentOppSprite, (int(finalW), int(finalH)))
                        cropSurface = scaledSprite.subsurface(0, 0, int(finalW), int(finalH - clipH))
                        self.windowSurface.blit(cropSurface, (int(renderX), int(renderY)))
                    except ValueError:
                        pass # Proteção contra erros matemáticos de subsuperfície

            # ==========================================
            # RENDERIZAÇÃO DO JOGADOR
            # ==========================================
            # Controla a velocidade de alternância dos frames do jogador
            if speed > 0:
                animTimer = (animTimer + speed) % 1500
            
            animFrame = 0 if animTimer < 750 else 1  
            carImage = self.carSprites[steerState][animFrame]
            carRect = carImage.get_rect()
            
            # Bounce (salto) do jogador. Mais violento se estiver na relva.
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
            # Velocímetro
            speedText = self.hudFont.render(f"{int(speed)} KM/H", True, (255, 255, 255))
            pygame.draw.rect(self.windowSurface, (0, 0, 0), pygame.Rect(15, 15, speedText.get_width() + 20, speedText.get_height() + 10))
            
            # Fica Azul Ciano se estiver a receber bónus de vácuo (estilingue)
            speedColor = (0, 255, 255) if draftBonus > 0.5 else (255, 255, 255)
            self.windowSurface.blit(self.hudFont.render(f"{int(speed)} KM/H", True, speedColor), (25, 20))
            
            # Contador de Voltas
            displayLap = min(currentLap, maxLaps)
            lapText = self.lapFont.render(f"LAP {displayLap}/{maxLaps}", True, (255, 200, 0))
            self.windowSurface.blit(lapText, (WINDOW_WIDTH - lapText.get_width() - 20, 20))
            
            # Fim de Jogo
            if currentLap > maxLaps:
                finishText = self.lapFont.render("FINISH!", True, (0, 255, 0))
                self.windowSurface.blit(finishText, (WINDOW_WIDTH//2 - finishText.get_width()//2, 100))

            # Renderiza o frame e espera (60 FPS)
            pygame.display.update()
            self.clock.tick(60)