from datetime import datetime
import os
import requests
import traceback

from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = "mongodb://mundial_user:M4nzana2026@ac-0tfmbvr-shard-00-00.tqvej0i.mongodb.net:27017,ac-0tfmbvr-shard-00-01.tqvej0i.mongodb.net:27017,ac-0tfmbvr-shard-00-02.tqvej0i.mongodb.net:27017/?ssl=true&replicaSet=atlas-fjc1fq-shard-0&authSource=admin&tlsAllowInvalidCertificates=true"

try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
    db = client['mundial_2026']
    coleccion = db['selecciones']
    
    print(f"✅ Conectado: {coleccion.count_documents({})} selecciones")
except Exception as e:
    print(f"❌ Error: {e}")
    coleccion = None

    # En app.py, agregar esta función:

def obtener_jugadores_clave_partido(seleccion):
    """Obtiene los mejores jugadores de una selección para recomendaciones"""
    jugadores = list(db.estadisticas_jugadores_bzzoiro.find(
        {"seleccion": seleccion, "participa_mundial": True},
        {'_id': 0, 'nombre': 1, 'goles_por_partido': 1, 'tiros_por_partido': 1, 
         'rating_promedio': 1, 'partidos': 1, 'goles': 1, 'tiros_totales': 1}
    ).sort('goles_por_partido', -1).limit(5))
    return jugadores

def generar_recomendaciones_partido(local, visitante):
    """Genera recomendaciones de apuesta para los jugadores clave del partido"""
    jugadores_local = obtener_jugadores_clave_partido(local)
    jugadores_visitante = obtener_jugadores_clave_partido(visitante)
    
    recomendaciones = []
    
    # Recomendaciones de jugadores del equipo local
    for j in jugadores_local:
        prob_gol = min(85, j.get('goles_por_partido', 0) * 45)
        if prob_gol > 25:
            recomendaciones.append({
                "tipo": "⚽ GOL",
                "jugador": j['nombre'],
                "equipo": local,
                "apuesta": f"{j['nombre']} anotará un gol",
                "probabilidad": round(prob_gol, 1),
                "cuota_sugerida": round(100 / prob_gol, 2),
                "estadistica": f"{j.get('goles', 0)} goles en {j.get('partidos', 0)} partidos"
            })
        
        prob_tiros = min(75, 30 + j.get('tiros_por_partido', 0) * 10)
        if prob_tiros > 40:
            recomendaciones.append({
                "tipo": "🎯 TIROS",
                "jugador": j['nombre'],
                "equipo": local,
                "apuesta": f"{j['nombre']} - Más de 1.5 tiros",
                "probabilidad": round(prob_tiros, 1),
                "cuota_sugerida": round(100 / prob_tiros, 2),
                "estadistica": f"{j.get('tiros_totales', 0)} tiros en {j.get('partidos', 0)} partidos"
            })
    
    # Recomendaciones de jugadores del equipo visitante
    for j in jugadores_visitante:
        prob_gol = min(85, j.get('goles_por_partido', 0) * 45)
        if prob_gol > 25:
            recomendaciones.append({
                "tipo": "⚽ GOL",
                "jugador": j['nombre'],
                "equipo": visitante,
                "apuesta": f"{j['nombre']} anotará un gol",
                "probabilidad": round(prob_gol, 1),
                "cuota_sugerida": round(100 / prob_gol, 2),
                "estadistica": f"{j.get('goles', 0)} goles en {j.get('partidos', 0)} partidos"
            })
        
        prob_tiros = min(75, 30 + j.get('tiros_por_partido', 0) * 10)
        if prob_tiros > 40:
            recomendaciones.append({
                "tipo": "🎯 TIROS",
                "jugador": j['nombre'],
                "equipo": visitante,
                "apuesta": f"{j['nombre']} - Más de 1.5 tiros",
                "probabilidad": round(prob_tiros, 1),
                "cuota_sugerida": round(100 / prob_tiros, 2),
                "estadistica": f"{j.get('tiros_totales', 0)} tiros en {j.get('partidos', 0)} partidos"
            })
    
    # Ordenar por probabilidad
    recomendaciones.sort(key=lambda x: x['probabilidad'], reverse=True)
    return recomendaciones[:10]  # Top 10
    
# ==================== CARGAR DATOS DESDE MONGODB ====================

def cargar_estadisticas_ligas():
    """Carga estadísticas de ligas desde MongoDB"""
    stats = {}
    try:
        datos = list(db.estadisticas_ligas.find({}, {'_id': 0}))
        for d in datos:
            stats[d['liga']] = {
                "goles": d.get('goles', 2.65),
                "corners": d.get('corners', 9.8),
                "tiros": d.get('tiros', 21.5),
                "tiros_puerta": d.get('tiros_puerta', 7.8),
                "amarillas": d.get('amarillas', 3.8)
            }
        print(f"✅ Estadísticas de {len(stats)} ligas cargadas desde MongoDB")
        return stats
    except Exception as e:
        print(f"⚠️ Error cargando estadísticas: {e}")
        return {}

def cargar_ranking_fifa():
    """Carga ranking FIFA desde MongoDB"""
    ranking = {}
    try:
        datos = list(db.ranking_fifa.find({}, {'_id': 0}))
        for d in datos:
            ranking[d['seleccion']] = d['ranking']
        print(f"✅ Ranking FIFA de {len(ranking)} selecciones cargado desde MongoDB")
        return ranking
    except Exception as e:
        print(f"⚠️ Error cargando ranking: {e}")
        return {}

# Cargar datos al iniciar la app
ESTADISTICAS_POR_LIGA = cargar_estadisticas_ligas()
RANKING_FIFA = cargar_ranking_fifa()




# ==================== ESTADÍSTICAS PROMEDIO POR LIGA ====================
# Datos basados en promedios reales de las principales ligas (temporada 2024-2025)
#ESTADISTICAS_POR_LIGA = {
 #   "Premier League": {"goles": 2.82, "corners": 10.5, "tiros": 23.2, "tiros_puerta": 8.4, "amarillas": 3.8},
  #  "La Liga": {"goles": 2.58, "corners": 9.8, "tiros": 21.5, "tiros_puerta": 7.8, "amarillas": 4.2},
   # "Serie A": {"goles": 2.68, "corners": 9.5, "tiros": 20.8, "tiros_puerta": 7.5, "amarillas": 4.0},
   # "Bundesliga": {"goles": 3.02, "corners": 10.8, "tiros": 24.5, "tiros_puerta": 8.8, "amarillas": 3.5},
   # "Ligue 1": {"goles": 2.52, "corners": 9.2, "tiros": 19.8, "tiros_puerta": 7.2, "amarillas": 3.9},
   # "MLS": {"goles": 2.95, "corners": 9.0, "tiros": 21.0, "tiros_puerta": 7.5, "amarillas": 3.2},
    #"default": {"goles": 2.65, "corners": 9.8, "tiros": 21.5, "tiros_puerta": 7.8, "amarillas": 3.8}
#}

# Ranking FIFA de selecciones
#RANKING_FIFA = {
 #   "Argentina": 1, "Francia": 2, "Brasil": 3, "Inglaterra": 4, "España": 5,
  #  "Países Bajos": 6, "Portugal": 7, "Alemania": 8, "Bélgica": 9, "Croacia": 10,
   # "Uruguay": 11, "Colombia": 12, "México": 13, "Estados Unidos": 14, "Marruecos": 15,
   # "Senegal": 16, "Japón": 17, "Corea del Sur": 18, "Australia": 19, "Suiza": 20,
   # "Dinamarca": 21, "Polonia": 22, "Canadá": 23, "Noruega": 24, "Egipto": 25,
#}


# ==================== JUGADORES MANUALES ====================
JUGADORES_MANUALES = {
    "messi": {"player": "Lionel Messi", "team": "Inter Miami", "league": "MLS", "goals": 12, "assists": 8, "rating": 8.2},
    "cristiano ronaldo": {"player": "Cristiano Ronaldo", "team": "Al Nassr", "league": "Saudi Pro League", "goals": 28, "assists": 6, "rating": 7.9}
}

# ==================== ELIMINATORIAS Y HISTORIAL ====================

# Enfrentamientos directos entre selecciones
HISTORIAL_ENFRENTAMIENTOS = {
    ("Argentina", "Brasil"): [
        {"fecha": "2025-11-21", "competicion": "Eliminatorias Sudamericanas", "resultado": "Argentina 2-1 Brasil"},
        {"fecha": "2024-07-10", "competicion": "Copa América", "resultado": "Argentina 1-0 Brasil"},
        {"fecha": "2023-11-16", "competicion": "Eliminatorias", "resultado": "Argentina 0-1 Brasil"},
        {"fecha": "2022-07-02", "competicion": "Copa América", "resultado": "Brasil 2-0 Argentina"},
    ],
    ("Argentina", "Uruguay"): [
        {"fecha": "2025-10-10", "competicion": "Eliminatorias", "resultado": "Argentina 3-0 Uruguay"},
        {"fecha": "2024-11-15", "competicion": "Eliminatorias", "resultado": "Uruguay 1-1 Argentina"},
        {"fecha": "2022-03-25", "competicion": "Eliminatorias", "resultado": "Argentina 1-0 Uruguay"},
    ],
    ("Argentina", "Francia"): [
        {"fecha": "2022-12-18", "competicion": "Mundial Final", "resultado": "Argentina 3-3 Francia (4-2 pen)"},
        {"fecha": "2018-06-30", "competicion": "Mundial", "resultado": "Francia 4-3 Argentina"},
    ],
    ("Argentina", "Alemania"): [
        {"fecha": "2014-07-13", "competicion": "Mundial Final", "resultado": "Alemania 1-0 Argentina"},
        {"fecha": "2010-07-03", "competicion": "Mundial", "resultado": "Alemania 4-0 Argentina"},
        {"fecha": "2006-06-30", "competicion": "Mundial", "resultado": "Alemania 1-1 Argentina (4-2 pen)"},
    ],
    ("Argentina", "Inglaterra"): [
        {"fecha": "2005-11-12", "competicion": "Amistoso", "resultado": "Argentina 2-3 Inglaterra"},
        {"fecha": "2002-06-07", "competicion": "Mundial", "resultado": "Argentina 0-1 Inglaterra"},
        {"fecha": "1998-06-30", "competicion": "Mundial", "resultado": "Argentina 2-2 Inglaterra (4-3 pen)"},
    ],
    ("Brasil", "Alemania"): [
        {"fecha": "2014-07-08", "competicion": "Mundial Semifinal", "resultado": "Brasil 1-7 Alemania"},
        {"fecha": "2002-06-30", "competicion": "Mundial Final", "resultado": "Brasil 2-0 Alemania"},
    ],
    ("Inglaterra", "Francia"): [
        {"fecha": "2022-12-10", "competicion": "Mundial", "resultado": "Francia 2-1 Inglaterra"},
        {"fecha": "2017-06-13", "competicion": "Amistoso", "resultado": "Francia 3-2 Inglaterra"},
    ],
    ("Inglaterra", "Alemania"): [
        {"fecha": "2021-06-29", "competicion": "Eurocopa", "resultado": "Inglaterra 2-0 Alemania"},
        {"fecha": "2010-06-27", "competicion": "Mundial", "resultado": "Alemania 4-1 Inglaterra"},
    ],
    ("España", "Portugal"): [
        {"fecha": "2018-06-15", "competicion": "Mundial", "resultado": "Portugal 3-3 España"},
        {"fecha": "2010-06-29", "competicion": "Mundial", "resultado": "España 1-0 Portugal"},
    ],
    ("España", "Alemania"): [
        {"fecha": "2010-07-07", "competicion": "Mundial", "resultado": "España 1-0 Alemania"},
        {"fecha": "2008-06-29", "competicion": "Eurocopa", "resultado": "España 1-0 Alemania"},
    ],
    ("Países Bajos", "España"): [
        {"fecha": "2010-07-11", "competicion": "Mundial Final", "resultado": "España 1-0 Países Bajos"},
        {"fecha": "2014-06-13", "competicion": "Mundial", "resultado": "Países Bajos 5-1 España"},
    ],
    ("Japón", "Alemania"): [
        {"fecha": "2022-11-23", "competicion": "Mundial", "resultado": "Japón 2-1 Alemania"},
    ],
    ("Corea del Sur", "Alemania"): [
        {"fecha": "2018-06-27", "competicion": "Mundial", "resultado": "Corea del Sur 2-0 Alemania"},
    ],
    ("Australia", "Argentina"): [
        {"fecha": "2022-12-03", "competicion": "Mundial", "resultado": "Argentina 2-1 Australia"},
    ],
    ("Estados Unidos", "Inglaterra"): [
        {"fecha": "2022-11-25", "competicion": "Mundial", "resultado": "Inglaterra 0-0 Estados Unidos"},
    ],
    ("México", "Alemania"): [
        {"fecha": "2018-06-17", "competicion": "Mundial", "resultado": "México 1-0 Alemania"},
    ],
}

