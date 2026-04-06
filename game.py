import pygame
import sys
import os
import random

from config import *
from utils import drawQuad, drawStripedSky
from track import Track

import numpy as np

class GameWindow:
    def __init__(self, dev_mode=False):
        self.dev_mode = dev_mode
        
        self.windowSurface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("TrackDay")
        self.clock = pygame.time.Clock()
        
        pygame.font.init()
        try:
            self.hudFont = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 20)
            self.lapFont = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 30)
            self.finishFont = pygame.font.Font('fonts/PressStart2P-Regular.ttf', 50)
        except FileNotFoundError:
            print("Aviso: Fonte 8-bit não encontrada. Usando fonte padrão.")
            self.hudFont = pygame.font.SysFont('Courier New', 24, bold=True)
            self.lapFont = pygame.font.SysFont('Courier New', 34, bold=True)
            self.finishFont = pygame.font.SysFont('Courier New', 54, bold=True)

        self.digiGreen = (50, 255, 50)
        self.digiGreenDark = (0, 40, 0)
        self.digiBlue = (50, 150, 255)
        self.digiBlueDark = (0, 20, 40)

        try:
            self.speedFont = pygame.font.Font('fonts/dseg7-classic-latin-700-italic.ttf', 80)
        except FileNotFoundError:
            self.speedFont = pygame.font.SysFont('Courier New', 80, bold=True, italic=True)

        pygame.mixer.init()
        self.readySound = pygame.mixer.Sound("sfx/Ready.wav")
        self.goSound = pygame.mixer.Sound("sfx/Go.wav")
        self.skidSound = pygame.mixer.Sound("sfx/Skid.wav")
        self.skidSound.set_volume(0.3)
        self.collisionSound = pygame.mixer.Sound("sfx/Collision.wav")
        self.collisionSound.set_volume(0.4)

        som_motor_base = pygame.mixer.Sound("sfx/Engine.wav")
        versoesMotor = self._gerarPitchMotor(som_motor_base, steps=2, pitchMin=1.0, pitchMax=1.20)
        som_motor_agudo = versoesMotor[1]

        self.engineChannelLow = pygame.mixer.Channel(0)
        self.engineChannelHigh = pygame.mixer.Channel(2)
        self.skidChannel = pygame.mixer.Channel(1)
        self.collisionChannel = pygame.mixer.Channel(3)

        self.engineChannelLow.play(som_motor_base, loops=-1)
        self.engineChannelHigh.play(som_motor_agudo, loops=-1)
        
        self.engineChannelLow.set_volume(0.0)
        self.engineChannelHigh.set_volume(0.0)

        self.collisionCooldown = 0

        self.hasPlayedReady3 = False
        self.hasPlayedReady2 = False
        self.hasPlayedReady1 = False
        self.hasPlayedGo = False

        self.roadWidth = 2000
        self.segmentLength = 200
        self.cameraDepth = 0.84
        self.showSegments = 300
        
        self.track = Track(self.segmentLength)
        self._loadAssets()

    def _loadAssets(self):
        self.trackSprites = {}
        try:
            self.trackSprites['PD'] = pygame.image.load("sprites/track/PD.png").convert_alpha()
            self.trackSprites['PE'] = pygame.image.load("sprites/track/PE.png").convert_alpha()
            self.trackSprites['START'] = pygame.image.load("sprites/track/start.png").convert_alpha()
            
            self.trackSprites['HEUER'] = pygame.image.load("sprites/track/sponsors/heuer.png").convert_alpha()
            self.trackSprites['LONGHI'] = pygame.image.load("sprites/track/sponsors/longhi.png").convert_alpha()
            self.trackSprites['MARELLI'] = pygame.image.load("sprites/track/sponsors/marelli.png").convert_alpha()
            self.trackSprites['MARLBORO'] = pygame.image.load("sprites/track/sponsors/marlboro.png").convert_alpha()
            self.trackSprites['PIRELLI'] = pygame.image.load("sprites/track/sponsors/pirelli.png").convert_alpha()
            self.trackSprites['SHELL'] = pygame.image.load("sprites/track/sponsors/shell.png").convert_alpha()
            self.trackSprites['TYRE'] = pygame.image.load("sprites/track/tyre.png").convert_alpha()
            
        except FileNotFoundError:
            print("Aviso: Faltam imagens das placas ou patrocínios!")

        self.startLights = {}
        try:
            self.startLights['3'] = pygame.image.load("sprites/track/start/3.png").convert_alpha()
            self.startLights['2'] = pygame.image.load("sprites/track/start/2.png").convert_alpha()
            self.startLights['1'] = pygame.image.load("sprites/track/start/1.png").convert_alpha()
            self.startLights['GO'] = pygame.image.load("sprites/track/start/GO.png").convert_alpha()
                
        except FileNotFoundError:
            print("Aviso: Imagens do semáforo (1, 2, 3, GO) não encontradas!")

        self.carModels = ['288GTO', '959', 'Testarossa', 'XJR15']
        self.playerModel = '959'

        self.allRawCarSprites = {}
        diretorioAtual = os.path.dirname(os.path.abspath(__file__))

        for model in self.carModels:
            basePath = os.path.join(diretorioAtual, "sprites", "cars", model)
            try:
                self.allRawCarSprites[model] = {
                    'S':  [pygame.image.load(os.path.join(basePath, 'S.png')).convert_alpha(),   pygame.image.load(os.path.join(basePath, 'S2.png')).convert_alpha()],
                    'L':  [pygame.image.load(os.path.join(basePath, 'L.png')).convert_alpha(),   pygame.image.load(os.path.join(basePath, 'L2.png')).convert_alpha()],
                    'SL': [pygame.image.load(os.path.join(basePath, 'SL.png')).convert_alpha(),  pygame.image.load(os.path.join(basePath, 'SL2.png')).convert_alpha()],
                    'R':  [pygame.image.load(os.path.join(basePath, 'R.png')).convert_alpha(),   pygame.image.load(os.path.join(basePath, 'R2.png')).convert_alpha()],
                    'SR': [pygame.image.load(os.path.join(basePath, 'SR.png')).convert_alpha(),  pygame.image.load(os.path.join(basePath, 'SR2.png')).convert_alpha()]
                }
            except FileNotFoundError:
                print(f"Aviso: Sprites do carro {model} não encontrados!")
                continue

        self.set_player_car(self.playerModel)

    def set_player_car(self, model):
        """Define o carro do jogador e redimensiona os sprites e efeitos correspondentes."""
        self.playerModel = model
        carTargetWidth = 300 
        diretorioAtual = os.path.dirname(os.path.abspath(__file__))
        
        imagemReta = self.allRawCarSprites[model]['S'][0]
        fatorEscala = carTargetWidth / imagemReta.get_width()
        
        self.carSprites = {}
        for state, images in self.allRawCarSprites[model].items():
            self.carSprites[state] = []
            for img in images:
                nW = int(img.get_width() * fatorEscala)
                nH = int(img.get_height() * fatorEscala)
                self.carSprites[state].append(pygame.transform.scale(img, (nW, nH)))

        self.smokeSprites = {'S': [], 'L': [], 'R': []}
        try:
            basePathPlayer = os.path.join(diretorioAtual, "sprites", "cars", model)
            for i in range(1, 4): 
                imgS = pygame.image.load(os.path.join(basePathPlayer, 'effects', f'S{i}.png')).convert_alpha()
                imgL = pygame.image.load(os.path.join(basePathPlayer, 'effects', f'L{i}.png')).convert_alpha()
                imgR = pygame.image.load(os.path.join(basePathPlayer, 'effects', f'R{i}.png')).convert_alpha()
                
                self.smokeSprites['S'].append(pygame.transform.scale(imgS, (int(imgS.get_width() * fatorEscala), int(imgS.get_height() * fatorEscala))))
                self.smokeSprites['L'].append(pygame.transform.scale(imgL, (int(imgL.get_width() * fatorEscala), int(imgL.get_height() * fatorEscala))))
                self.smokeSprites['R'].append(pygame.transform.scale(imgR, (int(imgR.get_width() * fatorEscala), int(imgR.get_height() * fatorEscala))))
        except FileNotFoundError:
            print(f"Aviso: Efeitos de fumaça não encontrados para o modelo {model}!")

    def _loadBackground(self, path, scale=2):
        """Carrega o fundo de uma pista específica."""
        try:
            bgOriginal = pygame.image.load(path).convert_alpha()
            novoW = bgOriginal.get_width() * scale
            novoH = bgOriginal.get_height() * scale
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

    def _muteEngine(self):
        """Silencia todos os canais de áudio do motor."""
        self.engineChannelLow.set_volume(0.0)
        self.engineChannelHigh.set_volume(0.0)
        self.skidChannel.stop()


    def _gerarPitchMotor(self, baseSound, steps=40, pitchMin=0.8, pitchMax=1.20):
        """
        Gera versões do som usando interpolação linear (suavização) 
        para evitar que o áudio fique crackelando.
        """
        try:
            audioArray = pygame.sndarray.array(baseSound)
        except Exception as e:
            print(f"Erro ao processar áudio: {e}")
            return [baseSound] * steps

        generatedSounds = []
        pitches = np.linspace(pitchMin, pitchMax, steps)
        
        tOld = np.arange(len(audioArray))

        for pitch in pitches:
            tNew = np.arange(0, len(audioArray) - 1, pitch)
            
            if len(audioArray.shape) == 2:
                newArray = np.zeros((len(tNew), 2), dtype=np.float32)
                newArray[:, 0] = np.interp(tNew, tOld, audioArray[:, 0])
                newArray[:, 1] = np.interp(tNew, tOld, audioArray[:, 1])
            else:
                newArray = np.interp(tNew, tOld, audioArray).astype(np.float32)

            newArray = newArray.astype(audioArray.dtype)
            newArray = np.ascontiguousarray(newArray)
            
            generatedSounds.append(pygame.sndarray.make_sound(newArray))
            
        return generatedSounds

    def draw_hud(self, text, font, color, x, y, align="left"):
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
                    self.windowSurface.blit(surface_outline, (rect.x + dx, rect.y + dy))

        self.windowSurface.blit(surface_color, rect)

    def run(self, track_id='autodromo'):
        from tracks_data import get_track
        track_data = get_track(track_id)
        
        self.track.buildTrack(track_data)
        self._loadBackground(track_data['background'], track_data.get('bg_scale', 6))
        
        self.sky_top = track_data['sky_top']
        self.sky_bottom = track_data['sky_bottom']
        
        lines = self.track.lines
        totalSegments = len(lines)
        trackLength = totalSegments * self.segmentLength
        last_lap = 1
        last_player_pos = None
        center_msg = ""
        center_msg_timer = 0

        linha_largada_z = 25 * self.segmentLength 
        primeira_fileira_z = linha_largada_z - (14 * self.segmentLength) 
        distancia_entre_fileiras = 2000

        posicao_jogador = 16
        fileira_jogador = posicao_jogador // 2
        
        player_virtual_z = primeira_fileira_z - (fileira_jogador * distancia_entre_fileiras)
        playerVisualZ = 780 
        absolutePos = player_virtual_z - playerVisualZ 
        
        maxLaps = 99999 if self.dev_mode else track_data.get('laps', 5)
        playerX = 1.1
        playerY = 1250
        playerPitchBase = 150
        smoothPitch = 0.0
        
        speed = 0.0
        basePlayerMaxSpeed = 260 
        maxSpeed = basePlayerMaxSpeed
        draftBonus = 0.0
        
        animTimer = 0
        turnTimer = 0
        is_drifting = False

        self.countdownStartTick = pygame.time.get_ticks()
        self.finishStartTick = 0
        self.opponents = []

        if self.dev_mode:
            self.raceState = 'RACING'
        else:
            self.raceState = 'COUNTDOWN'
            
            bot_models_list = []
            for model in self.carModels:
                if model == self.playerModel:
                    bot_models_list.extend([model] * 3)
                else:
                    bot_models_list.extend([model] * 4)
                    
            random.shuffle(bot_models_list)

            slots_ocupados = 0
            for i in range(15):
                if i == posicao_jogador:
                    continue
                    
                baseSpeed = 258 + ((15 - i) * 0.5) 
                
                fileira = i // 2 
                start_z = primeira_fileira_z - (fileira * distancia_entre_fileiras)
                pos_x = -1.1 if i % 2 == 0 else 1.1
                
                self.opponents.append({
                    'id': i,
                    'model': bot_models_list[slots_ocupados],
                    'z': start_z,
                    'totalZ': start_z, 
                    'x': pos_x,
                    'targetX': pos_x,
                    'speed': 0.0, 
                    'baseMaxSpeed': baseSpeed, 
                    'accel': 2.0 + ((15 - i) * 0.13), 
                    'decisionTimer': random.randint(0, 100),
                    'lateralDelta': 0.0
                })
                slots_ocupados += 1
                
        fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        fade_surface.fill((0, 0, 0))
        fade_alpha = 255
        fading_in = True
        is_aborting = False

        self.clock.tick()
        while True:
            currentTick = pygame.time.get_ticks()

            if self.collisionCooldown > 0:
                self.collisionCooldown -= 1
            
            ratioVelocidade = max(0.0, min(speed / basePlayerMaxSpeed, 1.0))
            
            masterVolume = 0.2
            
            volumeLow = ((1.0 - ratioVelocidade) ** 0.5) * masterVolume
            volumeHigh = (ratioVelocidade ** 0.5) * masterVolume
            
            if ratioVelocidade < 0.1:
                volumeLow = max(volumeLow, masterVolume * 0.7)
                
            self.engineChannelLow.set_volume(volumeLow)
            self.engineChannelHigh.set_volume(volumeHigh)
            
            for event in pygame.event.get([pygame.QUIT, pygame.KEYDOWN]):
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    is_aborting = True

            keys = pygame.key.get_pressed()
            
            cmd_up = keys[pygame.K_UP]
            cmd_down = keys[pygame.K_DOWN]
            cmd_left = keys[pygame.K_LEFT]
            cmd_right = keys[pygame.K_RIGHT]
            
            pos = absolutePos % trackLength 
            currentLap = int(absolutePos // trackLength) + 1
            if currentLap > last_lap and currentLap <= maxLaps:
                center_msg = f"LAP: {currentLap}"
                center_msg_timer = 120
                last_lap = currentLap

            startPos = int(pos // self.segmentLength)
            startSegment = lines[startPos % totalSegments]
            rawCurve = startSegment.curve
            absCurve = abs(rawCurve)
            
            if self.raceState == 'COUNTDOWN':
                cmd_up = cmd_down = cmd_left = cmd_right = False
                
                elapsed = currentTick - self.countdownStartTick
                if elapsed >= 3000: 
                    self.raceState = 'RACING'
                    
            elif self.raceState == 'RACING':
                if currentLap > maxLaps:
                    self.raceState = 'FINISHED'
                    self.finishStartTick = currentTick
                    
                    playerRealZ = absolutePos + playerVisualZ
                    distances = [playerRealZ] + [o['totalZ'] for o in self.opponents]
                    distances.sort(reverse=True)
                    self.final_position = distances.index(playerRealZ) + 1
                    
            elif self.raceState == 'FINISHED':
                autoMaxSpeed = 220
                
                cmd_up = speed < autoMaxSpeed
                cmd_down = speed > autoMaxSpeed + 10
                
                autoCurve = rawCurve
                autoAbsCurve = absCurve
                
                if autoAbsCurve > 1.0:
                    autoTargetX = -0.8 if autoCurve > 0 else 0.8
                else:
                    autoTargetX = 0.0
                
                for opp in self.opponents:
                    dz = opp['dz']
                    if 0 < dz < 2000 and abs(playerX - opp['x']) < 1.2:
                        autoTargetX = 1.2 if playerX >= opp['x'] else -1.2
                        break
                
                autoCentrifugal = (autoAbsCurve ** 0.6) * 0.015 * (speed / max(maxSpeed, 1)) if autoAbsCurve > 0 else 0

                if playerX < autoTargetX - 0.05:
                    cmd_right = True
                    cmd_left = False
                elif playerX > autoTargetX + 0.05:
                    cmd_left = True
                    cmd_right = False
                else:
                    cmd_left = cmd_right = False
                
                if currentTick - self.finishStartTick > 5000:
                    self._muteEngine()

                    final_time = self.finishStartTick - self.countdownStartTick - 3000
                    return {
                        'position': self.final_position, 
                        'time': max(0, final_time)
                    }

            isDrafting = False
            playerVirtualZ = pos + playerVisualZ 

            if absCurve <= 2.0 and speed >= 240:
                for opp in self.opponents:
                    dz = opp['z'] - playerVirtualZ
                    if dz < 0: dz += trackLength 
                    if 50 < dz < 7000 and abs(opp['x'] - playerX) < 0.3:
                        isDrafting = True
                        break
            
            if isDrafting: draftBonus = min(14.0, draftBonus + 0.15)
            else: draftBonus = max(0.0, draftBonus - 0.05)
            maxSpeed = basePlayerMaxSpeed + draftBonus

            trackDriftForce = (absCurve ** 0.6) * 0.015
            currentCentrifugal = trackDriftForce * (speed / maxSpeed)

            isOffroad = abs(playerX) > 2.3
            currentMaxSpeed = maxSpeed * 0.4 if isOffroad else maxSpeed

            accel_power = 3.0
            if self.raceState == 'RACING':
                tempo_de_corrida = currentTick - self.countdownStartTick - 3000
                
                if 0 <= tempo_de_corrida < 2000: 
                    accel_power = 0.2 + (tempo_de_corrida / 2000.0) * 2.5
            
            if cmd_up: speed += accel_power
            elif cmd_down: speed -= 8
            else:
                if speed > 0: speed -= 2
                elif speed < 0: speed += 2

            steerState = 'S'
            baseSteer = 0.07
            steerCap = 0.10
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
            
            for opp in self.opponents:
                if self.raceState == 'COUNTDOWN':
                    opp['speed'] = 0
                    opp['lateralDelta'] = 0.0
                else:
                    distFromPlayer = opp['z'] - pos
                    if distFromPlayer > trackLength / 2: distFromPlayer -= trackLength
                    elif distFromPlayer < -trackLength / 2: distFromPlayer += trackLength
                    
                    if distFromPlayer < -6000: opp['maxSpeed'] = opp['baseMaxSpeed'] + 3
                    elif distFromPlayer > 1000: opp['maxSpeed'] = opp['baseMaxSpeed'] - 5
                    else: opp['maxSpeed'] = opp['baseMaxSpeed']

                    if opp['speed'] < opp['maxSpeed']: opp['speed'] += opp.get('accel', 2.5)
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
                    
                    if 0 < distToPlayer < 2000: 
                        if abs(playerX - opp['x']) < 1.2 and opp['speed'] > speed:
                            opp['targetX'] = -1.2 if playerX >= 0 else 1.2
                            opp['decisionTimer'] = 60 
                            
                        if 0 < distToPlayer < 200 and opp['speed'] > speed and abs(playerX - opp['x']) < 0.6:
                            opp['speed'] = speed 
                            
                    elif -400 < distToPlayer <= 0 and abs(playerX - opp['x']) < 0.9: 
                        opp['targetX'] = 1.2 if opp['x'] >= playerX else -1.2
                        opp['decisionTimer'] = 60
                    
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
                        targetOppSpeed = opp['maxSpeed'] - (oppDriftForce * 900)
                        if opp['speed'] > targetOppSpeed: opp['speed'] -= 5.0

                    opp['x'] = max(-1.8, min(opp['x'], 1.8))
                
                opp['z'] = (opp['z'] + opp['speed']) % trackLength
                opp['totalZ'] += opp['speed']
                dzOpp = opp['z'] - pos
                if dzOpp < 0: dzOpp += trackLength 
                opp['dz'] = dzOpp 
                
                if self.raceState == 'RACING':
                    if playerVisualZ < dzOpp < playerVisualZ + 400 and abs(playerX - opp['x']) < 0.50:

                        if self.collisionCooldown == 0:
                            self.collisionChannel.play(self.collisionSound)
                            self.collisionCooldown = 30

                        if speed > opp['speed']:
                            speed *= 0.3
                        else:
                            opp['speed'] *= 0.3

            speed = max(0, min(speed, currentMaxSpeed))
            absolutePos += speed
            pos = absolutePos % trackLength 

            self.opponents.sort(key=lambda o: o['dz'], reverse=True)

            lookahead = 3
            segmentoFrente = (startPos + lookahead) % totalSegments
            dy = lines[segmentoFrente].y - lines[startPos].y
            pitchAlvo = playerPitchBase + (-dy * 0.5)
            smoothPitch += (pitchAlvo - smoothPitch) * 0.1 

            camHeight = lines[startPos].y + playerY
            maxY = WINDOW_HEIGHT

            self.bgOffsetX += rawCurve * speed * 0.008
            self.backgroundRect.x = -(int(self.bgOffsetX) % self.bgWidth)

            farNode = startPos + self.showSegments - 1
            farLine = lines[farNode % totalSegments]
            farCamZ = pos - (totalSegments * self.segmentLength if farNode >= totalSegments else 0)
            
            if farLine.z - farCamZ > 0.1:
                farScale = self.cameraDepth / (farLine.z - farCamZ)
                farY = ((1 - farScale * (farLine.y - camHeight)) * WINDOW_HEIGHT / 2) - smoothPitch
            else:
                farY = WINDOW_HEIGHT / 2
            
            drawStripedSky(self.windowSurface, self.sky_top, self.sky_bottom, SKY_BAND_HEIGHT, farY)
            self.backgroundRect.bottom = int(farY) + 1 
            self.windowSurface.blit(self.backgroundSurface, self.backgroundRect)

            worldX = 0.0  
            dx = 0.0  
            playerXWorld = playerX * 1000

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

            renderables = []
            
            for n in range(startPos, startPos + self.showSegments):
                line = lines[n % totalSegments]
                if line.sprite and line.Y < WINDOW_HEIGHT:
                    dz = line.z - pos
                    if dz < 0: dz += trackLength
                    renderables.append({'type': 'sign', 'dz': dz, 'line': line})

            for opp in self.opponents:
                dz = opp['dz']
                if 0 < dz < (self.showSegments - 2) * self.segmentLength:
                    renderables.append({'type': 'opp', 'dz': dz, 'opp': opp})

            renderables.sort(key=lambda x: x['dz'], reverse=True)

            for obj in renderables:
                
                if obj['type'] == 'sign':
                    line = obj['line']
                    sprite_img = self.trackSprites.get(line.sprite)
                    
                    if sprite_img and line.scale > 0:
                        
                        if line.sprite == 'START':
                            targetSignW = line.W * 1.5
                        elif line.sprite in ['PD', 'PE']:
                            targetSignW = line.W * 0.25
                        elif line.sprite == 'TYRE':
                            targetSignW = line.W * 0.175
                        else:
                            targetSignW = line.W * 0.45
                            
                        escalaSign = targetSignW / sprite_img.get_width()
                        
                        finalW = int(sprite_img.get_width() * escalaSign)
                        finalH = int(sprite_img.get_height() * escalaSign)
                        
                        if finalW > 0 and finalH > 0:
                            destX = line.X + (line.spriteX * line.W)
                            
                            if line.sprite == 'START':
                                renderX = destX
                            else:
                                renderX = destX - (finalW / 2)
                                
                            renderY = line.Y - finalH
                            
                            clipH = renderY + finalH - line.clip
                            if clipH < 0: clipH = 0
                            
                            if clipH < finalH:
                                try:
                                    scaledSprite = pygame.transform.scale(sprite_img, (finalW, finalH))
                                    if clipH > 0:
                                        cropSurface = scaledSprite.subsurface(0, 0, finalW, int(finalH - clipH))
                                        self.windowSurface.blit(cropSurface, (int(renderX), int(renderY)))
                                    else:
                                        self.windowSurface.blit(scaledSprite, (int(renderX), int(renderY)))
                                except ValueError:
                                    pass

                elif obj['type'] == 'opp':
                    opp = obj['opp']
                    segIdx = int(opp['z'] // self.segmentLength) % totalSegments
                    
                    line1 = lines[segIdx]
                    line2 = lines[(segIdx + 1) % totalSegments]
                    
                    if line1.scale == 0 or line2.scale == 0: continue
                    
                    percent = (opp['z'] % self.segmentLength) / self.segmentLength
                    destX = line1.X + (line2.X - line1.X) * percent
                    destY = line1.Y + (line2.Y - line1.Y) * percent
                    destW = line1.W + (line2.W - line1.W) * percent
                    
                    baseTargetW = destW * 0.28
                    
                    baseSpriteW = self.allRawCarSprites[opp['model']]['S'][0].get_width()
                    escalaDistancia = baseTargetW / baseSpriteW

                    turnForce = line1.curve + (opp.get('lateralDelta', 0.0) * 80.0)
                    oppSteer = 'S'
                    
                    if turnForce < -1.0: oppSteer = 'L' if turnForce < -3.0 else 'SL'
                    elif turnForce > 1.0: oppSteer = 'R' if turnForce > 3.0 else 'SR'
                    
                    oppFrame = 0 if (int(opp['z']) % 400) < 200 else 1
                    
                    currentOppSprite = self.allRawCarSprites[opp['model']][oppSteer][oppFrame]
                    
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

            limite_curva_fechada = 3.0 
            
            if absCurve > limite_curva_fechada and steerState in ['L', 'R'] and speed > 180:
                is_drifting = True  
            elif absCurve < 1.0 or speed < 120 or steerState == 'S':
                is_drifting = False 
                
            tempo_corrida = currentTick - self.countdownStartTick - 3000
            is_patinando_largada = (self.raceState == 'RACING' and 0 <= tempo_corrida < 2000 and cmd_up)

            if is_drifting or is_patinando_largada:
                if not self.skidChannel.get_busy():
                    self.skidChannel.play(self.skidSound, loops=-1)
            else:
                self.skidChannel.stop()
            
            is_fumaca_curva = (is_drifting and steerState in ['L', 'R', 'SL', 'SR'])
            is_fumaca_esporadica = is_fumaca_curva and (random.random() < 0.5)

            if (is_patinando_largada or is_fumaca_esporadica) and self.smokeSprites.get('S'):
                
                if is_fumaca_curva:
                    estado_fumaca = 'L' if steerState in ['L', 'SL'] else 'R'
                else:
                    estado_fumaca = 'S'
                
                frame_fumaca = (currentTick // 80) % 3 
                img_fumaca = self.smokeSprites[estado_fumaca][frame_fumaca]
                rect_fumaca = img_fumaca.get_rect()
                
                rect_fumaca.bottom = carRect.bottom
                
                if estado_fumaca == 'S':
                    rect_fumaca.centerx = carRect.centerx
                elif estado_fumaca == 'L':
                    rect_fumaca.left = carRect.left
                elif estado_fumaca == 'R':
                    rect_fumaca.right = carRect.right
                    
                self.windowSurface.blit(img_fumaca, rect_fumaca)

            if draftBonus > 0.5:
                speedColor, digiDark = self.digiBlue, self.digiBlueDark
            else:
                speedColor, digiDark = self.digiGreen, self.digiGreenDark

            margem_lateral = 25
            base_y = 110
            
            num_w, num_h = 175, 85 
            unit_w, unit_h = 92, 38 
            espacamento_entre_blocos = 12

            largura_total = num_w + espacamento_entre_blocos + unit_w
            vx_num = WINDOW_WIDTH - largura_total - margem_lateral 
            
            pygame.draw.rect(self.windowSurface, (0, 0, 0), (vx_num, base_y - num_h, num_w + 18, num_h))
            
            self.draw_hud("888", self.speedFont, digiDark, vx_num, base_y - 82, "left")
            str_speed = f"{int(speed):03d}"
            self.draw_hud(str_speed, self.speedFont, speedColor, vx_num, base_y - 82, "left")

            vx_unit = vx_num + num_w + espacamento_entre_blocos
            pygame.draw.rect(self.windowSurface, (0, 0, 0), (vx_unit, base_y - unit_h, unit_w, unit_h))
            
            self.draw_hud("KM/H", self.hudFont, speedColor, vx_unit + 6, base_y - 28, "left")

            if self.raceState == 'COUNTDOWN':
                race_time = 0
            elif self.raceState == 'RACING':
                race_time = currentTick - self.countdownStartTick - 3000
            elif self.raceState == 'FINISHED':
                race_time = self.finishStartTick - self.countdownStartTick - 3000

            race_time = max(0, race_time)
            
            minutos = race_time // 60000
            segundos = (race_time % 60000) // 1000
            centesimos = (race_time % 1000) // 10  
            
            time_str = f"{minutos:02d}'{segundos:02d}''{centesimos:02d}"
            
            timer_y = base_y + 15
            
            timer_right_x = vx_unit + unit_w 
            
            self.draw_hud(time_str, self.lapFont, (255, 255, 255), timer_right_x, timer_y, "right")

            bottom_y = WINDOW_HEIGHT - 60
            
            if self.dev_mode:
                self.draw_hud("FREE DRIVE", self.lapFont, (255, 255, 50), 30, bottom_y, "left")
                self.draw_hud(track_data['name'].upper(), self.hudFont, (180, 180, 180), WINDOW_WIDTH - 30, bottom_y + 5, "right")
            else:
                displayLap = min(currentLap, maxLaps)
                self.draw_hud(f"LAP {displayLap}/{maxLaps}", self.lapFont, (255, 255, 255), 30, bottom_y, "left")
                
                if self.raceState == 'FINISHED':
                    player_pos = self.final_position
                else:
                    playerRealZ = absolutePos + playerVisualZ
                    distances = [playerRealZ] + [o['totalZ'] for o in self.opponents]
                    distances.sort(reverse=True)
                    player_pos = distances.index(playerRealZ) + 1
                    
                sufixos = {1: "ST", 2: "ND", 3: "RD"}
                pos_suffix = sufixos.get(player_pos, "TH")
                self.draw_hud(f"{player_pos}{pos_suffix}", self.lapFont, (255, 255, 255), WINDOW_WIDTH - 30, bottom_y, "right")

            if not self.dev_mode:
                if last_player_pos is None:
                    last_player_pos = player_pos
                elif player_pos != last_player_pos:
                    center_msg = f"{player_pos}{pos_suffix}"
                    center_msg_timer = 120
                    last_player_pos = player_pos
                    
                if center_msg_timer > 0:
                    if self.raceState == 'RACING':
                        if (center_msg_timer // 10) % 2 == 0:
                            self.draw_hud(center_msg, self.lapFont, (255, 255, 255), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 120, "center")
                    
                    center_msg_timer -= 1

                elapsed_start = currentTick - self.countdownStartTick
                
                if elapsed_start < 3500:
                    light_sprite = None
                    
                    if elapsed_start < 1000: 
                        light_sprite = self.startLights.get('3')
                        if not self.hasPlayedReady3:
                            self.readySound.play()
                            self.hasPlayedReady3 = True
                    elif elapsed_start < 2000: 
                        light_sprite = self.startLights.get('2')
                        if not self.hasPlayedReady2:
                            self.readySound.play()
                            self.hasPlayedReady2 = True
                    elif elapsed_start < 3000: 
                        light_sprite = self.startLights.get('1')
                        if not self.hasPlayedReady1:
                            self.readySound.play()
                            self.hasPlayedReady1 = True
                    elif elapsed_start < 3500: 
                        light_sprite = self.startLights.get('GO')
                        if not self.hasPlayedGo:
                            self.goSound.play()
                            self.hasPlayedGo = True
                        
                    if light_sprite:
                        light_rect = light_sprite.get_rect(center=(WINDOW_WIDTH // 2, 300))
                        self.windowSurface.blit(light_sprite, light_rect)

                if self.raceState == 'FINISHED':
                    if (currentTick // 500) % 2 == 0:
                        self.draw_hud("FINISH!", self.finishFont, (255, 255, 255), WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50, "center")

            dt = self.clock.get_time()

            if dt > 50: dt = 50
            
            if fading_in:
                fade_alpha -= (255 / 1000) * dict
                if fade_alpha <= 0:
                    fade_alpha = 0
                    fading_in = False
                    
            elif is_aborting:
                fade_alpha += (255 / 500) * dt
                if fade_alpha >= 255:
                    self._muteEngine()
                    return False
                    
            elif self.raceState == 'FINISHED':
                elapsed_finish = currentTick - self.finishStartTick
                if elapsed_finish > 4000:
                    fade_alpha += (255 / 1000) * dt
                    if fade_alpha >= 255:
                        fade_alpha = 255
            
            if fade_alpha > 0:
                fade_surface.set_alpha(int(fade_alpha))
                self.windowSurface.blit(fade_surface, (0, 0))

            pygame.display.update()
            self.clock.tick(60)