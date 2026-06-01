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

# ==================== CARGAR MODELO ML (OPCIONAL) ====================
ML_DISPONIBLE = False
modelo_ml = None
scaler_ml = None

try:
    import joblib
    if os.path.exists('modelo_pronostico.pkl') and os.path.exists('scaler.pkl'):
        modelo_ml = joblib.load('modelo_pronostico.pkl')
        scaler_ml = joblib.load('scaler.pkl')
        ML_DISPONIBLE = True
        print("✅ Modelo ML cargado correctamente")
    else:
        print("⚠️ Archivos del modelo ML no encontrados")
except ImportError:
    print("⚠️ Librería joblib no disponible, ejecutando sin modelo ML")
except Exception as e:
    print(f"⚠️ Error cargando modelo ML: {e}")

# ==================== CARGAR MODELO ML ====================
# Intentar cargar el modelo ML si existe
try:
    modelo_ml = joblib.load('modelo_pronostico.pkl')
    scaler_ml = joblib.load('scaler.pkl')
    print("✅ Modelo ML cargado correctamente")
    ML_DISPONIBLE = True
except:
    print("⚠️ Modelo ML no disponible, usando pronóstico tradicional")
    ML_DISPONIBLE = False

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

def pronostico_ml(local, visitante):
    """Pronóstico usando Machine Learning"""
    if not ML_DISPONIBLE:
        return None
    
    # Obtener datos de las selecciones
    selecciones = obtener_selecciones()
    
    d1 = next((s for s in selecciones if s.get('nombre') == local), None)
    d2 = next((s for s in selecciones if s.get('nombre') == visitante), None)
    
    if not d1 or not d2:
        return None
    
    # Preparar características para el modelo
    ranking_local = d1.get('ranking_fifa', 15)
    ranking_visitante = d2.get('ranking_fifa', 15)
    
    # Calcular fuerza
    fuerza_local = max(0, (100 - ranking_local) / 100)
    fuerza_visitante = max(0, (100 - ranking_visitante) / 100)
    
    # Otras características
    diferencia_fuerza = fuerza_local - fuerza_visitante
    diferencia_fuerza_abs = abs(diferencia_fuerza)
    prob_local_base = fuerza_local / (fuerza_local + fuerza_visitante + 0.01)
    prob_visitante_base = fuerza_visitante / (fuerza_local + fuerza_visitante + 0.01)
    diferencia_ranking = ranking_visitante - ranking_local
    goles_prom_local = d1.get('goles_total', 30) / max(1, d1.get('jugadores', 20)) / 5
    goles_prom_visit = d2.get('goles_total', 30) / max(1, d2.get('jugadores', 20)) / 5
    ratio_goles = goles_prom_local / (goles_prom_visit + 0.1)
    
    # Crear vector de características (16 features)
    features = {
        'ranking_local': ranking_local,
        'ranking_visitante': ranking_visitante,
        'fuerza_local': fuerza_local,
        'fuerza_visitante': fuerza_visitante,
        'diferencia_fuerza': diferencia_fuerza,
        'diferencia_fuerza_abs': diferencia_fuerza_abs,
        'prob_local_base': prob_local_base,
        'prob_visitante_base': prob_visitante_base,
        'ratio_goles': ratio_goles,
        'diferencia_ranking': diferencia_ranking,
        'rank_cat_ligera_ventaja_local': 1 if -10 < diferencia_ranking <= 0 else 0,
        'rank_cat_ligera_ventaja_visitante': 1 if 0 < diferencia_ranking <= 10 else 0,
        'rank_cat_mucha_ventaja_local': 1 if diferencia_ranking <= -20 else 0,
        'rank_cat_mucha_ventaja_visitante': 1 if diferencia_ranking >= 20 else 0,
        'rank_cat_ventaja_local': 1 if -20 < diferencia_ranking <= -10 else 0,
        'rank_cat_ventaja_visitante': 1 if 10 < diferencia_ranking <= 20 else 0,
    }
    
    # Convertir a DataFrame y escalar
    import pandas as pd
    features_df = pd.DataFrame([features])
    
    # Asegurar el orden correcto de las columnas
    columnas_orden = scaler_ml.feature_names_in_
    features_df = features_df[columnas_orden]
    
    features_scaled = scaler_ml.transform(features_df)
    prob = modelo_ml.predict_proba(features_scaled)[0]
    
    return {
        'local': round(prob[0] * 100, 1),
        'empate': round(prob[1] * 100, 1),
        'visitante': round(prob[2] * 100, 1),
        'modelo': 'ML (XGBoost)'
    }

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
    <button class="btn-blue" onclick="calcularPronosticoML()">🤖 ML</button>
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
    
function calcularPronosticoML() {
    let local = document.getElementById('eqLocal').value;
    let visitante = document.getElementById('eqVisitante').value;
    if (!local || !visitante) { alert("Selecciona dos equipos"); return; }
    if (local === visitante) { alert("Equipos diferentes"); return; }
    let div = document.getElementById('pronosticoResultado');
    div.innerHTML = '<p>Cargando pronóstico ML...</p>';
    div.style.display = 'block';
    fetch('/api/pronostico_ml?local='+encodeURIComponent(local)+'&visitante='+encodeURIComponent(visitante))
        .then(r=>r.json())
        .then(data=>{
            div.innerHTML = `<div class="grid-3">
                <div class="stat-card"><div class="big-number">${data.local}%</div><div>🏠 ${local}</div></div>
                <div class="stat-card"><div class="big-number">${data.empate}%</div><div>🤝 Empate</div></div>
                <div class="stat-card"><div class="big-number">${data.visitante}%</div><div>✈️ ${visitante}</div></div>
            </div>
            <div style="background:#1a1a2e;padding:15px;border-radius:10px;text-align:center">
                🤖 Pronóstico con Machine Learning<br>
                <small>Modelo XGBoost entrenado con 5000 partidos</small>
            </div>`;
        })
        .catch(e => div.innerHTML = '<p>Error al calcular pronóstico ML</p>');
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
    <div class="nav"><a href="/">🏆 Ranking</a><a href="/jugador">🔍 Jugadores</a><a href="/eliminatorias">🌍 Eliminatorias</a><a href="/resultados">📋 Resultados</a></div>
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
    <div class="nav"><a href="/">🏆 Ranking</a><a href="/jugador">🔍 Jugadores</a><a href="/eliminatorias">🌍 Eliminatorias</a><a href="/resultados">📋 Resultados</a></div>
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

@app.route('/api/pronostico_ml')
def api_pronostico_ml():
    local = request.args.get('local', '')
    visitante = request.args.get('visitante', '')
    p = pronostico_ml(local, visitante)
    if p:
        return jsonify(p)
    return jsonify({'error': 'Modelo ML no disponible'}), 404


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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