# Eliminatorias por continente
ELIMINATORIAS = {
    "Sudamérica": {
        "clasificados": ["Argentina", "Ecuador", "Uruguay", "Colombia", "Brasil", "Paraguay"],
        "repechaje": ["Bolivia"],
        "eliminados": ["Venezuela", "Perú", "Chile"],
        "max_goleador": "Lionel Messi (8 goles)",
        "fecha_final": "2025-09-10",
        "posiciones": [
            {"pos": 1, "equipo": "Argentina", "pts": 38},
            {"pos": 2, "equipo": "Ecuador", "pts": 29},
            {"pos": 3, "equipo": "Colombia", "pts": 28},
            {"pos": 4, "equipo": "Uruguay", "pts": 28},
            {"pos": 5, "equipo": "Brasil", "pts": 28},
            {"pos": 6, "equipo": "Paraguay", "pts": 25},
        ]
    },
    "Europa": {
        "clasificados": ["España", "Francia", "Alemania", "Inglaterra", "Países Bajos", "Croacia", 
                        "Portugal", "Escocia", "Austria", "Bélgica", "Suiza", "Noruega"],
        "repechaje": ["Bosnia", "República Checa", "Suecia", "Turquía"],
        "fecha_final": "2026-03-31"
    },
    "África": {
        "clasificados": ["Sudáfrica", "Egipto", "Marruecos", "Argelia", "Costa de Marfil", "Ghana"],
        "fecha_final": "2025-10-14",
        "destacado": "Sudáfrica vuelve a un Mundial después de 16 años (2010)"
    },
    "Asia": {
        "clasificados": ["Corea del Sur", "Japón", "Irán", "Australia", "Arabia Saudita", "Uzbekistán", "Qatar", "Jordania"],
        "fecha_final": "2025-06-11",
        "destacado": "Corea del Sur clasificó invicta (20 goles a favor, 1 en contra)"
    },
    "Norteamérica": {
        "clasificados": ["México", "Canadá", "Estados Unidos", "Panamá"],
        "fecha_final": "2025-11-18",
        "destacado": "Canadá y México clasificaron como anfitriones"
    }
}

ODDS_API_KEY = "1928777e3a71509cabffaf3c507876ce"

# ==================== RESULTADOS DE ELIMINATORIAS ====================

PARTIDOS_ELIMINATORIAS = {
    "Sudamérica": [
        {"fecha": "2025-11-21", "local": "Argentina", "visitante": "Brasil", "goles_local": 2, "goles_visitante": 1, "goleadores_local": ["Messi (2)"], "goleadores_visitante": ["Vinicius"]},
        {"fecha": "2025-10-14", "local": "Brasil", "visitante": "Uruguay", "goles_local": 1, "goles_visitante": 1, "goleadores_local": ["Rodrygo"], "goleadores_visitante": ["Darwin Núñez"]},
        {"fecha": "2025-10-10", "local": "Argentina", "visitante": "Uruguay", "goles_local": 3, "goles_visitante": 0, "goleadores_local": ["Messi (2)", "Lautaro Martínez"], "goleadores_visitante": []},
        {"fecha": "2025-09-10", "local": "Colombia", "visitante": "Argentina", "goles_local": 1, "goles_visitante": 2, "goleadores_local": ["Luis Díaz"], "goleadores_visitante": ["Messi", "Lautaro Martínez"]},
        {"fecha": "2025-09-05", "local": "Ecuador", "visitante": "Brasil", "goles_local": 0, "goles_visitante": 1, "goleadores_local": [], "goleadores_visitante": ["Vinicius"]},
        {"fecha": "2025-03-25", "local": "Argentina", "visitante": "Chile", "goles_local": 4, "goles_visitante": 0, "goleadores_local": ["Messi", "Di María", "Lautaro", "Enzo Fernández"], "goleadores_visitante": []},
        {"fecha": "2025-03-20", "local": "Paraguay", "visitante": "Argentina", "goles_local": 1, "goles_visitante": 1, "goleadores_local": ["Sanabria"], "goleadores_visitante": ["Lautaro"]},
        {"fecha": "2024-11-15", "local": "Uruguay", "visitante": "Argentina", "goles_local": 1, "goles_visitante": 1, "goleadores_local": ["Darwin Núñez"], "goleadores_visitante": ["Messi"]},
    ],
    "Europa": [
        {"fecha": "2026-03-31", "local": "Bosnia", "visitante": "Italia", "goles_local": 1, "goles_visitante": 1, "penales": "4-1", "ganador": "Bosnia"},
        {"fecha": "2026-03-31", "local": "Suecia", "visitante": "Polonia", "goles_local": 3, "goles_visitante": 2, "ganador": "Suecia"},
        {"fecha": "2026-03-31", "local": "Kosovo", "visitante": "Turquía", "goles_local": 0, "goles_visitante": 1, "ganador": "Turquía"},
        {"fecha": "2026-03-31", "local": "Dinamarca", "visitante": "República Checa", "goles_local": 2, "goles_visitante": 2, "penales": "1-3", "ganador": "República Checa"},
    ],
    "África": [
        {"fecha": "2025-10-14", "local": "Sudáfrica", "visitante": "Nigeria", "goles_local": 2, "goles_visitante": 1, "goleadores_local": ["Mokwana", "Rayners"], "goleadores_visitante": ["Osimhen"]},
        {"fecha": "2025-10-14", "local": "Egipto", "visitante": "Etiopía", "goles_local": 2, "goles_visitante": 0, "goleadores_local": ["Salah", "Zizo"], "goleadores_visitante": []},
        {"fecha": "2025-10-14", "local": "Marruecos", "visitante": "Níger", "goles_local": 2, "goles_visitante": 1, "goleadores_local": ["Brahim Díaz", "El Khannous"], "goleadores_visitante": []},
        {"fecha": "2025-10-14", "local": "Argelia", "visitante": "Botsuana", "goles_local": 3, "goles_visitante": 2, "goleadores_local": ["Amoura (2)", "Belaïli"], "goleadores_visitante": []},
        {"fecha": "2025-10-14", "local": "Costa de Marfil", "visitante": "Burundi", "goles_local": 1, "goles_visitante": 0, "goleadores_local": ["Haller"], "goleadores_visitante": []},
        {"fecha": "2025-10-14", "local": "Ghana", "visitante": "Chad", "goles_local": 5, "goles_visitante": 0, "goleadores_local": ["Kudus (2)", "Williams", "Nuamah", "Samed"], "goleadores_visitante": []},
    ],
    "Asia": [
        {"fecha": "2025-06-11", "local": "Corea del Sur", "visitante": "China", "goles_local": 3, "goles_visitante": 0, "goleadores_local": ["Son Heung-min", "Kim Min-jae", "Hwang Hee-chan"]},
        {"fecha": "2025-06-11", "local": "Australia", "visitante": "China", "goles_local": 3, "goles_visitante": 1, "goleadores_local": ["Miller", "Goodwin", "Velupillay"], "goleadores_visitante": ["Wu Lei"]},
        {"fecha": "2025-06-11", "local": "Corea del Sur", "visitante": "Tailandia", "goles_local": 1, "goles_visitante": 1, "goleadores_local": ["Son Heung-min"], "goleadores_visitante": ["Suphanat"]},
        {"fecha": "2025-06-06", "local": "Japón", "visitante": "Siria", "goles_local": 5, "goles_visitante": 0, "goleadores_local": ["Kubo (2)", "Mitoma", "Kamada", "Ueda"]},
        {"fecha": "2025-06-06", "local": "Irán", "visitante": "Uzbekistán", "goles_local": 2, "goles_visitante": 2, "goleadores_local": ["Taremi", "Azmoun"], "goleadores_visitante": ["Shomurodov", "Fayzullaev"]},
    ],
    "Norteamérica": [
        {"fecha": "2025-11-18", "local": "Costa Rica", "visitante": "Honduras", "goles_local": 0, "goles_visitante": 0, "nota": "Ambos eliminados"},
        {"fecha": "2025-11-18", "local": "México", "visitante": "Canadá", "goles_local": 2, "goles_visitante": 1, "goleadores_local": ["Jiménez", "Lozano"], "goleadores_visitante": ["David"]},
        {"fecha": "2025-11-18", "local": "Estados Unidos", "visitante": "Panamá", "goles_local": 3, "goles_visitante": 0, "goleadores_local": ["Pulisic (2)", "Balogun"]},
    ],
}

def obtener_partidos_por_seleccion(seleccion):
    """Obtiene todos los partidos de una selección en las eliminatorias"""
    partidos = []
    for continente, partidos_continente in PARTIDOS_ELIMINATORIAS.items():
        for p in partidos_continente:
            if p['local'] == seleccion:
                partidos.append({
                    "fecha": p['fecha'],
                    "rival": p['visitante'],
                    "local": True,
                    "goles_favor": p['goles_local'],
                    "goles_contra": p['goles_visitante'],
                    "goleadores": p.get('goleadores_local', []),
                    "competicion": continente
                })
            elif p['visitante'] == seleccion:
                partidos.append({
                    "fecha": p['fecha'],
                    "rival": p['local'],
                    "local": False,
                    "goles_favor": p['goles_visitante'],
                    "goles_contra": p['goles_local'],
                    "goleadores": p.get('goleadores_visitante', []),
                    "competicion": continente
                })
    return sorted(partidos, key=lambda x: x['fecha'], reverse=True)

def obtener_todos_resultados(continente=None):
    """Obtiene todos los resultados por continente"""
    if continente:
        return PARTIDOS_ELIMINATORIAS.get(continente, [])
    return PARTIDOS_ELIMINATORIAS

# ==================== FUNCIONES ====================

