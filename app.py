import os
import requests
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

# ==================== SISTEMA DE CACHÉ PARA API-FOOTBALL ====================
from datetime import datetime, timedelta
import hashlib

# Colección para caché de jugadores
# Asegúrate de crear esta colección en MongoDB
cache_coleccion = db['cache_jugadores'] if coleccion is not None else None

def generar_cache_key(nombre_jugador):
    """Genera una clave única para cada jugador"""
    return hashlib.md5(nombre_jugador.lower().encode()).hexdigest()

def obtener_desde_cache(nombre_jugador):
    """
    Obtiene un jugador desde la caché si existe y no ha expirado
    """
    if cache_coleccion is None:
        return None
    
    cache_key = generar_cache_key(nombre_jugador)
    
    try:
        cache_entry = cache_coleccion.find_one({'key': cache_key})
        
        if not cache_entry:
            print(f"📦 Caché: '{nombre_jugador}' no encontrado en caché")
            return None
        
        # Verificar si ha expirado (7 días)
        last_update = cache_entry.get('last_update')
        if last_update:
            fecha_update = datetime.fromisoformat(last_update)
            if datetime.now() - fecha_update > timedelta(days=7):
                print(f"⏰ Caché: '{nombre_jugador}' expirado (más de 7 días)")
                # Eliminar entrada expirada
                cache_coleccion.delete_one({'key': cache_key})
                return None
        
        print(f"✅ Caché: '{nombre_jugador}' encontrado (actualizado: {last_update})")
        return cache_entry.get('data')
        
    except Exception as e:
        print(f"❌ Error leyendo caché: {e}")
        return None

