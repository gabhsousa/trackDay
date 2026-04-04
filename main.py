import pygame
from game import GameWindow

if __name__ == "__main__":
    pygame.init()
    
    jogo = GameWindow()
    jogo.run()