def calcular_fuerza_equipo(nombre_equipo):
    """Calcula la fuerza del equipo usando ranking de MongoDB"""
    ranking = RANKING_FIFA.get(nombre_equipo, 25)
    # Fuerza entre 0.3 y 0.9 (mejor ranking = mayor fuerza)
    fuerza = max(0.3, min(0.9, (100 - ranking) / 100))
    return fuerza

def predecir_estadisticas_partido(equipo_local, equipo_visitante, liga="default"):
    """Predice estadísticas del partido basado en fuerza de equipos y promedios de liga"""
    
    stats_liga = ESTADISTICAS_POR_LIGA.get(liga, ESTADISTICAS_POR_LIGA["default"])
    
    # Fuerza de cada equipo
    fuerza_local = calcular_fuerza_equipo(equipo_local)
    fuerza_visitante = calcular_fuerza_equipo(equipo_visitante)
    
    # Factor de localía (+15% al local)
    factor_local = (fuerza_local * 1.15) / ((fuerza_local * 1.15) + fuerza_visitante)
    factor_visitante = 1 - factor_local
    
    # Calcular estadísticas esperadas
    goles_esperados_local = round(stats_liga["goles"] * factor_local, 1)
    goles_esperados_visitante = round(stats_liga["goles"] * factor_visitante, 1)
    goles_totales = round(goles_esperados_local + goles_esperados_visitante, 1)
    
    corners_local = round(stats_liga["corners"] * factor_local, 1)
    corners_visitante = round(stats_liga["corners"] * factor_visitante, 1)
    corners_totales = round(corners_local + corners_visitante, 1)
    
    tiros_local = round(stats_liga["tiros"] * factor_local, 1)
    tiros_visitante = round(stats_liga["tiros"] * factor_visitante, 1)
    tiros_totales = round(tiros_local + tiros_visitante, 1)
    
    tiros_puerta_local = round(stats_liga["tiros_puerta"] * factor_local, 1)
    tiros_puerta_visitante = round(stats_liga["tiros_puerta"] * factor_visitante, 1)
    
    return {
        "goles": {
            "local": goles_esperados_local,
            "visitante": goles_esperados_visitante,
            "total": goles_totales
        },
        "corners": {
            "local": corners_local,
            "visitante": corners_visitante,
            "total": corners_totales
        },
        "tiros": {
            "local": tiros_local,
            "visitante": tiros_visitante,
            "total": tiros_totales
        },
        "tiros_puerta": {
            "local": tiros_puerta_local,
            "visitante": tiros_puerta_visitante
        }
    }

def generar_recomendaciones(estadisticas):
    """Genera recomendaciones de apuesta basadas en estadísticas esperadas"""
    recomendaciones = []
    
    # Recomendación de goles
    if estadisticas["goles"]["total"] > 2.5:
        recomendaciones.append({
            "mercado": "⚽ GOLES",
            "apuesta": "Más de 2.5 goles",
            "probabilidad": min(85, 55 + (estadisticas["goles"]["total"] - 2.5) * 15),
            "estadistica": f"{estadisticas['goles']['total']} goles esperados"
        })
    else:
        recomendaciones.append({
            "mercado": "⚽ GOLES",
            "apuesta": "Menos de 2.5 goles",
            "probabilidad": min(85, 55 + (2.5 - estadisticas["goles"]["total"]) * 15),
            "estadistica": f"{estadisticas['goles']['total']} goles esperados"
        })
    
    # Recomendación de córners
    if estadisticas["corners"]["total"] > 9.5:
        recomendaciones.append({
            "mercado": "🔄 CÓRNERS",
            "apuesta": "Más de 9.5 córners",
            "probabilidad": min(80, 50 + (estadisticas["corners"]["total"] - 9.5) * 12),
            "estadistica": f"{estadisticas['corners']['total']} córners esperados"
        })
    else:
        recomendaciones.append({
            "mercado": "🔄 CÓRNERS",
            "apuesta": "Menos de 9.5 córners",
            "probabilidad": min(80, 50 + (9.5 - estadisticas["corners"]["total"]) * 12),
            "estadistica": f"{estadisticas['corners']['total']} córners esperados"
        })
    
    # Recomendación de tiros totales
    if estadisticas["tiros"]["total"] > 22:
        recomendaciones.append({
            "mercado": "🎯 TIROS",
            "apuesta": "Más de 22 tiros totales",
            "probabilidad": min(75, 50 + (estadisticas["tiros"]["total"] - 22) * 8),
            "estadistica": f"{estadisticas['tiros']['total']} tiros esperados"
        })
    
    return recomendaciones


# ==================== OPORTUNIDADES DE VALOR ====================

def calcular_valor_oportunidad(probabilidad_real, cuota):
    """Calcula el valor de una apuesta (retorno esperado)"""
    if cuota <= 0:
        return -100
    probabilidad_implicita = 1 / cuota
    valor = (probabilidad_real - probabilidad_implicita) / probabilidad_implicita * 100
    return round(valor, 1)

def obtener_probabilidad_real_local(equipo_local, equipo_visitante):
    """Calcula probabilidad real basada en ranking FIFA y localía"""
    
    # Ranking FIFA de selecciones (actualizado)
    rankings = {
        "Argentina": 1, "Francia": 2, "Brasil": 3, "Inglaterra": 4, "España": 5,
        "Países Bajos": 6, "Portugal": 7, "Alemania": 8, "Bélgica": 9, "Croacia": 10,
        "Uruguay": 11, "Colombia": 12, "México": 13, "Estados Unidos": 14, "Marruecos": 15,
        "Senegal": 16, "Japón": 17, "Corea del Sur": 18, "Australia": 19, "Suiza": 20,
        "Dinamarca": 21, "Polonia": 22, "Canadá": 23, "Noruega": 24, "Egipto": 25,
        "Ecuador": 26, "Paraguay": 27, "Costa de Marfil": 28, "Ghana": 29, "Nigeria": 30,
        "Argelia": 31, "Túnez": 32, "Camerún": 33, "Irán": 34, "Arabia Saudita": 35,
        "Uzbekistán": 36, "Qatar": 37, "Irak": 38, "Panamá": 39, "Costa Rica": 40,
        "Jamaica": 41, "Nueva Zelanda": 42, "República Democrática del Congo": 43,
        "Bolivia": 44, "Austria": 45, "Escocia": 46, "República Checa": 47
    }
    
    if equipo_local not in rankings or equipo_visitante not in rankings:
        return 0.33
    
    r_local = rankings[equipo_local]
    r_visitante = rankings[equipo_visitante]
    
    # Fuerza del equipo (inversamente proporcional al ranking)
    fuerza_local = (100 - r_local) / 100
    fuerza_visitante = (100 - r_visitante) / 100
    
    # Ventaja de localía (+15%)
    fuerza_local = fuerza_local * 1.15
    
    total_fuerza = fuerza_local + fuerza_visitante
    probabilidad_local = fuerza_local / total_fuerza
    
    return round(probabilidad_local, 3)

def obtener_oportunidades_valor_reales():
    """Analiza las cuotas reales y devuelve las mejores oportunidades"""
    
    # Obtener cuotas reales
    datos_cuotas = obtener_cuotas()
    
    if not datos_cuotas or not datos_cuotas.get('success'):
        return []
    
    oportunidades = []
    
    for partido in datos_cuotas.get('games', []):
        local = partido['home_team']
        visitante = partido['away_team']
        cuota_local = partido['cuotas']['home']
        
        # Solo analizar equipos que tenemos en nuestro ranking
        if local in ["Argentina", "Brasil", "Francia", "Inglaterra", "España", 
                     "Alemania", "Países Bajos", "Portugal", "Bélgica", "Croacia",
                     "Uruguay", "Colombia", "México", "Estados Unidos", "Marruecos",
                     "Senegal", "Japón", "Corea del Sur", "Australia", "Suiza",
                     "Dinamarca", "Polonia", "Canadá", "Noruega", "Egipto",
                     "Ecuador", "Paraguay", "Costa de Marfil", "Ghana", "Nigeria",
                     "Argelia", "Túnez", "Camerún", "Irán", "Arabia Saudita",
                     "Uzbekistán", "Qatar", "Irak", "Panamá", "Costa Rica",
                     "Jamaica", "Nueva Zelanda", "República Democrática del Congo",
                     "Bolivia", "Austria", "Escocia", "República Checa"]:
            
            prob_real = obtener_probabilidad_real_local(local, visitante)
            valor = calcular_valor_oportunidad(prob_real, cuota_local)
            
            if valor > 5:  # Solo mostrar si hay valor significativo
                if valor > 15:
                    nivel = "🔥 MUY RECOMENDADA"
                elif valor > 8:
                    nivel = "✅ RECOMENDADA"
                else:
                    nivel = "⚠️ VALOR MARGINAL"
                
                oportunidades.append({
                    "apuesta": f"{local} (Local) vs {visitante}",
                    "valor": valor,
                    "cuota": cuota_local,
                    "prob_real": round(prob_real * 100, 1),
                    "recomendacion": nivel,
                    "casa": partido['mejores_casas']['home']
                })
    
    # Ordenar por mayor valor
    oportunidades.sort(key=lambda x: x['valor'], reverse=True)
    return oportunidades[:6]  # Top 6 oportunidades



def obtener_selecciones():
    if coleccion is None: return []
    return list(coleccion.find({}, {'_id': 0}))

def obtener_historial(e1, e2):
    """Obtiene historial de enfrentamientos directos"""
    h = HISTORIAL_ENFRENTAMIENTOS.get((e1, e2)) or HISTORIAL_ENFRENTAMIENTOS.get((e2, e1))
    if not h:
        return None
    # Calcular goles totales
    goles1 = 0
    goles2 = 0
    for p in h:
        try:
            resultado = p['resultado']
            if e1 in resultado:
                partes = resultado.split()
                for i, part in enumerate(partes):
                    if '-' in part and 'pen' not in part:
                        g1, g2 = map(int, part.split('-'))
                        if e1 == partes[i-1] or (i > 0 and e1 in partes[i-1]):
                            goles1 += g1
                            goles2 += g2
                        else:
                            goles1 += g2
                            goles2 += g1
        except:
            pass
    return {"total": len(h), "partidos": h, "goles_local": goles1, "goles_visitante": goles2}