def guardar_en_cache(nombre_jugador, datos_jugador):
    """
    Guarda un jugador en la caché
    """
    if cache_coleccion is None or datos_jugador is None:
        return
    
    cache_key = generar_cache_key(nombre_jugador)
    
    try:
        cache_entry = {
            'key': cache_key,
            'nombre': nombre_jugador,
            'data': datos_jugador,
            'last_update': datetime.now().isoformat(),
            'expira_en': (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        # Reemplazar si ya existe
        cache_coleccion.update_one(
            {'key': cache_key},
            {'$set': cache_entry},
            upsert=True
        )
        print(f"💾 Caché: '{nombre_jugador}' guardado (expira en 7 días)")
        
    except Exception as e:
        print(f"❌ Error guardando en caché: {e}")

def obtener_estadisticas_con_cache(nombre_jugador, force_refresh=False):
    """
    Obtiene estadísticas de un jugador usando caché
    Primero busca en caché, si no está o force_refresh=True, consulta API
    """
    if not force_refresh:
        # Intentar obtener desde caché
        datos_cache = obtener_desde_cache(nombre_jugador)
        if datos_cache:
            datos_cache['fuente'] = 'Caché (datos reales)'
            return datos_cache
    
    # Si no está en caché o se fuerza actualización, consultar API
    print(f"🌐 Consultando API-Football para '{nombre_jugador}'...")
    datos_reales = obtener_estadisticas_reales_jugador(nombre_jugador)
    
    if datos_reales:
        # Guardar en caché para futuras consultas
        guardar_en_cache(nombre_jugador, datos_reales)
        datos_reales['fuente'] = 'API-Football (datos reales)'
        return datos_reales
    
    return None

def limpiar_cache_expirada():
    """Elimina todas las entradas de caché expiradas"""
    if cache_coleccion is None:
        return
    
    try:
        resultado = cache_coleccion.delete_many({
            'expira_en': {'$lt': datetime.now().isoformat()}
        })
        print(f"🧹 Caché limpiada: {resultado.deleted_count} entradas expiradas eliminadas")
    except Exception as e:
        print(f"❌ Error limpiando caché: {e}")

def estadisticas_cache():
    """Muestra estadísticas del caché"""
    if cache_coleccion is None:
        return
    
    total = cache_coleccion.count_documents({})
    print(f"📊 CACHÉ STATS:")
    print(f"   • Total jugadores en caché: {total}")
    
    # Mostrar últimos 5 guardados
    ultimos = cache_coleccion.find().sort('last_update', -1).limit(5)
    print(f"   • Últimos guardados:")
    for doc in ultimos:
        print(f"     - {doc['nombre']} (actualizado: {doc['last_update'][:10]})")

# ==================== API-FOOTBALL - DATOS REALES ====================
import requests

API_FOOTBALL_KEY = "2d815f1ac9a12c9296b3f9c3f5d30f7c"
API_FOOTBALL_URL = "https://v3.football.api-sports.io"

def obtener_estadisticas_reales_jugador(nombre_jugador):
    """
    Obtiene estadísticas REALES de un jugador desde API-Football
    """
    print(f"🔍 Buscando '{nombre_jugador}' en API-Football...")
    
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY,
        "x-apisports-host": "v3.football.api-sports.io"
    }
    
    try:
        url_search = f"{API_FOOTBALL_URL}/players"
        params_search = {"search": nombre_jugador}
        
        response = requests.get(url_search, headers=headers, params=params_search)
        data = response.json()
        
        remaining = response.headers.get('x-ratelimit-requests-remaining', 'N/A')
        print(f"📊 Peticiones restantes hoy: {remaining}")
        
        if data.get('results', 0) == 0:
            print(f"❌ No se encontró a '{nombre_jugador}'")
            return None
        
        jugador = data['response'][0]
        player_id = jugador['player']['id']
        print(f"✅ Encontrado: {jugador['player']['name']} (ID: {player_id})")
        
        # Obtener estadísticas detalladas
        url_stats = f"{API_FOOTBALL_URL}/players"
        params_stats = {"id": player_id, "season": 2025}
        
        response_stats = requests.get(url_stats, headers=headers, params=params_stats)
        data_stats = response_stats.json()
        
        if data_stats.get('results', 0) == 0:
            return {
                'nombre': jugador['player']['name'],
                'equipo': 'N/A',
                'edad': jugador['player'].get('age', 'N/A'),
                'posicion': jugador['player'].get('position', 'N/A'),
                'partidos': 0,
                'goles': 0,
                'asistencias': 0,
                'tiros_por_partido': 0,
                'pases_clave_por_partido': 0,
                'regates_por_partido': 0,
                'fuente': 'API-Football'
            }
        
        stats = data_stats['response'][0]['statistics'][0] if data_stats['response'] else {}
        partidos = stats.get('games', {}).get('appearences', 1)
        if partidos == 0:
            partidos = 1
        
        return {
            'nombre': jugador['player']['name'],
            'equipo': stats.get('team', {}).get('name', 'N/A'),
            'edad': jugador['player']['age'],
            'posicion': jugador['player']['position'],
            'partidos': partidos,
            'goles': stats.get('goals', {}).get('total', 0),
            'asistencias': stats.get('goals', {}).get('assists', 0),
            'tiros_totales': stats.get('shots', {}).get('total', 0),
            'tiros_puerta': stats.get('shots', {}).get('on', 0),
            'tiros_por_partido': round(stats.get('shots', {}).get('total', 0) / partidos, 2),
            'pases_clave': stats.get('passes', {}).get('key', 0),
            'pases_clave_por_partido': round(stats.get('passes', {}).get('key', 0) / partidos, 2),
            'regates': stats.get('dribbles', {}).get('success', 0),
            'regates_por_partido': round(stats.get('dribbles', {}).get('success', 0) / partidos, 2),
            'entradas': stats.get('tackles', {}).get('total', 0),
            'intercepciones': stats.get('tackles', {}).get('interceptions', 0),
            'rating': stats.get('rating', 0),
            'fuente': 'API-Football (datos reales)'
        }
        
    except Exception as e:
        print(f"❌ Error en API-Football: {e}")
        return None
        
        # Tomar las estadísticas (pueden ser de varias ligas)
        stats = data_stats['response'][0]['statistics'][0] if data_stats['response'] else {}
        
        # Calcular promedios por partido
        partidos = stats.get('games', {}).get('appearences', 1)
        if partidos == 0:
            partidos = 1
        
        return {
            'nombre': jugador['player']['name'],
            'equipo': stats.get('team', {}).get('name', 'N/A'),
            'edad': jugador['player']['age'],
            'posicion': jugador['player']['position'],
            'partidos': partidos,
            'goles': stats.get('goals', {}).get('total', 0),
            'asistencias': stats.get('goals', {}).get('assists', 0),
            'tiros_totales': stats.get('shots', {}).get('total', 0),
            'tiros_puerta': stats.get('shots', {}).get('on', 0),
            'tiros_por_partido': round(stats.get('shots', {}).get('total', 0) / partidos, 2),
            'pases_clave': stats.get('passes', {}).get('key', 0),
            'pases_clave_por_partido': round(stats.get('passes', {}).get('key', 0) / partidos, 2),
            'regates': stats.get('dribbles', {}).get('success', 0),
            'regates_por_partido': round(stats.get('dribbles', {}).get('success', 0) / partidos, 2),
            'entradas': stats.get('tackles', {}).get('total', 0),
            'intercepciones': stats.get('tackles', {}).get('interceptions', 0),
            'rating': stats.get('rating', 0),
            'fuente': 'API-Football (datos reales)'
        }
        
    except Exception as e:
        print(f"❌ Error en API-Football: {e}")
        return None

def obtener_partidos_hoy():
    """
    Obtiene los partidos de fútbol de hoy
    """
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY,
        "x-apisports-host": "v3.football.api-sports.io"
    }
    
    try:
        from datetime import datetime
        fecha = datetime.now().strftime("%Y-%m-%d")
        
        url = f"{API_FOOTBALL_URL}/fixtures"
        params = {"date": fecha}
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        if data.get('results', 0) == 0:
            return []
        
        partidos = []
        for p in data['response'][:10]:
            partidos.append({
                'home_team': p['teams']['home']['name'],
                'away_team': p['teams']['away']['name'],
                'home_logo': p['teams']['home']['logo'],
                'away_logo': p['teams']['away']['logo'],
                'status': p['fixture']['status']['short'],
                'time': p['fixture']['date']
            })
        
        return partidos
        
    except Exception as e:
        print(f"Error obteniendo partidos: {e}")
        return []


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
        .charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .chart-box { background: #0f3460; padding: 20px; border-radius: 15px; text-align: center; }
        canvas { max-height: 300px; width: 100% !important; }
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
        .odds-card { background: #1a1a2e; border-radius: 10px; padding: 15px; margin-bottom: 10px; }
        .odds-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; }
        @media (max-width: 600px) { .grid-3 { grid-template-columns: 1fr; } .charts { grid-template-columns: 1fr; } .odds-grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <a href="/">🏆 Ranking</a>
        <a href="/jugador">🔍 Jugadores</a>
        <a href="/eliminatorias">🌍 Eliminatorias</a>
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
        <div class="chart-box">
            <h3>⭐ Top 10 - Rating Promedio</h3>
            <canvas id="ratingChart" width="500" height="300" style="width:100%; height:auto; max-height:300px;"></canvas>
        </div>
        <div class="chart-box">
            <h3>⚽ Top 10 - Goles Totales</h3>
            <canvas id="golesChart" width="500" height="300" style="width:100%; height:auto; max-height:300px;"></canvas>
        </div>
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
    
    <!-- Cuotas -->
    <h2>📊 Cuotas Tiempo Real</h2>
    <button class="btn-blue" onclick="cargarCuotas()">🔄 Actualizar</button>
    <div id="cuotasResultado" style="margin-top:15px;"></div>
    
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
        const canvasRating = document.getElementById('ratingChart');
        const canvasGoles = document.getElementById('golesChart');
        
        if (!canvasRating || !canvasGoles) return;
        
        fetch('/api/selecciones')
            .then(r => r.json())
            .then(data => {
                const topRating = [...data].filter(s => s.rating_promedio > 0).sort((a,b) => b.rating_promedio - a.rating_promedio).slice(0,10);
                const topGoles = [...data].sort((a,b) => b.goles_total - a.goles_total).slice(0,10);
                
                if (ratingChart) ratingChart.destroy();
                ratingChart = new Chart(canvasRating, {
                    type: 'bar',
                    data: { labels: topRating.map(t=>t.nombre), datasets: [{ label: 'Rating Promedio', data: topRating.map(t=>t.rating_promedio), backgroundColor: 'rgba(76,175,80,0.8)', borderRadius: 8 }] },
                    options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#fff' } } }, scales: { y: { ticks: { color: '#fff' } }, x: { ticks: { color: '#fff', rotation: 45 } } } }
                });
                
                if (golesChart) golesChart.destroy();
                golesChart = new Chart(canvasGoles, {
                    type: 'bar',
                    data: { labels: topGoles.map(t=>t.nombre), datasets: [{ label: 'Goles Totales', data: topGoles.map(t=>t.goles_total), backgroundColor: 'rgba(33,150,243,0.8)', borderRadius: 8 }] },
                    options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#fff' } } }, scales: { y: { ticks: { color: '#fff' } }, x: { ticks: { color: '#fff', rotation: 45 } } } }
                });
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
                div.innerHTML = `<div class="grid-3"><div class="stat-card"><div class="big-number">${data.local}%</div><div>🏠 ${local}</div></div><div class="stat-card"><div class="big-number">${data.empate}%</div><div>🤝 Empate</div></div><div class="stat-card"><div class="big-number">${data.visitante}%</div><div>✈️ ${visitante}</div></div></div><div style="background:#1a1a2e;padding:15px;border-radius:10px;text-align:center">${data.recomendacion}</div>`;
            });
    }
    
    function cargarCuotas() {
        let div = document.getElementById('cuotasResultado');
        div.innerHTML = '<p>Cargando cuotas...</p>';
        fetch('/api/odds')
            .then(r => r.json())
            .then(data => {
                if (!data.success || data.games.length === 0) { div.innerHTML = '<p>No hay partidos disponibles</p>'; return; }
                let html = '';
                for (let g of data.games.slice(0,10)) {
                    html += `<div class="odds-card"><strong>${g.home_team} 🆚 ${g.away_team}</strong><div class="odds-grid"><div class="stat-card">🏠 Local<br><span class="big-number">${g.cuotas.home > 0 ? g.cuotas.home.toFixed(2) : 'N/A'}</span><br><small>${g.mejores_casas.home}</small></div><div class="stat-card">🤝 Empate<br><span class="big-number">${g.cuotas.draw > 0 ? g.cuotas.draw.toFixed(2) : 'N/A'}</span><br><small>${g.mejores_casas.draw}</small></div><div class="stat-card">✈️ Visitante<br><span class="big-number">${g.cuotas.away > 0 ? g.cuotas.away.toFixed(2) : 'N/A'}</span><br><small>${g.mejores_casas.away}</small></div></div></div>`;
                }
                div.innerHTML = html;
            })
            .catch(e => div.innerHTML = '<p>Error cargando cuotas</p>');
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
                let html = `<div style="background:#0f3460;border-radius:15px;padding:20px"><h3>📊 ${local} vs ${visitante}</h3><div class="grid-3"><div class="stat-card">🏆 Total<br><span class="big-number">${data.total}</span><br>partidos</div><div class="stat-card">⚽ Goles ${local}<br><span class="big-number">${data.goles_local}</span></div><div class="stat-card">⚽ Goles ${visitante}<br><span class="big-number">${data.goles_visitante}</span></div></div><h4>📋 Partidos</h4><table style="width:100%"><thead><tr><th>Fecha</th><th>Competición</th><th>Resultado</th></tr></thead><tbody>`;
                for (let p of data.partidos) { html += `<tr><td>${p.fecha}</td><td>${p.competicion}</td><td>${p.resultado}</td></tr>`; }
                html += `</tbody></table></div>`;
                div.innerHTML = html;
            });
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        cargarGraficos();
        setTimeout(cargarCuotas, 500);
    });
