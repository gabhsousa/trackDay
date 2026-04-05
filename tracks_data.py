"""
Definições de dados de todas as pistas do jogo.
Cada pista é um dicionário com layout, cores e configurações visuais.

Para criar uma nova pista:
  1. Copie um bloco existente
  2. Altere id, name, cores, sky e layout
  3. Layout: lista de tuplas (enter, hold, leave, curve, y)
     - enter/hold/leave: segmentos de transição e permanência
     - curve: intensidade da curva (negativo=esquerda, positivo=direita)
     - y: elevação (negativo=subida)
"""

TRACKS = [
    {
        "id": "BRA",
        "name": "Interlagos",
        "laps": 4,
        "background": "sprites/bg/L1.png",
        "bg_scale": 6,
        "sky_top": (0, 60, 150),
        "sky_bottom": (40, 180, 250),
        "colors": {
            "dark_grass": (0, 107, 0),
            "light_grass": (0, 123, 0),
            "dark_road": (95, 95, 95),
            "light_road": (107, 107, 107),
            "white_rumble": (255, 255, 255),
            "black_rumble": (200, 0, 0),
        },
        "sponsors": ['HEUER', 'LONGHI', 'MARELLI', 'MARLBORO', 'PIRELLI', 'SHELL'],
        "start_segment": 25,
        "layout": [
            (0, 100, 0, 0.0, 0.0),
            (0, 100, 0, 0.0, 0.0),
            (40, 10, 5, -20.0, -2500.0),
            (5, 40, 10, 15.0, -5000.0),
            (60, 80, 45, -3.0, -5500.0),
            (0, 200, 0, 0.0, -5500.0),
            (40, 40, 20, -10.0, -6000.0),
            (30, 40, 0, 0.0, -7000.0),
            (50, 40, 10, -6.0, -7000.0),
            (30, 100, 0, 0.0, -4500.0),
            (0, 70, 20, 5.0, -2500.0),
            (10, 30, 30, 15.0, -4500.0),
            (20, 50, 20, -25.0, -5000.0),
            (30, 80, 5, 0.0, -3000.0),
            (5, 50, 35, 10.0, -2500.0),
            (0, 40, 15, 12.0, -3500.0),
            (20, 70, 40, -6.0, -6500.0),
            (25, 100, 5, 0.0, -4000.0),
            (5, 40, 20, -14.0, -2500.0),
            (20, 80, 20, 0.0, -2000.0),
            (20, 100, 20, -1.0, -1000.0),
            (20, 150, 20, -1.0, -500.0),
            (30, 100, 30, 0.0, 0.0),
        ]
    },
    {
        "id": "ITA",
        "name": "Monza",
        "laps": 4,
        "background": "sprites/bg/L3.png",
        "bg_scale": 6,
        "sky_top": (0, 60, 150),
        "sky_bottom": (40, 180, 250),
        "colors": {
            "dark_grass": (57, 90, 0),
            "light_grass": (74, 107, 0),
            "dark_road": (95, 95, 95),
            "light_road": (107, 107, 107),
            "white_rumble": (255, 255, 255),
            "black_rumble": (200, 0, 0),
        },
        "sponsors": ['HEUER', 'LONGHI', 'MARELLI', 'MARLBORO', 'PIRELLI', 'SHELL'],
        "start_segment": 25,
        "layout": [
            (0, 350, 0, 0.0, 0.0),
            (10, 30, 0, 20.0, 0.0),
            (0, 30, 10, -20.0, 0.0),
            (0, 100, 0, 0.0, 0.0),
            (10, 250, 10, 2.0, 500.0),
            (0, 100, 0, 0.0, 500.0),
            (0, 30, 10, -20.0, 500.0),
            (0, 30, 10, 20.0, 500.0),
            (0, 150, 0, 0.0, 500.0),
            (30, 20, 20, 10.0, 1000.0),
            (0, 100, 0, 0.0, 1000.0),
            (30, 20, 20, 15.0, -1500.0),
            (0, 200, 0, 0.0, -6000),
            (0, 50, 0, 0.0, -6000),
            (0, 150, 0, 0.0, 0.0),
            (10, 30, 5, -15.0, 0.0),
            (5, 30, 5, 15.0, 0.0),
            (5, 30, 15, -15.0, 0.0),
            (0, 400, 0, 0.0, 0.0),
            (100, 150, 0, 7.0, 0.0),
            (0, 50, 80, 5.0, 0.0),
            (0, 150, 0, 0.0, 0.0),
        ]
    },
    {
        "id": "AUS",
        "name": "Red Bull Ring",
        "laps": 5,
        "background": "sprites/bg/L2.png",
        "bg_scale": 6,
        "sky_top": (0, 60, 150),
        "sky_bottom": (40, 180, 250),
        "colors": {
            "dark_grass": (0, 107, 0),
            "light_grass": (0, 123, 0),
            "dark_road": (95, 95, 95),
            "light_road": (107, 107, 107),
            "white_rumble": (255, 255, 255),
            "black_rumble": (255, 0, 0),
        },
        "sponsors": ['HEUER', 'LONGHI', 'MARELLI', 'MARLBORO', 'PIRELLI', 'SHELL'],
        "start_segment": 25,
        "layout": [
            (0, 200, 0, 0.0, 0.0),
            (10, 30, 5, 20.0, 2000.0),
            (0, 100, 0, -1.0, 4000.0),
            (0, 200, 0, 0.0, 6000.0),
            (0, 100, 0, -1.0, 8000.0),
            (0, 100, 0, 0.0, 10000.0),
            (5, 20, 10, 20.0, 11000.0),
            (0, 350, 0, 0.0, 11000.0),
            (20, 40, 30, 20.0, 8000.0),
            (20, 150, 20, 1.0, 8000.0),
            (10, 50, 20, 1.0, 8000.0),
            (20, 40, 20, -10.0, 8000.0),
            (0, 100, 0, 0.0, 6000.0),
            (20, 50, 40, -20.0, 5000.0),
            (20, 70, 20, 5.0, 5000.0),
            (0, 200, 0, 0.0, 5000.0),
            (50, 50, 20, 15.0, 4000.0),
            (0, 150, 0, 0.0, 2000.0),
            (20, 80, 20, 10.0, 1000.0),
            (0, 250, 0, 0.0, 0.0),
        ]
    }
]


def get_track(track_id: str) -> dict:
    for track in TRACKS:
        if track['id'] == track_id:
            return track
    raise ValueError(f"Pista '{track_id}' não encontrada!")


def get_all_tracks() -> list:
    return TRACKS
