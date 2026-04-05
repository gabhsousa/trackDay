import pygame
from game import GameWindow

if __name__ == "__main__":
    pygame.init()
    
    jogo = GameWindow(dev_mode=False)
    
    while True:
        track_id = jogo.trackSelect()
        jogo.run(track_id)