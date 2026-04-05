import pygame
from game import GameWindow

# ADICIONE O CarInfoMenu AQUI NOS IMPORTS
from menu import StartMenu, CarSelectMenu, TrackSelectMenu, CarInfoMenu 

if __name__ == "__main__":
    pygame.init()
    
    jogo = GameWindow(dev_mode=False)
    
    menu_inicial = StartMenu(jogo.windowSurface)
    menu_carro = CarSelectMenu(jogo.windowSurface)
    menu_pista = TrackSelectMenu(jogo.windowSurface)
    
    # 1. Instancie o novo menu aqui
    menu_carro_info = CarInfoMenu(jogo.windowSurface) 
    
    menu_inicial.run()
    
    while True:
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(loops=-1, fade_ms=1000)
            
        carro_id = menu_carro.run()
        jogo.set_player_car(carro_id) 
        
        menu_carro_info.run(carro_id)
        
        track_id = menu_pista.run()
        
        pygame.mixer.music.fadeout(1000)
        jogo.run(track_id)