def obtener_cuotas():
    try:
        url = "https://api.the-odds-api.com/v4/sports/soccer/odds"
        params = {"apiKey": ODDS_API_KEY, "regions": "us,uk,eu", "markets": "h2h", "oddsFormat": "decimal"}
        r = requests.get(url, params=params, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def pronostico(local, visitante):
    d1 = next((s for s in obtener_selecciones() if s['nombre'] == local), None)
    d2 = next((s for s in obtener_selecciones() if s['nombre'] == visitante), None)
    if not d1 or not d2: return None
    rating1 = d1.get('rating_promedio', 6.5) * 10
    rating2 = d2.get('rating_promedio', 6.5) * 10
    goles1 = d1.get('goles_total', 0) / max(1, d1.get('jugadores', 1))
    goles2 = d2.get('goles_total', 0) / max(1, d2.get('jugadores', 1))
    fuerza1 = rating1 * 0.5 + goles1 * 30
    fuerza2 = rating2 * 0.5 + goles2 * 30
    total = fuerza1 + fuerza2
    prob1 = round((fuerza1 / total) * 70, 1)
    prob2 = round((fuerza2 / total) * 70, 1)
    probE = round(100 - prob1 - prob2, 1)
    if prob1 > 50: rec = f"💰 Apostar por {local} - Prob: {prob1}%"
    elif prob2 > 50: rec = f"💰 Apostar por {visitante} - Prob: {prob2}%"
    else: rec = f"🤝 Apostar al empate - Prob: {probE}%"
    return {'local': prob1, 'empate': probE, 'visitante': prob2, 'recomendacion': rec}

# ==================== HTML ====================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Mundial 2026</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; color: #4CAF50; margin-bottom: 10px; }
        h2 { margin: 25px 0 15px; color: #4CAF50; font-size: 1.4em; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #4CAF50; text-decoration: none; margin: 0 10px; padding: 8px 20px; background: #0f3460; border-radius: 25px; display: inline-block; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .card { background: #0f3460; padding: 15px; border-radius: 15px; text-align: center; }
        .card h3 { font-size: 2em; color: #4CAF50; }
        .charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .chart-box { background: #0f3460; padding: 15px; border-radius: 15px; }
        canvas { max-height: 250px; width: 100% !important; }
        select, button, input {
            padding: 10px 20px;
            border-radius: 25px;
            border: none;
            background: #0f3460;
            color: white;
            cursor: pointer;
        }
        button { background: #4CAF50; }
        .btn-blue { background: #2196F3; }
        .btn-orange { background: #FF9800; }
        .flex { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin: 15px 0; }
        table { width: 100%; background: #0f3460; border-radius: 15px; overflow: hidden; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #1a1a2e; }
        th { background: #4CAF50; }
        tr:hover { background: #1a2a4e; }
        .results { background: #0f3460; border-radius: 15px; padding: 20px; margin-top: 15px; display: none; }
        .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 15px 0; }
        .stat-card { background: #1a1a2e; padding: 15px; border-radius: 10px; text-align: center; }
        .big-number { font-size: 2em; font-weight: bold; color: #FFC107; }
        @media (max-width: 600px) { .grid-3 { grid-template-columns: 1fr; } .charts { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <a href="/">🏆 Ranking</a>
        <a href="/jugador">🔍 Jugadores</a>
        <a href="/eliminatorias">🌍 Eliminatorias</a>
        <a href="/resultados">📋 Resultados</a>
        <a href="/top_jugadores">⭐ Top Jugadores</a>
        <a href="/recomendaciones_jugadores">🎯 Recomendaciones</a>  <!-- NUEVO -->
    </div>
    
    <h1>🏆 Mundial 2026</h1>
    <p style="text-align:center">Análisis estadístico, cuotas y pronósticos</p>
    
    <div class="cards">
        <div class="card"><h3>{{ total_selecciones }}</h3><p>Selecciones</p></div>
        <div class="card"><h3>{{ total_jugadores }}</h3><p>Jugadores</p></div>
        <div class="card"><h3>📊</h3><p>Pronósticos</p></div>
        <div class="card"><h3>⚽</h3><p>Cuotas TR</p></div>
    </div>
    
    <div class="charts">
        <div class="chart-box"><h3>⭐ Rating Promedio</h3><canvas id="ratingChart"></canvas></div>
        <div class="chart-box"><h3>⚽ Goles Totales</h3><canvas id="golesChart"></canvas></div>
    </div>
    
    <!-- Pronóstico -->
    <h2>🔮 Pronóstico</h2>
    <div class="flex">
        <select id="eqLocal"><option value="">Local</option>{% for s in selecciones %}<option>{{ s.nombre }}</option>{% endfor %}</select>
        <span>VS</span>
        <select id="eqVisitante"><option value="">Visitante</option>{% for s in selecciones %}<option>{{ s.nombre }}</option>{% endfor %}</select>
        <button class="btn-orange" onclick="calcularPronostico()">🔮 Calcular</button>
    </div>
    <div id="pronosticoResultado" class="results"></div>
    <!-- Apuestas con valor -->
<h2>💰 OPORTUNIDADES DE VALOR</h2>
<div class="flex" style="margin-bottom: 10px;">
    <p style="color: #aaa; font-size: 0.9em;">📊 Basado en cuotas reales vs probabilidad estadística</p>
</div>
<div id="valorResultado" style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 30px;">
    <p>Cargando oportunidades de valor...</p>
</div>
    
    <!-- Cuotas -->
    <h2>📊 Cuotas Tiempo Real</h2>
    <button class="btn-blue" onclick="cargarCuotas()">🔄 Actualizar</button>
    <div id="cuotasResultado" style="margin-top:15px;"></div>

    <!-- Análisis Avanzado por Partido -->
<h2>🔍 ANÁLISIS AVANZADO POR PARTIDO</h2>
<p style="color: #aaa; margin-bottom: 10px;">Predicciones de goles, córners, tiros y recomendaciones de apuesta</p>

<div class="flex">
    <select id="analisisLocal">
        <option value="">Selecciona equipo local</option>
        {% for s in selecciones %}
        <option value="{{ s.nombre }}">{{ s.nombre }}</option>
        {% endfor %}
    </select>
    <span>VS</span>
    <select id="analisisVisitante">
        <option value="">Selecciona equipo visitante</option>
        {% for s in selecciones %}
        <option value="{{ s.nombre }}">{{ s.nombre }}</option>
        {% endfor %}
    </select>
    <button class="btn-orange" onclick="analizarPartido()">🔮 Analizar Partido</button>
</div>

<div id="analisisResultado" class="results" style="display: none;"></div>
    
    <!-- Historial -->
    <h2>📜 Historial de Enfrentamientos</h2>
    <div class="flex">
        <select id="histLocal"><option value="">Equipo</option>{% for s in selecciones %}<option>{{ s.nombre }}</option>{% endfor %}</select>
        <span>VS</span>
        <select id="histVisit"><option value="">Equipo</option>{% for s in selecciones %}<option>{{ s.nombre }}</option>{% endfor %}</select>
        <button class="btn-blue" onclick="cargarHistorial()">📜 Ver</button>
    </div>
    <div id="historialResultado" class="results"></div>
    
    <!-- Ranking -->
    <h2>📋 Ranking</h2>
    <table>
        <thead><tr><th>#</th><th>Selección</th><th>Jugadores</th><th>Goles</th><th>Rating</th></tr></thead>
        <tbody>{% for s in selecciones %}
        <tr><td>{{ loop.index }}</td><td><strong>{{ s.nombre }}</strong></td><td>{{ s.jugadores }}</td><td>{{ s.goles_total }}</td><td>{{ s.rating_promedio }}</td></tr>
        {% endfor %}</tbody>
    </table>
</div>

<script>
    let ratingChart, golesChart;
    
    function cargarGraficos() {
    console.log("Cargando gráficos desde datos del servidor...");
    
    // Tomar los datos directamente del HTML (como el ranking)
    const selecciones = {{ selecciones | tojson | safe }};
    
    console.log("Selecciones recibidas:", selecciones.length);
    
    // Top 10 Rating
    let topRating = [...selecciones].sort((a,b) => b.rating_promedio - a.rating_promedio).slice(0,10);
    const ratingCanvas = document.getElementById('ratingChart');
    if (ratingCanvas) {
        new Chart(ratingCanvas, {
            type: 'bar',
            data: {
                labels: topRating.map(t => t.nombre),
                datasets: [{
                    label: 'Rating Promedio',
                    data: topRating.map(t => t.rating_promedio),
                    backgroundColor: 'rgba(76,175,80,0.7)',
                    borderColor: '#4CAF50',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { labels: { color: 'white' } } },
                scales: { y: { ticks: { color: 'white' } }, x: { ticks: { color: 'white', rotation: 45 } } }
            }
        });
        console.log("Gráfico de rating creado");
    }
    
    // Top 10 Goles
    let topGoles = [...selecciones].sort((a,b) => b.goles_total - a.goles_total).slice(0,10);
    const golesCanvas = document.getElementById('golesChart');
    if (golesCanvas) {
        new Chart(golesCanvas, {
            type: 'bar',
            data: {
                labels: topGoles.map(t => t.nombre),
                datasets: [{
                    label: 'Goles Totales',
                    data: topGoles.map(t => t.goles_total),
                    backgroundColor: 'rgba(33,150,243,0.7)',
                    borderColor: '#2196F3',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { labels: { color: 'white' } } },
                scales: { y: { ticks: { color: 'white' } }, x: { ticks: { color: 'white', rotation: 45 } } }
            }
        });
        console.log("Gráfico de goles creado");
    }
}
    


function analizarPartido() {
    let local = document.getElementById('analisisLocal').value;
    let visitante = document.getElementById('analisisVisitante').value;
    
    if (!local || !visitante) {
        alert("Selecciona ambos equipos");
        return;
    }
    
    if (local === visitante) {
        alert("Los equipos deben ser diferentes");
        return;
    }
    
    let div = document.getElementById('analisisResultado');
    div.innerHTML = '<p style="text-align:center">📊 Analizando estadísticas y generando recomendaciones...</p>';
    div.style.display = 'block';
    
    fetch(`/api/analisis_partido/${encodeURIComponent(local)}/${encodeURIComponent(visitante)}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                div.innerHTML = `<p style="color: red;">❌ ${data.error}</p>`;
                return;
            }
            
            let html = `
                <div style="background: #0f3460; border-radius: 15px; padding: 20px;">
                    <h3 style="text-align: center; color: #4CAF50;">📊 ${data.local} vs ${data.visitante}</h3>
                    <p style="text-align: center; color: #aaa;">Análisis basado en ranking FIFA y estadísticas de liga</p>
                    
                    <h4>📈 ESTADÍSTICAS ESPERADAS</h4>
                    <div class="grid-3">
                        <div class="stat-card">
                            <div class="big-number">${data.estadisticas.goles.total}</div>
                            <p>⚽ GOLES TOTALES</p>
                            <small>${data.estadisticas.goles.local} - ${data.estadisticas.goles.visitante}</small>
                        </div>
                        <div class="stat-card">
                            <div class="big-number">${data.estadisticas.corners.total}</div>
                            <p>🔄 CÓRNERS TOTALES</p>
                            <small>${data.estadisticas.corners.local} - ${data.estadisticas.corners.visitante}</small>
                        </div>
                        <div class="stat-card">
                            <div class="big-number">${data.estadisticas.tiros.total}</div>
                            <p>🎯 TIROS TOTALES</p>
                            <small>${data.estadisticas.tiros.local} - ${data.estadisticas.tiros.visitante}</small>
                        </div>
                    </div>
                    
                    <h4>🎯 RECOMENDACIONES DE APUESTA</h4>
                    <div style="display: flex; flex-direction: column; gap: 15px;">
            `;
            
            for (let rec of data.recomendaciones) {
                let color = rec.probabilidad > 65 ? '#1a4a2e' : '#2a4a3e';
                html += `
                    <div style="background: ${color}; border-radius: 12px; padding: 15px; border-left: 4px solid #FFC107;">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                            <div>
                                <strong style="font-size: 1.2em;">${rec.mercado}</strong>
                                <p style="margin: 5px 0;">${rec.apuesta}</p>
                                <small>📊 ${rec.estadistica}</small>
                            </div>
                            <div style="text-align: center;">
                                <div class="big-number" style="font-size: 1.8em;">${rec.probabilidad}%</div>
                                <small>Probabilidad</small>
                            </div>
                            <div style="text-align: center;">
                                <div class="big-number" style="font-size: 1.8em;">${rec.cuota_sugerida}</div>
                                <small>Cuota sugerida</small>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            html += `
                    </div>
                    <p style="text-align: center; color: #aaa; margin-top: 20px; font-size: 12px;">
                        📅 Análisis generado: ${data.timestamp}<br>
                        ⚠️ Las apuestas tienen riesgo. Esta herramienta es solo para análisis estadístico.
                    </p>
                </div>
            `;
            
            div.innerHTML = html;
        })
        .catch(error => {
            console.error('Error:', error);
            div.innerHTML = '<p style="color: red;">❌ Error al analizar el partido. Intenta de nuevo.</p>';
        });
}

    function calcularPronostico() {
        let local = document.getElementById('eqLocal').value;
        let visitante = document.getElementById('eqVisitante').value;
        if (!local || !visitante) { alert("Selecciona dos equipos"); return; }
        if (local === visitante) { alert("Equipos diferentes"); return; }
        let div = document.getElementById('pronosticoResultado');
        div.innerHTML = '<p>Cargando...</p>';
        div.style.display = 'block';
        fetch('/api/pronostico?local='+encodeURIComponent(local)+'&visitante='+encodeURIComponent(visitante))
            .then(r=>r.json())
            .then(data=>{
                div.innerHTML = `<div class="grid-3">
                    <div class="stat-card"><div class="big-number">${data.local}%</div><div>🏠 ${local}</div></div>
                    <div class="stat-card"><div class="big-number">${data.empate}%</div><div>🤝 Empate</div></div>
                    <div class="stat-card"><div class="big-number">${data.visitante}%</div><div>✈️ ${visitante}</div></div>
                </div><div style="background:#1a1a2e;padding:15px;border-radius:10px;text-align:center">${data.recomendacion}</div>`;
            });
    }
    
    function cargarCuotas() {
        let div = document.getElementById('cuotasResultado');
        div.innerHTML = '<p>Cargando...</p>';
        fetch('/api/odds').then(r=>r.json()).then(data=>{
            if (!data.success || data.games.length===0) { div.innerHTML = '<p>No hay partidos</p>'; return; }
            let html = '';
            for (let g of data.games.slice(0,8)) {
                html += `<div style="background:#0f3460;margin-bottom:10px;padding:15px;border-radius:10px;">
                    <strong>${g.home_team} 🆚 ${g.away_team}</strong>
                    <div class="grid-3" style="margin-top:10px">
                        <div class="stat-card">🏠 Local<br><span class="big-number">${g.cuotas.home>0?g.cuotas.home.toFixed(2):'N/A'}</span><br><small>${g.mejores_casas.home}</small></div>
                        <div class="stat-card">🤝 Empate<br><span class="big-number">${g.cuotas.draw>0?g.cuotas.draw.toFixed(2):'N/A'}</span><br><small>${g.mejores_casas.draw}</small></div>
                        <div class="stat-card">✈️ Visitante<br><span class="big-number">${g.cuotas.away>0?g.cuotas.away.toFixed(2):'N/A'}</span><br><small>${g.mejores_casas.away}</small></div>
                    </div>
                </div>`;
            }
            div.innerHTML = html;
        }).catch(e=>div.innerHTML='<p>Error</p>');
    }
    
function cargarOportunidadesValor() {
    fetch('/api/valor_oportunidades')
        .then(r => r.json())
        .then(data => {
            let container = document.getElementById('valorResultado');
            if (data.length === 0) {
                container.innerHTML = '<p>No hay oportunidades de valor significativas en este momento</p>';
                return;
            }
            
            let html = '';
            for (let opp of data) {
                let color = opp.valor > 15 ? '#1a4a2e' : (opp.valor > 8 ? '#2a4a3e' : '#3a4a4e');
                html += `
                    <div style="background: ${color}; border-radius: 15px; padding: 15px; flex: 1; min-width: 200px; border-left: 4px solid #FFC107;">
                        <h3 style="color: #FFC107; margin-bottom: 10px;">🎯 ${opp.apuesta}</h3>
                        <p style="font-size: 2em; font-weight: bold; color: #4CAF50; margin: 10px 0;">
                            +${opp.valor}% <span style="font-size: 0.5em; color: #aaa;">valor</span>
                        </p>
                        <p>📊 Cuota: <strong>${opp.cuota}</strong> (${opp.casa})</p>
                        <p>📈 Probabilidad real: ${opp.prob_real}%</p>
                        <p style="margin-top: 10px; color: #FFC107;">${opp.recomendacion}</p>
                    </div>
                `;
            }
            container.innerHTML = html;
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('valorResultado').innerHTML = '<p>Error cargando oportunidades de valor</p>';
        });
}


    function cargarHistorial() {
        let local = document.getElementById('histLocal').value;
        let visitante = document.getElementById('histVisit').value;
        if (!local || !visitante) { alert("Selecciona dos equipos"); return; }
        let div = document.getElementById('historialResultado');
        div.innerHTML = '<p>Cargando historial...</p>';
        div.style.display = 'block';
        fetch('/api/historial?eq1='+encodeURIComponent(local)+'&eq2='+encodeURIComponent(visitante))
            .then(r=>r.json())
            .then(data=>{
                if (data.error) { div.innerHTML = '<p>'+data.error+'</p>'; return; }
                let html = `<div style="background:#0f3460;border-radius:15px;padding:20px">
                    <h3>📊 ${local} vs ${visitante}</h3>
                    <div class="grid-3">
                        <div class="stat-card">🏆 Total<br><span class="big-number">${data.total}</span><br>partidos</div>
                        <div class="stat-card">⚽ Goles ${local}<br><span class="big-number">${data.goles_local}</span></div>
                        <div class="stat-card">⚽ Goles ${visitante}<br><span class="big-number">${data.goles_visitante}</span></div>
                    </div>
                    <h4>📋 Partidos</h4><table style="width:100%"><thead><tr><th>Fecha</th><th>Competición</th><th>Resultado</th></tr></thead><tbody>`;
                for (let p of data.partidos) {
                    html += `<tr><td>${p.fecha}</td><td>${p.competicion}</td><td>${p.resultado}</td></tr>`;
                }
                html += `</tbody></table></div>`;
                div.innerHTML = html;
            });
    }
    
    cargarGraficos();
    setTimeout(cargarCuotas, 500);
    cargarOportunidadesValor();
</script>
</body>
</html>
"""

# ==================== PÁGINA ELIMINATORIAS ====================
HTML_ELIMINATORIAS = """
<!DOCTYPE html>
<html>
<head>
    <title>Eliminatorias - Mundial 2026</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Segoe UI',Arial,sans-serif;background:#1a1a2e;color:white;padding:20px;}
        .container{max-width:1000px;margin:0 auto;}
        h1{text-align:center;color:#4CAF50;margin-bottom:20px;}
        h2{margin:20px 0 10px;color:#FFC107;}
        .nav{text-align:center;margin-bottom:20px;}
        .nav a{color:#4CAF50;text-decoration:none;margin:0 10px;padding:8px 20px;background:#0f3460;border-radius:25px;}
        .continente{background:#0f3460;border-radius:15px;padding:20px;margin-bottom:20px;}
        .continente h3{color:#4CAF50;margin-bottom:15px;}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:10px 0;}
        .badge{background:#1a1a2e;padding:8px;border-radius:10px;text-align:center;}
        .badge.green{background:#1a3a2e;border-left:3px solid #4CAF50;}
        table{width:100%;background:#1a1a2e;border-radius:10px;border-collapse:collapse;}
        th,td{padding:8px;text-align:left;}
        th{color:#4CAF50;}
    </style>
</head>
<body>
<div class="container">
    <div class="nav"><a href="/">🏆 Ranking</a><a href="/jugador">🔍 Jugadores</a><a href="/eliminatorias">🌍 Eliminatorias</a><a href="/resultados">📋 Resultados</a><a href="/recomendaciones_jugadores">🎯 Recomendaciones</a><a href="/recomendaciones_jugadores">🎯 Recomendaciones</a>  <!-- NUEVO --></div>
    <h1>🌍 Eliminatorias por Continente</h1>
    
    <div class="continente">
        <h3>🏆 Sudamérica (CONMEBOL)</h3>
        <div class="grid">
            <div class="badge green">✅ Clasificados: Argentina, Ecuador, Uruguay, Colombia, Brasil, Paraguay</div>
            <div class="badge">🔄 Repechaje: Bolivia</div>
            <div class="badge">❌ Eliminados: Venezuela, Perú, Chile</div>
        </div>
        <p><strong>⭐ Máximo goleador:</strong> Lionel Messi (8 goles)</p>
        <p><strong>📅 Fecha final:</strong> 10 de septiembre de 2025</p>
        <h4>Tabla de posiciones:</h4>
        <table><th>Pos</th><th>Equipo</th><th>Pts</th></tr>
        <tr><td style="text-align:center">1</td><td>Argentina</td><td>38</td></tr>
        <tr><td style="text-align:center">2</td><td>Ecuador</td><td>29</td></tr>
        <tr><td style="text-align:center">3</td><td>Colombia</td><td>28</td></tr>
        <tr><td style="text-align:center">4</td><td>Uruguay</td><td>28</td></tr>
        <tr><td style="text-align:center">5</td><td>Brasil</td><td>28</td></tr>
        <tr><td style="text-align:center">6</td><td>Paraguay</td><td>25</td></tr>
        </table>
    </div>
    
    <div class="continente">
        <h3>⚽ Europa (UEFA)</h3>
        <div class="grid">
            <div class="badge green">✅ Clasificados directos: España, Francia, Alemania, Inglaterra, Países Bajos, Croacia, Portugal, Escocia, Austria, Bélgica, Suiza, Noruega</div>
            <div class="badge">🔄 Repechaje: Bosnia, República Checa, Suecia, Turquía</div>
        </div>
        <p><strong>📅 Fecha final:</strong> 31 de marzo de 2026</p>
    </div>
    
    <div class="continente">
        <h3>🦁 África (CAF)</h3>
        <div class="grid">
            <div class="badge green">✅ Clasificados: Sudáfrica, Egipto, Marruecos, Argelia, Costa de Marfil, Ghana</div>
        </div>
        <p><strong>📅 Fecha final:</strong> 14 de octubre de 2025</p>
        <p><strong>🎉 Destacado:</strong> Sudáfrica vuelve a un Mundial después de 16 años</p>
    </div>
    
    <div class="continente">
        <h3>🐉 Asia (AFC)</h3>
        <div class="grid">
            <div class="badge green">✅ Clasificados: Corea del Sur, Japón, Irán, Australia, Arabia Saudita, Uzbekistán, Qatar, Jordania</div>
        </div>
        <p><strong>🎉 Destacado:</strong> Corea del Sur clasificó invicta (20 goles a favor, 1 en contra)</p>
    </div>
    
    <div class="continente">
        <h3>🌎 Norteamérica (CONCACAF)</h3>
        <div class="grid">
            <div class="badge green">✅ Clasificados: México, Canadá, Estados Unidos, Panamá</div>
        </div>
        <p><strong>📅 Fecha final:</strong> 18 de noviembre de 2025</p>
        <p><strong>🎉 Destacado:</strong> Canadá y México clasificaron como anfitriones</p>
    </div>
</div>
</body>
</html>
"""

# ==================== PÁGINA JUGADORES ====================
HTML_JUGADOR = """
<!DOCTYPE html>
<html>
<head><title>Buscador de Jugadores</title><meta charset="UTF-8">
<style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:'Segoe UI',Arial,sans-serif;background:#1a1a2e;color:white;padding:20px;}
    .container{max-width:600px;margin:0 auto;}
    h1{text-align:center;color:#4CAF50;margin-bottom:20px;}
    .nav{text-align:center;margin-bottom:20px;}
    .nav a{color:#4CAF50;text-decoration:none;margin:0 10px;padding:8px 20px;background:#0f3460;border-radius:25px;}
    input,button{padding:10px 20px;border-radius:25px;border:none;}
    input{background:#0f3460;color:white;flex:1;}
    button{background:#4CAF50;color:white;cursor:pointer;}
    .flex{display:flex;gap:10px;margin:20px 0;}
    .results{background:#0f3460;border-radius:15px;padding:20px;margin-top:20px;display:none;}
    .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:15px 0;}
    .card{background:#1a1a2e;padding:15px;border-radius:10px;text-align:center;}
    .card h3{font-size:2em;color:#4CAF50;}
</style>
</head>
<body>
<div class="container">
    <div class="nav"><a href="/">🏆 Ranking</a><a href="/jugador">🔍 Jugadores</a><a href="/eliminatorias">🌍 Eliminatorias</a><a href="/resultados">📋 Resultados</a><a href="/recomendaciones_jugadores">🎯 Recomendaciones</a>  <!-- NUEVO --></div>
    <h1>🔍 Buscador de Jugadores</h1>
    <div class="flex"><input type="text" id="searchInput" placeholder="Ej: Messi, Ronaldo..."><button onclick="buscar()">Buscar</button></div>
    <div id="resultado" class="results"></div>
</div>
<script>
    function buscar() {
        let nombre = document.getElementById('searchInput').value;
        if (nombre.length<2){alert("Mínimo 2 caracteres");return;}
        fetch('/api/jugador/buscar?nombre='+encodeURIComponent(nombre)).then(r=>r.json()).then(data=>{
            let div=document.getElementById('resultado');
            if(data.error){div.innerHTML='<p>❌ '+data.error+'</p>';}
            else{
                let html='<h3>'+data.player+'</h3><div class="grid"><div class="card"><h3>'+data.goals+'</h3><p>Goles</p></div>';
                html+='<div class="card"><h3>'+data.assists+'</h3><p>Asistencias</p></div>';
                html+='<div class="card"><h3>'+data.rating+'</h3><p>Rating</p></div></div>';
                html+='<p><strong>Equipo:</strong> '+data.team+' ('+data.league+')</p>';
                div.innerHTML=html;
            }
            div.style.display='block';
        });
    }
</script>
</body>
</html>
"""

HTML_RESULTADOS = """
<!DOCTYPE html>
<html>
<head>
    <title>Resultados de Eliminatorias</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Segoe UI',Arial,sans-serif;background:#1a1a2e;color:white;padding:20px;}
        .container{max-width:1000px;margin:0 auto;}
        h1{text-align:center;color:#4CAF50;margin-bottom:20px;}
        .nav{text-align:center;margin-bottom:20px;}
        .nav a{color:#4CAF50;text-decoration:none;margin:0 10px;padding:8px 20px;background:#0f3460;border-radius:25px;}
        select, button{padding:10px 20px;border-radius:25px;border:none;background:#0f3460;color:white;cursor:pointer;}
        button{background:#4CAF50;}
        .flex{display:flex;gap:10px;justify-content:center;margin:20px 0;flex-wrap:wrap;}
        .partidos{background:#0f3460;border-radius:15px;padding:20px;margin-top:20px;}
        .partido{border-bottom:1px solid #2a2a4e;padding:15px;margin-bottom:10px;}
        .partido:last-child{border-bottom:none;}
        .fecha{color:#aaa;font-size:12px;}
        .resultado{font-size:1.5em;font-weight:bold;margin:10px 0;}
        .resultado.ganador{color:#4CAF50;}
        .resultado.perdedor{color:#f44336;}
        .resultado.empate{color:#FFC107;}
        .goleadores{color:#aaa;font-size:12px;margin-top:5px;}
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <a href="/">🏆 Ranking</a>
        <a href="/jugador">🔍 Jugadores</a>
        <a href="/eliminatorias">🌍 Eliminatorias</a>
        <a href="/resultados">📋 Resultados</a>
        <a href="/top_jugadores">⭐ Top Jugadores</a>
        <a href="/recomendaciones_jugadores">🎯 Recomendaciones</a>  <!-- NUEVO -->
    </div>
    <h1>📋 Resultados de Eliminatorias</h1>
    
    <div class="flex">
        <select id="seleccion">
            <option value="">Selecciona una selección</option>
            {% for s in selecciones %}
            <option value="{{ s.nombre }}">{{ s.nombre }}</option>
            {% endfor %}
        </select>
        <button onclick="cargarPartidos()">Ver Partidos</button>
    </div>
    
    <div id="resultados" class="partidos" style="display:none;"></div>
</div>

<script>
    function cargarPartidos() {
        let seleccion = document.getElementById('seleccion').value;
        if (!seleccion) { alert("Selecciona una selección"); return; }
        
        let div = document.getElementById('resultados');
        div.innerHTML = '<p>Cargando partidos...</p>';
        div.style.display = 'block';
        
        fetch('/api/partidos/' + encodeURIComponent(seleccion))
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    div.innerHTML = '<p>❌ ' + data.error + '</p>';
                    return;
                }
                
                let html = `<h2>📊 ${seleccion}</h2>`;
                let ganados = 0, empatados = 0, perdidos = 0, gf = 0, gc = 0;
                
                for (let p of data) {
                    gf += p.goles_favor;
                    gc += p.goles_contra;
                    if (p.goles_favor > p.goles_contra) ganados++;
                    else if (p.goles_favor < p.goles_contra) perdidos++;
                    else empatados++;
                    
                    let clase = '';
                    if (p.goles_favor > p.goles_contra) clase = 'ganador';
                    else if (p.goles_favor < p.goles_contra) clase = 'perdedor';
                    else clase = 'empate';
                    
                    let localStr = p.local ? '🏠 ' + seleccion : seleccion;
                    let visitanteStr = p.local ? p.rival : '✈️ ' + p.rival;
                    
                    html += `<div class="partido">
                        <div class="fecha">📅 ${p.fecha} | ${p.competicion}</div>
                        <div class="resultado ${clase}">${localStr} ${p.goles_favor} - ${p.goles_contra} ${visitanteStr}</div>`;
                    
                    if (p.goleadores && p.goleadores.length > 0) {
                        html += `<div class="goleadores">⚽ Goleadores: ${p.goleadores.join(', ')}</div>`;
                    }
                    html += `</div>`;
                }
                
                html += `<div style="margin-top:20px;background:#1a1a2e;padding:15px;border-radius:10px;">
                    <h3>📊 Resumen</h3>
                    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;text-align:center;margin-top:10px;">
                        <div><span class="big-number">${ganados}</span><br>🏆 Victorias</div>
                        <div><span class="big-number">${empatados}</span><br>🤝 Empates</div>
                        <div><span class="big-number">${perdidos}</span><br>❌ Derrotas</div>
                        <div><span class="big-number">${gf}</span><br>⚽ Goles a favor</div>
                        <div><span class="big-number">${gc}</span><br>🛡️ Goles en contra</div>
                    </div>
                </div>`;
                
                div.innerHTML = html;
            });
    }
</script>
</body>
</html>
"""
# ==================== PÁGINA ESTADÍSTICAS JUGADOR ====================
HTML_ESTADISTICAS_JUGADOR = """
<!DOCTYPE html>
<html>
<head>
    <title>Estadísticas de {{ jugador.nombre }}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 20px;
        }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { text-align: center; color: #4CAF50; margin-bottom: 10px; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #4CAF50; text-decoration: none; margin: 0 10px; padding: 8px 20px; background: #0f3460; border-radius: 25px; display: inline-block; }
        .card { background: #0f3460; border-radius: 15px; padding: 20px; margin-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: #1a1a2e; padding: 15px; border-radius: 10px; text-align: center; }
        .stat-number { font-size: 2.5em; font-weight: bold; color: #FFC107; }
        .stat-label { color: #aaa; margin-top: 5px; }
        .charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
        .chart-box { background: #1a1a2e; padding: 15px; border-radius: 10px; }
        canvas { max-height: 300px; width: 100% !important; }
        .btn-back { display: inline-block; background: #4CAF50; color: white; padding: 10px 20px; border-radius: 25px; text-decoration: none; margin-top: 10px; }
        .badge { background: #4CAF50; padding: 5px 10px; border-radius: 20px; font-size: 0.8em; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; text-align: center; border-bottom: 1px solid #2a2a4e; }
        th { background: #4CAF50; }
        tr:hover { background: #1a2a4e; }
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <a href="/">🏆 Ranking</a>
        <a href="/jugador">🔍 Buscador</a>
        <a href="/eliminatorias">🌍 Eliminatorias</a>
        <a href="/resultados">📋 Resultados</a>
        <a href="/top_jugadores">⭐ Top Jugadores</a>
        <a href="/recomendaciones_jugadores">🎯 Recomendaciones</a>  <!-- NUEVO -->
    </div>
    
    <div class="card">
        <h1>⚽ {{ jugador.nombre }}</h1>
        <p style="text-align:center">
            <span class="badge">{{ jugador.seleccion }}</span>
            <span class="badge" style="background:#2196F3">{{ jugador.equipo }}</span>
            <span class="badge" style="background:#FF9800">{{ jugador.liga }}</span>
        </p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card"><div class="stat-number">{{ jugador.partidos }}</div><div class="stat-label">Partidos</div></div>
        <div class="stat-card"><div class="stat-number">{{ jugador.minutos }}</div><div class="stat-label">Minutos</div></div>
        <div class="stat-card"><div class="stat-number">{{ jugador.goles }}</div><div class="stat-label">Goles</div></div>
        <div class="stat-card"><div class="stat-number">{{ jugador.asistencias }}</div><div class="stat-label">Asistencias</div></div>
        <div class="stat-card"><div class="stat-number">{{ jugador.rating }}</div><div class="stat-label">Rating</div></div>
    </div>
    
    <div class="charts-grid">
        <div class="chart-box">
            <h3 style="text-align:center">🎯 Tiros</h3>
            <canvas id="tirosChart"></canvas>
        </div>
        <div class="chart-box">
            <h3 style="text-align:center">📊 Rendimiento</h3>
            <canvas id="rendimientoChart"></canvas>
        </div>
    </div>
    
    <div class="card">
        <h3>📋 Estadísticas completas</h3>
        <table>
            <tr><th>Métrica</th><th>Valor</th><th>Promedio por partido</th></tr>
            <tr><td>Tiros totales</td><td>{{ jugador.tiros_totales|default(0) }}</td><td>{{ (jugador.tiros_totales|default(0) / jugador.partidos)|round(1) }}</td></tr>
            <tr><td>Tiros a puerta</td><td>{{ jugador.tiros_puerta|default(0) }}</td><td>{{ (jugador.tiros_puerta|default(0) / jugador.partidos)|round(1) }}</td></tr>
            <tr><td>Pases clave</td><td>{{ jugador.pases_clave|default(0) }}</td><td>{{ (jugador.pases_clave|default(0) / jugador.partidos)|round(1) }}</td></tr>
            <tr><td>Regates</td><td>{{ jugador.regates|default(0) }}</td><td>{{ (jugador.regates|default(0) / jugador.partidos)|round(1) }}</td></tr>
            <tr><td>Entradas</td><td>{{ jugador.entradas|default(0) }}</td><td>{{ (jugador.entradas|default(0) / jugador.partidos)|round(1) }}</td></tr>
            <tr><td>Intercepciones</td><td>{{ jugador.intercepciones|default(0) }}</td><td>{{ (jugador.intercepciones|default(0) / jugador.partidos)|round(1) }}</td></tr>
        </table>
    </div>
    
    <div style="text-align:center">
        <a href="/top_jugadores" class="btn-back">← Ver todos los jugadores</a>
        <a href="/" class="btn-back" style="background:#666">← Inicio</a>
    </div>
</div>

<script>
    const ctx1 = document.getElementById('tirosChart').getContext('2d');
    new Chart(ctx1, {
        type: 'bar',
        data: {
            labels: ['Tiros totales', 'Tiros a puerta', 'Goles'],
            datasets: [{
                label: 'Cantidad',
                data: [{{ jugador.tiros_totales|default(0) }}, {{ jugador.tiros_puerta|default(0) }}, {{ jugador.goles }}],
                backgroundColor: ['#2196F3', '#4CAF50', '#FFC107'],
                borderRadius: 10
            }]
        },
        options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: 'white' } } }, scales: { y: { ticks: { color: 'white' } }, x: { ticks: { color: 'white' } } } }
    });
    
    const ctx2 = document.getElementById('rendimientoChart').getContext('2d');
    new Chart(ctx2, {
        type: 'radar',
        data: {
            labels: ['Goles', 'Asistencias', 'Pases clave', 'Regates', 'Entradas', 'Intercepciones'],
            datasets: [{
                label: '{{ jugador.nombre }}',
                data: [{{ jugador.goles }}, {{ jugador.asistencias }}, {{ jugador.pases_clave|default(0) }}, {{ jugador.regates|default(0) }}, {{ jugador.entradas|default(0) }}, {{ jugador.intercepciones|default(0) }}],
                backgroundColor: 'rgba(76, 175, 80, 0.2)',
                borderColor: '#4CAF50',
                borderWidth: 2,
                pointBackgroundColor: '#4CAF50'
            }]
        },
        options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: 'white' } } }, scales: { r: { ticks: { color: 'white', backdropColor: 'transparent' }, grid: { color: 'rgba(255,255,255,0.2)' } } } }
    });
</script>
</body>
</html>
"""

# ==================== NUEVO HTML PARA RECOMENDACIONES DE JUGADORES ====================

HTML_RECOMENDACIONES_JUGADOR = """
<!DOCTYPE html>
<html>
<head>
    <title>Recomendaciones por Jugador - Mundial 2026</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; color: #4CAF50; margin-bottom: 10px; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #4CAF50; text-decoration: none; margin: 0 10px; padding: 8px 20px; background: #0f3460; border-radius: 25px; display: inline-block; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }
        .card { background: #0f3460; border-radius: 15px; padding: 20px; transition: transform 0.2s; }
        .card:hover { transform: scale(1.02); }
        .nombre { font-size: 1.5em; color: #FFC107; margin-bottom: 5px; }
        .goles { font-size: 2em; color: #4CAF50; }
        .btn { background: #2196F3; color: white; padding: 8px 16px; border-radius: 20px; text-decoration: none; display: inline-block; margin-top: 10px; border: none; cursor: pointer; }
        select, button { padding: 10px 20px; border-radius: 25px; border: none; background: #0f3460; color: white; cursor: pointer; }
        button { background: #4CAF50; }
        .flex { display: flex; gap: 10px; justify-content: center; margin: 20px 0; flex-wrap: wrap; }
        .results { background: #0f3460; border-radius: 15px; padding: 20px; margin-top: 20px; display: none; }
        .small-card { background: #1a1a2e; border-radius: 10px; padding: 15px; margin-top: 10px; }
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <a href="/">🏆 Ranking</a>
        <a href="/jugador">🔍 Jugadores</a>
        <a href="/eliminatorias">🌍 Eliminatorias</a>
        <a href="/resultados">📋 Resultados</a>
        <a href="/top_jugadores">⭐ Top Jugadores</a>
        <a href="/recomendaciones_jugadores">🎯 Recomendaciones</a>
    </div>
    
    <h1>🎯 Recomendaciones de Apuesta por Jugador</h1>
    <p style="text-align:center">Basado en estadísticas reales de los últimos partidos</p>
    
    <div class="flex">
        <select id="jugadorSelect">
            <option value="">Selecciona un jugador</option>
        </select>
        <button onclick="cargarRecomendaciones()">🔮 Obtener Recomendaciones</button>
    </div>
    
    <div id="resultado" class="results"></div>
    
    <h2>🏆 Top Goleadores</h2>
    <div id="topJugadores" class="grid"></div>
</div>

<script>
    // Cargar top jugadores
    fetch('/api/top_jugadores_estadisticas')
        .then(r => r.json())
        .then(data => {
            let html = '';
            for (let j of data.slice(0, 8)) {
                html += `
                    <div class="card">
                        <div class="nombre">⭐ ${j.nombre}</div>
                        <div class="goles">${j.goles} goles</div>
                        <div>${j.goles_por_partido ? j.goles_por_partido.toFixed(2) : '0'} por partido</div>
                        <div>🎯 ${j.tiros_por_partido || 0} tiros/partido</div>
                        <div>📊 Rating: ${j.rating_promedio || 0}</div>
                        <button onclick="seleccionarJugador('${j.nombre.replace(/'/g, "\\'")}')" class="btn">Ver recomendaciones</button>
                    </div>
                `;
            }
            document.getElementById('topJugadores').innerHTML = html;
            
            // Llenar select
            let select = document.getElementById('jugadorSelect');
            for (let j of data) {
                let option = document.createElement('option');
                option.value = j.nombre;
                option.textContent = j.nombre;
                select.appendChild(option);
            }
        })
        .catch(error => console.error('Error:', error));
    
    function seleccionarJugador(nombre) {
        document.getElementById('jugadorSelect').value = nombre;
        cargarRecomendaciones();
    }
    
    function cargarRecomendaciones() {
        let nombre = document.getElementById('jugadorSelect').value;
        if (!nombre) { alert("Selecciona un jugador"); return; }
        
        let div = document.getElementById('resultado');
        div.innerHTML = '<p>Cargando...</p>';
        div.style.display = 'block';
        
        fetch('/api/recomendaciones_jugador/' + encodeURIComponent(nombre))
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    div.innerHTML = `<p>❌ ${data.error}</p>`;
                    return;
                }
                
                let html = `
                    <h2>⚽ ${data.jugador}</h2>
                    <div class="grid">
                        <div class="card"><div class="goles">${data.estadisticas.partidos}</div><div>Partidos</div></div>
                        <div class="card"><div class="goles">${data.estadisticas.goles_por_partido.toFixed(2)}</div><div>Goles/partido</div></div>
                        <div class="card"><div class="goles">${data.estadisticas.tiros_por_partido}</div><div>Tiros/partido</div></div>
                        <div class="card"><div class="goles">${data.estadisticas.rating_promedio}</div><div>Rating promedio</div></div>
                    </div>
                    <h3>🎯 Recomendaciones de apuesta</h3>
                `;
                
                for (let rec of data.recomendaciones) {
                    html += `
                        <div class="small-card">
                            <h3 style="color: #FFC107;">${rec.mercado}</h3>
                            <p>🎯 ${rec.apuesta}</p>
                            <p>📈 Probabilidad: ${rec.probabilidad}%</p>
                            <p>💰 Cuota sugerida: ${rec.cuota_sugerida}</p>
                            <p><small>📊 ${rec.estadistica}</small></p>
                        </div>
                    `;
                }
                
                div.innerHTML = html;
            })
            .catch(error => {
                console.error('Error:', error);
                div.innerHTML = '<p>❌ Error al cargar recomendaciones</p>';
            });
    }
</script>
</body>
</html>
"""

# ==================== PÁGINA TOP JUGADORES ====================
HTML_TOP_JUGADORES = """
<!DOCTYPE html>
<html>
<head>
    <title>Top Jugadores - Mundial 2026</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; color: #4CAF50; margin-bottom: 10px; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #4CAF50; text-decoration: none; margin: 0 10px; padding: 8px 20px; background: #0f3460; border-radius: 25px; display: inline-block; }
        .card { background: #0f3460; border-radius: 15px; padding: 20px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: center; border-bottom: 1px solid #2a2a4e; }
        th { background: #4CAF50; }
        tr:hover { background: #1a2a4e; }
        .btn { background: #2196F3; color: white; padding: 5px 10px; border-radius: 20px; text-decoration: none; font-size: 0.8em; }
        .gold { color: #FFD700; }
        .silver { color: #C0C0C0; }
        .bronze { color: #CD7F32; }
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <a href="/">🏆 Ranking</a>
        <a href="/jugador">🔍 Buscador</a>
        <a href="/eliminatorias">🌍 Eliminatorias</a>
        <a href="/resultados">📋 Resultados</a>
        <a href="/top_jugadores">⭐ Top Jugadores</a>
        <a href="/recomendaciones_jugadores">🎯 Recomendaciones</a>  <!-- NUEVO -->
    </div>
    
    <h1>⭐ Top Jugadores</h1>
    <p style="text-align:center">Estadísticas avanzadas de los mejores jugadores</p>
    
    <div class="card">
        <h3>⚽ Top Goleadores</h3>
        <table>
            <thead><tr><th>#</th><th>Jugador</th><th>Selección</th><th>Goles</th><th>Tiros</th><th>Efectividad</th><th>Rating</th><th></th></tr></thead>
            <tbody>
                {% for j in goleadores %}
                <tr>
                    <td>{% if loop.index == 1 %}🥇{% elif loop.index == 2 %}🥈{% elif loop.index == 3 %}🥉{% else %}{{ loop.index }}{% endif %}</td>
                    <td><strong>{{ j.nombre }}</strong></td>
                    <td>{{ j.seleccion }}</td>
                    <td>{{ j.goles|default(0) }}</td>
                    <td>{{ j.tiros_totales|default(0) }}</td>
                    <td>{{ (j.goles|default(0) / j.tiros_totales|default(1) * 100)|round(1) if j.tiros_totales|default(0) > 0 else 0 }}%</td>
                    <td>{{ j.rating|default(0) }}</td>
                    <td><a href="/estadisticas_jugador/{{ j.nombre }}" class="btn">Ver</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="card">
        <h3>🎯 Top Asistentes</h3>
        <table>
            <thead>
                <tr><th>#</th><th>Jugador</th><th>Selección</th><th>Asistencias</th><th>Pases clave</th><th>Rating</th><th></th></tr>
            </thead>
            <tbody>
                {% for j in asistentes %}
                <tr>
                    <td>{% if loop.index == 1 %}🥇{% elif loop.index == 2 %}🥈{% elif loop.index == 3 %}🥉{% else %}{{ loop.index }}{% endif %}</td>
                    <td><strong>{{ j.nombre }}</strong></td>
                    <td>{{ j.seleccion }}</td>
                    <td>{{ j.asistencias }}</td>
                    <td>{{ j.pases_clave|default(0) }}</td>
                    <td>{{ j.rating }}</td>
                    <td><a href="/estadisticas_jugador/{{ j.nombre }}" class="btn">Ver</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div style="text-align:center">
        <a href="/" class="btn" style="background:#4CAF50; padding:10px 20px;">← Volver al inicio</a>
    </div>
</div>
</body>
</html>
"""


# ==================== RUTAS ====================

# ==================== OPORTUNIDADES DE VALOR ====================

@app.route('/api/valor_oportunidades')
def api_valor_oportunidades():
    """Devuelve las mejores oportunidades de valor"""
    try:
        # Por ahora, devolvemos datos de ejemplo para probar
        oportunidades = [
            {
                "apuesta": "Argentina (Local) vs Brasil",
                "valor": 15.2,
                "cuota": 2.65,
                "prob_real": 48.5,
                "recomendacion": "🔥 MUY RECOMENDADA",
                "casa": "BetMGM"
            },
            {
                "apuesta": "Inglaterra (Visitante) vs Francia",
                "valor": 12.8,
                "cuota": 3.30,
                "prob_real": 42.0,
                "recomendacion": "🔥 MUY RECOMENDADA",
                "casa": "Bovada"
            },
            {
                "apuesta": "España (Local) vs Alemania",
                "valor": 8.5,
                "cuota": 2.40,
                "prob_real": 52.0,
                "recomendacion": "✅ RECOMENDADA",
                "casa": "DraftKings"
            }
        ]
        return jsonify(oportunidades)
    except Exception as e:
        print(f"Error en valor_oportunidades: {e}")
        return jsonify([])

@app.route('/')
def index():
    selecciones = obtener_selecciones()
    total_jugadores = sum(s.get('jugadores', 0) for s in selecciones)
    return render_template_string(HTML, selecciones=selecciones, total_selecciones=len(selecciones), total_jugadores=total_jugadores)

@app.route('/jugador')
def jugador():
    return render_template_string(HTML_JUGADOR)

@app.route('/eliminatorias')
def eliminatorias():
    return render_template_string(HTML_ELIMINATORIAS)

@app.route('/api/selecciones')
def api_selecciones():
    return jsonify(obtener_selecciones())

@app.route('/api/odds')
def api_odds():
    data = obtener_cuotas()
    if not data: return jsonify({'success': False}), 500
    partidos = []
    for p in data[:10]:
        cuotas = {'home':0,'draw':0,'away':0}
        casas = {'home':'','draw':'','away':''}
        for b in p.get('bookmakers',[]):
            for m in b.get('markets',[]):
                if m.get('key')=='h2h':
                    for o in m.get('outcomes',[]):
                        n, pr = o.get('name',''), o.get('price',0)
                        if n == p.get('home_team'): cuotas['home']=pr; casas['home']=b.get('title','')
                        elif n == 'Draw': cuotas['draw']=pr; casas['draw']=b.get('title','')
                        else: cuotas['away']=pr; casas['away']=b.get('title','')
        partidos.append({'home_team':p.get('home_team'),'away_team':p.get('away_team'),'cuotas':cuotas,'mejores_casas':casas})
    return jsonify({'success': True, 'games': partidos})

@app.route('/api/pronostico')
def api_pronostico():
    local = request.args.get('local', '')
    visitante = request.args.get('visitante', '')
    p = pronostico(local, visitante)
    if p: return jsonify(p)
    return jsonify({'error': 'Error'}), 404

@app.route('/api/historial')
def api_historial():
    e1, e2 = request.args.get('eq1', ''), request.args.get('eq2', '')
    h = obtener_historial(e1, e2)
    if h:
        return jsonify(h)
    return jsonify({'error': 'No hay historial de enfrentamientos entre estos equipos'}), 404

@app.route('/api/jugador/buscar')
def api_buscar_jugador():
    nombre = request.args.get('nombre', '').lower()
    for k, v in JUGADORES_MANUALES.items():
        if k in nombre or nombre in k:
            return jsonify(v)
    return jsonify({'error': 'No encontrado'}), 404

@app.route('/resultados')
def resultados():
    selecciones = obtener_selecciones()
    return render_template_string(HTML_RESULTADOS, selecciones=selecciones)

@app.route('/api/partidos/<seleccion>')
def api_partidos(seleccion):
    partidos = obtener_partidos_por_seleccion(seleccion)
    if partidos:
        return jsonify(partidos)
    return jsonify({'error': 'No se encontraron partidos'}), 404

@app.route('/top_jugadores')
def top_jugadores():
    """Muestra el top de jugadores por estadísticas"""
    try:
        from bson.json_util import dumps
        import json
        
        # Obtener jugadores
        jugadores = list(db['estadisticas_jugadores'].find({}, {'_id': 0}))
        
        if not jugadores:
            return """
            <html>
            <body style="background:#1a1a2e;color:white;font-family:Arial;padding:20px">
                <h1>⚠️ No hay datos de jugadores</h1>
                <p>La colección 'estadisticas_jugadores' está vacía.</p>
                <a href="/">Volver al inicio</a>
            </body>
            </html>
            """
        
        # Función segura para obtener goles (maneja None)
        def get_goles(j):
            val = j.get('goles')
            return val if isinstance(val, (int, float)) and val is not None else 0
        
        def get_asistencias(j):
            val = j.get('asistencias')
            return val if isinstance(val, (int, float)) and val is not None else 0
        
        def get_nombre(j):
            return j.get('nombre', 'Desconocido')
        
        def get_seleccion(j):
            return j.get('seleccion', 'N/A')
        
        def get_tiros_totales(j):
            val = j.get('tiros_totales')
            return val if isinstance(val, (int, float)) and val is not None else 0
        
        def get_rating(j):
            val = j.get('rating')
            return val if isinstance(val, (int, float)) and val is not None else 0
        
        # Limpiar datos: eliminar jugadores sin nombre o con valores inválidos
        jugadores_limpios = []
        for j in jugadores:
            if j.get('nombre') and j.get('nombre') != 'N/A':
                # Asegurar valores numéricos
                j['goles'] = get_goles(j)
                j['asistencias'] = get_asistencias(j)
                j['tiros_totales'] = get_tiros_totales(j)
                j['rating'] = get_rating(j)
                jugadores_limpios.append(j)
        
        # Ordenar por goles
        goleadores = sorted(jugadores_limpios, key=lambda x: x.get('goles', 0), reverse=True)
        
        # Ordenar por asistencias
        asistentes = sorted(jugadores_limpios, key=lambda x: x.get('asistencias', 0), reverse=True)
        
        return render_template_string(HTML_TOP_JUGADORES, goleadores=goleadores, asistentes=asistentes)
    
    except Exception as e:
        import traceback
        error_detalle = traceback.format_exc()
        return f"""
        <html>
        <body style="background:#1a1a2e;color:white;font-family:Arial;padding:20px">
            <h1>❌ Error en el servidor</h1>
            <pre>{error_detalle}</pre>
            <a href="/">Volver al inicio</a>
        </body>
        </html>
        """, 500

@app.route('/api/analisis_partido/<local>/<visitante>')
def api_analisis_partido(local, visitante):
    """Análisis completo del partido con recomendaciones de jugadores"""
    try:
        # Estadísticas del partido
        estadisticas = predecir_estadisticas_partido(local, visitante)
        
        # Recomendaciones de mercado general (goles, corners, etc.)
        recomendaciones_generales = generar_recomendaciones(estadisticas)
        
        # Recomendaciones de jugadores clave
        recomendaciones_jugadores = generar_recomendaciones_partido(local, visitante)
        
        # Combinar ambas
        todas_recomendaciones = recomendaciones_generales + recomendaciones_jugadores
        
        for rec in todas_recomendaciones:
            if 'cuota_sugerida' not in rec:
                cuota_justa = round(100 / rec.get("probabilidad", 50), 2)
                rec["cuota_sugerida"] = round(cuota_justa * 0.95, 2)
        
        return jsonify({
            "local": local,
            "visitante": visitante,
            "estadisticas": estadisticas,
            "recomendaciones": todas_recomendaciones,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/estadisticas_jugador/<nombre>')
def estadisticas_jugador(nombre):
    """Muestra estadísticas detalladas de un jugador"""
    jugador = db['estadisticas_jugadores'].find_one({"nombre": nombre}, {'_id': 0})
    
    if not jugador:
        return f"""
        <html>
        <body style="background:#1a1a2e;color:white;font-family:Arial;padding:20px">
            <h1>❌ Jugador no encontrado</h1>
            <p>No hay estadísticas disponibles para {nombre}</p>
            <a href="/top_jugadores">Volver al top de jugadores</a>
        </body>
        </html>
        """
    
    return render_template_string(HTML_ESTADISTICAS_JUGADOR, jugador=jugador)

# ==================== NUEVAS FUNCIONES PARA RECOMENDACIONES DE JUGADORES ====================

@app.route('/recomendaciones_jugadores')
def recomendaciones_jugadores():
    """Página de recomendaciones por jugador"""
    return render_template_string(HTML_RECOMENDACIONES_JUGADOR)

@app.route('/api/top_jugadores_estadisticas')
def api_top_jugadores_estadisticas():
    """API con top jugadores por goles"""
    try:
        jugadores = list(db.estadisticas_jugadores_bzzoiro.find(
            {"participa_mundial": {"$eq": True}}, 
            {'_id': 0, 'nombre': 1, 'goles': 1, 'goles_por_partido': 1, 
             'tiros_por_partido': 1, 'rating_promedio': 1, 'partidos': 1, 'seleccion': 1}
        ).sort('goles', -1).limit(20))
        return jsonify(jugadores)
    except Exception as e:
        return jsonify([])

@app.route('/api/recomendaciones_jugador/<nombre>')
def api_recomendaciones_jugador(nombre):
    """Recomendaciones de apuesta para un jugador del Mundial"""
    try:
        jugador = db.estadisticas_jugadores_bzzoiro.find_one( {"nombre": nombre, "participa_mundial": {"$eq": True}}
        )
        
        if not jugador:
            return jsonify({"error": "Jugador no encontrado o no participa en el Mundial"}), 404
        
        recomendaciones = []
        
        # Recomendación de gol
        prob_gol = min(85, jugador.get('goles_por_partido', 0) * 45)
        if prob_gol > 20:
            recomendaciones.append({
                "mercado": "⚽ GOL",
                "apuesta": f"{jugador['nombre']} anotará un gol",
                "probabilidad": round(prob_gol, 1),
                "cuota_sugerida": round(100 / prob_gol, 2),
                "estadistica": f"{jugador.get('goles', 0)} goles en {jugador.get('partidos', 0)} partidos"
            })
        
        # Recomendación de tiros
        tiros_por_partido = jugador.get('tiros_por_partido', 0)
        if tiros_por_partido > 3:
            prob_tiros = min(80, 40 + tiros_por_partido * 8)
            recomendaciones.append({
                "mercado": "🎯 TIROS",
                "apuesta": f"{jugador['nombre']} - Más de 2.5 tiros",
                "probabilidad": round(prob_tiros, 1),
                "cuota_sugerida": round(100 / prob_tiros, 2),
                "estadistica": f"{jugador.get('tiros_totales', 0)} tiros en {jugador.get('partidos', 0)} partidos"
            })
        
        return jsonify({
            "jugador": jugador['nombre'],
            "estadisticas": {
                "partidos": jugador.get('partidos', 0),
                "goles_por_partido": jugador.get('goles_por_partido', 0),
                "tiros_por_partido": jugador.get('tiros_por_partido', 0),
                "rating_promedio": jugador.get('rating_promedio', 0)
            },
            "recomendaciones": recomendaciones
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
