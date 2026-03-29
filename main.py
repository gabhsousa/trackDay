import pygame
from game import GameWindow

if __name__ == "__main__":
    pygame.init()
    
    # Inicia a janela do jogo e roda o loop principal
    jogo = GameWindow()
    jogo.run()