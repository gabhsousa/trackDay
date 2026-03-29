import pygame
import sys
import os
import random
from typing import List

# Constantes globais
SKY_COLOR_TOP = (0, 60, 150)  
SKY_COLOR_BOTTOM = (40, 180, 250)
SKY_BAND_HEIGHT = 24

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

class Line:
    def __init__(self, index):
        self.i = index
        self.x = self.y = self.z = 0.0  
        self.X = self.Y = self.W = 0.0  
        self.scale = 0.0  
        self.curve = 0.0  
        self.clip = 0.0  

        self.grassColor: pygame.Color = "black"
        self.rumbleColor: pygame.Color = "black"
        self.roadColor: pygame.Color = "black"

    def project(self, camX: float, camY: float, camZ: float, camPitch: float, cameraDepth: float, roadWidth: int):
        dz = self.z - camZ
        
        if dz <= 0.1:
            self.Y = WINDOW_HEIGHT + 1000
            self.X = 0; self.W = 0; self.scale = 0
            return

        self.scale = cameraDepth / dz
        self.X = (1 + self.scale * (self.x - camX)) * WINDOW_WIDTH / 2
        self.Y = ((1 - self.scale * (self.y - camY)) * WINDOW_HEIGHT / 2) - camPitch
        self.W = self.scale * roadWidth * WINDOW_WIDTH / 2


def drawQuad(surface: pygame.Surface, color: pygame.Color, x1: float, y1: float, w1: float, x2: float, y2: float, w2: float):
    pygame.draw.polygon(surface, color, [(x1 - w1, y1), (x2 - w2, y2), (x2 + w2, y2), (x1 + w1, y1)])

def drawStripedSky(surface: pygame.Surface, topColor, bottomColor, bandHeight, horizonY):
    if horizonY <= 0: return
    endY = min(WINDOW_HEIGHT, int(horizonY))
    
    for y in range(0, endY, bandHeight):
        t = y / horizonY 
        r = int(topColor[0] + (bottomColor[0] - topColor[0]) * t)
        g = int(topColor[1] + (bottomColor[1] - topColor[1]) * t)
        b = int(topColor[2] + (bottomColor[2] - topColor[2]) * t)
        pygame.draw.rect(surface, (r, g, b), (0, y, WINDOW_WIDTH, bandHeight))


