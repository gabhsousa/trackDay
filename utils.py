import pygame
from typing import Tuple
from config import WINDOW_WIDTH, WINDOW_HEIGHT

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

def easeInOut(t: float) -> float: 
    return t * t * (3 - 2 * t)