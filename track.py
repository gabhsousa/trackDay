import pygame
from typing import List
from config import *
from utils import easeInOut


class Line:
    def __init__(self, index):
        self.i = index
        self.x = self.y = self.z = 0.0  
        self.X = self.Y = self.W = 0.0  
        self.scale = 0.0  
        self.curve = 0.0  
        self.clip = 0.0  

        self.sprite = None  
        self.spriteX = 0.0

        self.grassColor: pygame.Color = DARK_GRASS
        self.rumbleColor: pygame.Color = BLACK_RUMBLE
        self.roadColor: pygame.Color = DARK_ROAD

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


class Track:
    def __init__(self, segmentLength: int):
        self.lines: List[Line] = []
        self.segmentLength = segmentLength
        
        self.dark_grass = DARK_GRASS
        self.light_grass = LIGHT_GRASS
        self.white_rumble = WHITE_RUMBLE
        self.black_rumble = BLACK_RUMBLE
        self.dark_road = DARK_ROAD
        self.light_road = LIGHT_ROAD

    def addSegment(self, curve: float, y: float):
        n = len(self.lines)
        line = Line(n)
        line.z = n * self.segmentLength + 0.00001
        line.curve = curve
        line.y = y
        line.grassColor = self.light_grass if (n // 3) % 2 else self.dark_grass
        line.rumbleColor = self.white_rumble if (n // 3) % 2 else self.black_rumble
        line.roadColor = self.light_road if (n // 3) % 2 else self.dark_road
        self.lines.append(line)

    def addRoad(self, enter: int, hold: int, leave: int, curve: float, y: float):
        startY = self.lines[-1].y if len(self.lines) > 0 else 0.0
        total = enter + hold + leave
        currentSegment = 0
        
        start_n = len(self.lines)

        for i in range(enter):
            curveTime = i / enter if enter > 0 else 0
            yTime = currentSegment / total if total > 0 else 0
            self.addSegment(curve * easeInOut(curveTime), startY + (y - startY) * easeInOut(yTime))
            currentSegment += 1

        for i in range(hold):
            yTime = currentSegment / total if total > 0 else 0
            currentY = startY + (y - startY) * easeInOut(yTime)
            self.addSegment(curve, currentY)
            currentSegment += 1

        for i in range(leave):
            curveTime = i / leave if leave > 0 else 0
            yTime = currentSegment / total if total > 0 else 0
            self.addSegment(curve * easeInOut(1 - curveTime), startY + (y - startY) * easeInOut(yTime))
            currentSegment += 1

        if abs(curve) > 1.0:
            sign_type = 'PD' if curve > 0 else 'PE'
            sign_x = -1.5 if curve > 0 else 1.5
            
            sign_start = max(0, start_n - 20)
            sign_end = start_n + enter + (hold)
            
            for i in range(sign_start, sign_end, 10):
                if i < len(self.lines):
                    self.lines[i].sprite = sign_type
                    self.lines[i].spriteX = sign_x

    def buildTrack(self, track_data: dict = None):
        self.lines = []
        
        if track_data is None:
            from tracks_data import get_track
            track_data = get_track('autodromo')
        
        colors = track_data.get('colors', {})
        if colors:
            self.dark_grass = pygame.Color(*colors['dark_grass'])
            self.light_grass = pygame.Color(*colors['light_grass'])
            self.dark_road = pygame.Color(*colors['dark_road'])
            self.light_road = pygame.Color(*colors['light_road'])
            self.white_rumble = pygame.Color(*colors['white_rumble'])
            self.black_rumble = pygame.Color(*colors['black_rumble'])
        
        for road in track_data['layout']:
            enter, hold, leave, curve, y = road
            self.addRoad(enter, hold, leave, curve, y)
        
        start_seg = track_data.get('start_segment', 25)
        if start_seg < len(self.lines):
            self.lines[start_seg].sprite = 'START'
            self.lines[start_seg].spriteX = -1.8
            for i in range(start_seg, min(start_seg + 2, len(self.lines))):
                self.lines[i].roadColor = pygame.Color(255, 255, 255)
        
        sponsors = track_data.get('sponsors', ['PIRELLI'])
        self._placeSponsors(sponsors)

    def _placeSponsors(self, sponsors):
        sponsor_idx = 0
        
        for i in range(40, len(self.lines)):
            line = self.lines[i]
            
            if line.sprite is not None:
                continue
                
            area_restrita = False
            for k in range(max(0, i - 12), min(len(self.lines), i + 5)):
                if self.lines[k].sprite in ['PD', 'PE']:
                    area_restrita = True
                    break
                    
            if area_restrita:
                continue

            if abs(line.curve) > 2.0:
                lado_fora = -1.5 if line.curve > 0 else 1.5
                line.sprite = 'TYRE'
                line.spriteX = lado_fora
                
            else:
                if i % 35 == 0:
                    line.sprite = sponsors[sponsor_idx % len(sponsors)]
                    line.spriteX = -1.5
                    sponsor_idx += 1
                else:
                    line.sprite = 'TYRE'
                    line.spriteX = 1.5