</script>
</body>
</html>
"""
# ==================== RUTAS ====================

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

@app.route('/resultados')
def resultados():
    selecciones = obtener_selecciones()
    return render_template_string(HTML_RESULTADOS, selecciones=selecciones)

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

@app.route('/api/partidos/<seleccion>')
def api_partidos(seleccion):
    partidos = obtener_partidos_por_seleccion(seleccion)
    if partidos:
        return jsonify(partidos)
    return jsonify({'error': 'No se encontraron partidos'}), 404

@app.route('/api/estadisticas/<nombre>')
def api_estadisticas(nombre):
    """Obtiene estadísticas de un jugador usando caché"""
    datos = obtener_estadisticas_con_cache(nombre)
    
    if datos:
        return jsonify(datos)
    
    # Fallback a datos manuales
    nombre_limpio = nombre.lower()
    for key, data in JUGADORES_MANUALES.items():
        if key in nombre_limpio or nombre_limpio in key:
            return jsonify({
                'nombre': data['player'],
                'equipo': data['team'],
                'liga': data['league'],
                'goles': data['goals'],
                'asistencias': data['assists'],
                'rating': data['rating'],
                'tiros_por_partido': data.get('tiros_por_partido', 0),
                'pases_clave_por_partido': data.get('pases_clave_por_partido', 0),
                'regates_por_partido': data.get('regates_por_partido', 0),
                'fuente': 'Datos manuales (fallback)'
            })
    
    return jsonify({'error': 'Jugador no encontrado'}), 404

@app.route('/api/cache/stats')
def api_cache_stats():
    """Muestra estadísticas del caché"""
    if cache_coleccion is None:
        return jsonify({'error': 'Caché no disponible'}), 500
    
    total = cache_coleccion.count_documents({})
    expirados = cache_coleccion.count_documents({
        'expira_en': {'$lt': datetime.now().isoformat()}
    })
    
    return jsonify({
        'total_jugadores': total,
        'expirados': expirados,
        'activos': total - expirados
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
