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

    def addSegment(self, curve: float, y: float):
        n = len(self.lines)
        line = Line(n)
        line.z = n * self.segmentLength + 0.00001
        line.curve = curve
        line.y = y
        line.grassColor = LIGHT_GRASS if (n // 3) % 2 else DARK_GRASS
        line.rumbleColor = WHITE_RUMBLE if (n // 3) % 2 else BLACK_RUMBLE
        line.roadColor = LIGHT_ROAD if (n // 3) % 2 else DARK_ROAD
        self.lines.append(line)

    def addRoad(self, enter: int, hold: int, leave: int, curve: float, y: float):
        startY = self.lines[-1].y if len(self.lines) > 0 else 0.0
        total = enter + hold + leave
        currentSegment = 0

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