class GameWindow:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("TrackDay - Arcade Bots com Efeito Estilingue")
        self.windowSurface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        
        pygame.font.init()
        self.hudFont = pygame.font.SysFont('Arial', 30, bold=True)
        self.lapFont = pygame.font.SysFont('Arial', 40, bold=True)

        self.lines: List[Line] = []
        
        self.roadWidth = 2000  
        self.segmentLength = 200  
        self.cameraDepth = 0.84  
        self.showSegments = 300

        self.darkGrass = pygame.Color(0, 120, 0)
        self.lightGrass = pygame.Color(0, 150, 0)
        self.whiteRumble = pygame.Color(255, 255, 255)
        self.blackRumble = pygame.Color(200, 0, 0)
        self.darkRoad = pygame.Color(95, 95, 95)
        self.lightRoad = pygame.Color(107, 107, 107)

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

    def addSegment(self, curve: float, y: float):
        n = len(self.lines)
        line = Line(n)
        line.z = n * self.segmentLength + 0.00001
        line.curve = curve
        line.y = y
        line.grassColor = self.lightGrass if (n // 3) % 2 else self.darkGrass
        line.rumbleColor = self.whiteRumble if (n // 3) % 2 else self.blackRumble
        line.roadColor = self.lightRoad if (n // 3) % 2 else self.darkRoad
        self.lines.append(line)

    def easeInOut(self, t: float) -> float: 
        return t * t * (3 - 2 * t)

    def addRoad(self, enter: int, hold: int, leave: int, curve: float, y: float):
        startY = self.lines[-1].y if len(self.lines) > 0 else 0.0
        total = enter + hold + leave
        currentSegment = 0

        for i in range(enter):
            curveTime = i / enter if enter > 0 else 0
            yTime = currentSegment / total if total > 0 else 0
            self.addSegment(curve * self.easeInOut(curveTime), startY + (y - startY) * self.easeInOut(yTime))
            currentSegment += 1

        for i in range(hold):
            yTime = currentSegment / total if total > 0 else 0
            currentY = startY + (y - startY) * self.easeInOut(yTime)
            self.addSegment(curve, currentY)
            currentSegment += 1

        for i in range(leave):
            curveTime = i / leave if leave > 0 else 0
            yTime = currentSegment / total if total > 0 else 0
            self.addSegment(curve * self.easeInOut(1 - curveTime), startY + (y - startY) * self.easeInOut(yTime))
            currentSegment += 1

    def buildTrack(self):
        self.lines = []
        self.addRoad(enter=0, hold=100, leave=0, curve=0.0, y=0.0)
        self.addRoad(enter=40, hold=10, leave=5, curve=-15.0, y=-2500.0)
        self.addRoad(enter=5, hold=40, leave=10, curve=15.0, y=-5000.0)
        self.addRoad(enter=60, hold=80, leave=45, curve=-3.0, y=-5500.0)
        self.addRoad(enter=0, hold=200, leave=0, curve=0.0, y=-5500.0)
        self.addRoad(enter=40, hold=40, leave=20, curve=-10.0, y=-6000.0)
        self.addRoad(enter=30, hold=40, leave=0, curve=0.0, y=-7000.0)
        self.addRoad(enter=50, hold=40, leave=10, curve=-6.0, y=-7000.0)
        self.addRoad(enter=30, hold=100, leave=0, curve=0.0, y=-4500.0)
        self.addRoad(enter=0, hold=70, leave=20, curve=5.0, y=-2500.0)
        self.addRoad(enter=10, hold=30, leave=30, curve=15.0, y=-4500.0)
        self.addRoad(enter=20, hold=50, leave=20, curve=-25.0, y=-5000.0)
        self.addRoad(enter=30, hold=80, leave=5, curve=0.0, y=-3000.0)
        self.addRoad(enter=5, hold=50, leave=35, curve=10.0, y=-2500.0)
        self.addRoad(enter=0, hold=40, leave=15, curve=12.0, y=-3500.0)
        self.addRoad(enter=20, hold=70, leave=40, curve=-6.0, y=-6500.0)
        self.addRoad(enter=25, hold=100, leave=5, curve=0.0, y=-4000.0)
        self.addRoad(enter=5, hold=40, leave=20, curve=-14.0, y=-2500.0)
        self.addRoad(enter=20, hold=80, leave=20, curve=-0.0, y=-2000.0)
        self.addRoad(enter=20, hold=100, leave=20, curve=-1.0, y=-1000.0)
        self.addRoad(enter=20, hold=150, leave=20, curve=-1.0, y=-500.0)
        self.addRoad(enter=30, hold=100, leave=30, curve=0.0, y=0.0)

    def run(self):
        self.buildTrack()
        totalSegments = len(self.lines)
        trackLength = totalSegments * self.segmentLength

        absolutePos = 0.0 
        maxLaps = 3

        playerX = 0.0  
        playerY = 1250  
        playerPitchBase = 150 
        smoothPitch = 0.0  
        
        speed = 0.0
        basePlayerMaxSpeed = 260 
        maxSpeed = basePlayerMaxSpeed
        draftBonus = 0.0 # NOVO: Variável para acumular o vácuo lentamente
        
        animTimer = 0
        turnTimer = 0

        self.opponents = []
        for i in range(9):
            baseSpeed = 240 + (i * 3) 
            
            self.opponents.append({
                'id': i, 
                'z': (i + 1) * 1500.0, 
                'x': (i % 3) * 1.2 - 1.2, 
                'targetX': (i % 3) * 1.2 - 1.2, 
                'speed': 0.0, 
                'baseMaxSpeed': baseSpeed, 
                'maxSpeed': baseSpeed,
                'decisionTimer': random.randint(0, 100),
                'lateralDelta': 0.0
            })

        while True:
            for event in pygame.event.get([pygame.QUIT]):
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            keys = pygame.key.get_pressed()

            pos = absolutePos % trackLength 
            currentLap = int(absolutePos // trackLength) + 1

            startPos = int(pos // self.segmentLength)
            startSegment = self.lines[startPos % totalSegments]
            rawCurve = startSegment.curve
            absCurve = abs(rawCurve)
            
            # --- SISTEMA DE VÁCUO (SLIPSTREAM COM ACELERAÇÃO GRADUAL) ---
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
            
            # Incremento Gradual do Vácuo (Estilingue)
            if isDrafting:
                draftBonus += 0.15 # Enche a barra de vácuo aos poucos
                if draftBonus > 10.0:
                    draftBonus = 10.0
            else:
                draftBonus -= 0.10# Esvazia rapidamente ao sair de trás do carro (efeito de ultrapassagem)
                if draftBonus < 0.0:
                    draftBonus = 0.0
                    
            maxSpeed = basePlayerMaxSpeed + draftBonus
            # ------------------------------------------------------------

            trackDriftForce = (absCurve ** 0.6) * 0.015
            currentCentrifugal = trackDriftForce * (speed / maxSpeed)

            isOffroad = abs(playerX) > 2.3
            currentMaxSpeed = maxSpeed * 0.4 if isOffroad else maxSpeed

            if keys[pygame.K_UP]: speed += 3
            elif keys[pygame.K_DOWN]: speed -= 8
            else:
                if speed > 0: speed -= 2
                elif speed < 0: speed += 2

            steerState = 'S' 
            baseSteer = 0.045
            steerCap = 0.09
            steerAmount = 0.0
            isTurning = False

            if keys[pygame.K_LEFT] and speed > 0:
                isTurning = True
                if rawCurve < -1.0: 
                    dynamicSteer = max(baseSteer * 0.6, currentCentrifugal + 0.002)
                    steerAmount = min(dynamicSteer, steerCap)
                else: steerAmount = baseSteer
                    
                playerX -= steerAmount
                if turnTimer < 0: turnTimer = 0 
                turnTimer += 1 
                steerState = 'L' if turnTimer > 5 else 'SL'
                    
            elif keys[pygame.K_RIGHT] and speed > 0:
                isTurning = True
                if rawCurve > 1.0: 
                    dynamicSteer = max(baseSteer * 0.6, currentCentrifugal + 0.002)
                    steerAmount = min(dynamicSteer, steerCap)
                else: steerAmount = baseSteer
                    
                playerX += steerAmount
                if turnTimer > 0: turnTimer = 0 
                turnTimer -= 1 
                steerState = 'R' if turnTimer < -5 else 'SR'
            else:
                turnTimer = 0

            if rawCurve > 0: trackDrift = currentCentrifugal
            elif rawCurve < 0: trackDrift = -currentCentrifugal
            else: trackDrift = 0.0
                
            playerX -= trackDrift

            if isOffroad and speed > currentMaxSpeed: speed -= 6 
                
            if isTurning and trackDriftForce > 0.015:
                targetSpeed = currentMaxSpeed - (trackDriftForce * 900)
                if speed > targetSpeed: speed -= 5.0

            playerX = max(-5.0, min(playerX, 5.0))
            
            # --- ATUALIZAÇÃO DA FÍSICA E IA DOS OPONENTES ---
            for opp in self.opponents:
                
                distFromPlayer = opp['z'] - pos
                if distFromPlayer > trackLength / 2: distFromPlayer -= trackLength
                elif distFromPlayer < -trackLength / 2: distFromPlayer += trackLength
                
                if distFromPlayer < -1000:
                    opp['maxSpeed'] = opp['baseMaxSpeed'] + 7
                elif distFromPlayer > 1200:
                    opp['maxSpeed'] = opp['baseMaxSpeed'] - 5
                else:
                    opp['maxSpeed'] = opp['baseMaxSpeed']

                if opp['speed'] < opp['maxSpeed']:
                    opp['speed'] += 2.5
                elif opp['speed'] > opp['maxSpeed']:
                    opp['speed'] -= 1.0 
                
                oppSeg = self.lines[int(opp['z'] // self.segmentLength) % totalSegments]
                oppCurve = oppSeg.curve
                oppAbsCurve = abs(oppCurve)
                
                opp['decisionTimer'] -= 1
                if opp['decisionTimer'] <= 0:
                    opp['decisionTimer'] = random.randint(60, 120)
                    if oppAbsCurve < 0.5:
                        faixas = [-1.2, -0.6, 0.0, 0.6, 1.2]
                        opp['targetX'] = random.choice(faixas)
                
                # Radar Anticolisão (Bots vs Bots)
                for other in self.opponents:
                    if other is opp: continue 
                    distZ = other['z'] - opp['z']
                    if distZ < 0: distZ += trackLength 
                    
                    if 0 < distZ < 400:
                        if abs(other['x'] - opp['x']) < 0.8: 
                            if opp['x'] >= other['x']:
                                opp['targetX'] = 1.2
                            else:
                                opp['targetX'] = -1.2
                                
                            if distZ < 150 and opp['speed'] > other['speed'] and abs(other['x'] - opp['x']) < 0.4:
                                opp['speed'] = other['speed']

                # --- RADAR ANTICOLISÃO (BOTS VS PLAYER) FOCADO EM DESVIO ---
                distToPlayer = playerVirtualZ - opp['z']
                if distToPlayer < 0: distToPlayer += trackLength
                
                if 0 < distToPlayer < 800:
                    if abs(playerX - opp['x']) < 0.8: 
                        if opp['x'] >= playerX:
                            opp['targetX'] = 1.2
                        else:
                            opp['targetX'] = -1.2
                        
                        if distToPlayer < 100 and opp['speed'] > speed and abs(playerX - opp['x']) < 0.4:
                            opp['speed'] = speed 
                # -----------------------------------------------------------
                
                # Força Centrífuga e Movimentação
                oppDriftForce = 0.0
                isOppTurning = False
                oppCentrifugal = 0.0
                lateralDelta = 0.0 
                
                if oppAbsCurve > 0:
                    oppDriftForce = (oppAbsCurve ** 0.6) * 0.015
                    oppCentrifugal = oppDriftForce * (opp['speed'] / maxSpeed)
                    
                    if oppCurve > 0: opp['x'] -= oppCentrifugal
                    elif oppCurve < 0: opp['x'] += oppCentrifugal

                baseBotSteer = 0.04
                dynamicBotSteer = max(baseBotSteer, oppCentrifugal + 0.015) 
                
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
                    if opp['speed'] > targetOppSpeed:
                        opp['speed'] -= 4.5

                opp['x'] = max(-1.8, min(opp['x'], 1.8))
                
                opp['z'] += opp['speed']
                if opp['z'] >= trackLength:
                    opp['z'] -= trackLength

                dzOpp = opp['z'] - pos
                if dzOpp < 0: dzOpp += trackLength 
                opp['dz'] = dzOpp 
                
                if playerVisualZ < dzOpp < playerVisualZ + 400 and abs(playerX - opp['x']) < 0.50:
                    speed *= 0.3
            # ------------------------------------------------
            
            speed = max(0, min(speed, currentMaxSpeed))
            absolutePos += speed
            pos = absolutePos % trackLength 

            self.opponents.sort(key=lambda o: o['dz'], reverse=True)

            if keys[pygame.K_w]: playerY += 100
            if keys[pygame.K_s]: playerY -= 100
            if keys[pygame.K_q]: playerPitchBase += 10 
            if keys[pygame.K_e]: playerPitchBase -= 10 
            if playerY < 500: playerY = 500

            lookahead = 3
            segmentoFrente = (startPos + lookahead) % totalSegments
            dy = self.lines[segmentoFrente].y - self.lines[startPos].y
            pitchAlvo = playerPitchBase + (-dy * 0.5)
            smoothPitch += (pitchAlvo - smoothPitch) * 0.1

            camHeight = self.lines[startPos].y + playerY
            maxY = WINDOW_HEIGHT

            self.bgOffsetX += rawCurve * speed * 0.0005
            wrappedX = int(self.bgOffsetX) % self.bgWidth
            self.backgroundRect.x = -wrappedX

            farNode = startPos + self.showSegments - 1
            farLine = self.lines[farNode % totalSegments]
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

            for n in range(startPos, startPos + self.showSegments):
                currentLine = self.lines[n % totalSegments]
                currentLine.project(playerXWorld - worldX, camHeight, pos - (totalSegments * self.segmentLength if n >= totalSegments else 0), smoothPitch, self.cameraDepth, self.roadWidth)
                
                worldX += dx
                dx += currentLine.curve
                currentLine.clip = maxY

                if currentLine.Y >= maxY: continue
                maxY = currentLine.Y
                prevLine = self.lines[(n - 1) % totalSegments]  

                drawQuad(self.windowSurface, currentLine.grassColor, 0, prevLine.Y, WINDOW_WIDTH, 0, currentLine.Y, WINDOW_WIDTH)
                drawQuad(self.windowSurface, currentLine.rumbleColor, prevLine.X, prevLine.Y, prevLine.W * 1.2, currentLine.X, currentLine.Y, currentLine.W * 1.2)
                drawQuad(self.windowSurface, currentLine.roadColor, prevLine.X, prevLine.Y, prevLine.W, currentLine.X, currentLine.Y, currentLine.W)

            for opp in self.opponents:
                dz = opp['dz']
                if 0 < dz < (self.showSegments - 2) * self.segmentLength:
                    segIdx = int(opp['z'] // self.segmentLength) % totalSegments
                    
                    line1 = self.lines[segIdx]
                    line2 = self.lines[(segIdx + 1) % totalSegments]
                    
                    if line1.scale == 0 or line2.scale == 0: continue
                    
                    percent = (opp['z'] % self.segmentLength) / self.segmentLength
                    
                    destX = line1.X + (line2.X - line1.X) * percent
                    destY = line1.Y + (line2.Y - line1.Y) * percent
                    destW = line1.W + (line2.W - line1.W) * percent
                    
                    finalW = destW * 0.28
                    
                    turnForce = line1.curve + (opp.get('lateralDelta', 0.0) * 80.0)
                    
                    oppSteer = 'S'
                    if turnForce < -1.0: oppSteer = 'SL' if turnForce < -3.0 else 'L'
                    elif turnForce > 1.0: oppSteer = 'SR' if turnForce > 3.0 else 'R'
                    
                    oppFrame = 0 if (int(opp['z']) % 400) < 200 else 1
                    
                    oppBounce = 0
                    if opp['speed'] > 0:
                        oppBounce = (finalW * 0.03) if (int(opp['z']) % 300) < 150 else 0
                    
                    currentOppSprite = self.rawCarSprites[oppSteer][oppFrame]
                    
                    h = currentOppSprite.get_height()
                    w = currentOppSprite.get_width()
                    finalH = finalW * (h / w)
                    
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

            if speed > 0:
                animTimer += speed
                if animTimer > 1500: animTimer = 0
            
            animFrame = 0 if animTimer < 750 else 1  
            carImage = self.carSprites[steerState][animFrame]
            carRect = carImage.get_rect()
            
            bounceOffset = 0
            if speed > 0:
                bounceOffset = 2 if (int(pos) % 400) < 200 else 0
                if isOffroad:
                    bounceOffset *= 3 
                    
            carRect.centerx = WINDOW_WIDTH // 2 
            carRect.bottom = (WINDOW_HEIGHT - 30) - bounceOffset
            self.windowSurface.blit(carImage, carRect)

            speedText = self.hudFont.render(f"{int(speed)} KM/H", True, (255, 255, 255))
            bgRect = pygame.Rect(15, 15, speedText.get_width() + 20, speedText.get_height() + 10)
            pygame.draw.rect(self.windowSurface, (0, 0, 0), bgRect)
            
            # O texto da velocidade muda de cor enquanto você tiver qualquer bônus de vácuo ativo
            speedColor = (0, 255, 255) if draftBonus > 0.5 else (255, 255, 255)
            speedSurface = self.hudFont.render(f"{int(speed)} KM/H", True, speedColor)
            self.windowSurface.blit(speedSurface, (25, 20))
            
            displayLap = min(currentLap, maxLaps)
            lapText = self.lapFont.render(f"LAP {displayLap}/{maxLaps}", True, (255, 200, 0))
            self.windowSurface.blit(lapText, (WINDOW_WIDTH - lapText.get_width() - 20, 20))
            
            if currentLap > maxLaps:
                finishText = self.lapFont.render("FINISH!", True, (0, 255, 0))
                self.windowSurface.blit(finishText, (WINDOW_WIDTH//2 - finishText.get_width()//2, 100))

            pygame.display.update()
            self.clock.tick(60)

if __name__ == "__main__":
    game = GameWindow()
    game.run()