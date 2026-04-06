import pygame
from game import GameWindow
from menu import StartMenu, CarSelectMenu, CarInfoMenu, TrackInfoMenu, ResultsMenu

if __name__ == "__main__":
    pygame.init()
    jogo = GameWindow(dev_mode=False)
    
    menu_inicial = StartMenu(jogo.windowSurface)
    menu_carro = CarSelectMenu(jogo.windowSurface)
    menu_carro_info = CarInfoMenu(jogo.windowSurface) 
    menu_pista_info = TrackInfoMenu(jogo.windowSurface)
    menu_resultados = ResultsMenu(jogo.windowSurface)
    
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

        resultados_campeonato = []

        for track_id in campeonato:
            nova_musica = musicas[track_id]
            
            if nova_musica != musica_atual:
                pygame.mixer.music.fadeout(1000)
                pygame.mixer.music.load(nova_musica)
                pygame.mixer.music.play(loops=-1, fade_ms=1000)
                musica_atual = nova_musica
            elif not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(loops=-1, fade_ms=1000)

            menu_pista_info.run(track_id)
            
            dados_corrida = jogo.run(track_id)
            
            if not dados_corrida:
                resultados_campeonato = []
                break
            
            dados_corrida['track'] = track_id
            resultados_campeonato.append(dados_corrida)
        
        if len(resultados_campeonato) == len(campeonato):
            pygame.mixer.music.fadeout(1500)
            menu_resultados.run(resultados_campeonato)
        else:
            pygame.mixer.music.fadeout(1000)