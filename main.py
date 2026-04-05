import pygame
from game import GameWindow
from menu import StartMenu, CarSelectMenu, CarInfoMenu, TrackInfoMenu 

if __name__ == "__main__":
    pygame.init()
    jogo = GameWindow(dev_mode=False)
    
    menu_inicial = StartMenu(jogo.windowSurface)
    menu_carro = CarSelectMenu(jogo.windowSurface)
    menu_carro_info = CarInfoMenu(jogo.windowSurface) 
    menu_pista_info = TrackInfoMenu(jogo.windowSurface)
    
    campeonato = ["ITA", "AUS", "BRA"]
    
    musicas = {
        "MENU": "sfx/songs/menu.WAV",
        "ITA": "sfx/songs/menu.WAV",
        "AUS": "sfx/songs/angryMen.wav",
        "BRA": "sfx/songs/runaway.wav"
    }

    while True:
        pygame.mixer.music.load(musicas["MENU"])
        pygame.mixer.music.play(loops=-1, fade_ms=3000)
        
        menu_inicial.run()
        
        carro_id = menu_carro.run()
        jogo.set_player_car(carro_id) 
        menu_carro_info.run(carro_id)
        
        musica_atual = musicas["MENU"]

        for track_id in campeonato:
            nova_musica = musicas[track_id]
            
            if nova_musica != musica_atual:
                pygame.mixer.music.fadeout(1000)
                pygame.mixer.music.load(nova_musica)
                pygame.mixer.music.play(loops=-1, fade_ms=1000)
                musica_atual = nova_musica
            elif not pygame.mixer.music.get_busy():
                # Reinicia se tiver parado por algum motivo
                pygame.mixer.music.play(loops=-1, fade_ms=1000)

            menu_pista_info.run(track_id)
            
            completou_corrida = jogo.run(track_id)
            
            if not completou_corrida:
                break
        
        pygame.mixer.music.fadeout(2000)