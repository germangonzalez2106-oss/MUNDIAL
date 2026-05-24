import os
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = "mongodb://mundial_user:M4nzana2026@ac-0tfmbvr-shard-00-00.tqvej0i.mongodb.net:27017,ac-0tfmbvr-shard-00-01.tqvej0i.mongodb.net:27017,ac-0tfmbvr-shard-00-02.tqvej0i.mongodb.net:27017/?ssl=true&replicaSet=atlas-fjc1fq-shard-0&authSource=admin&tlsAllowInvalidCertificates=true"

try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=15000)
    db = client['mundial_2026']
    coleccion = db['selecciones']
    print(f"✅ Conectado a MongoDB Atlas: {coleccion.count_documents({})} selecciones")
except Exception as e:
    print(f"❌ Error: {e}")
    coleccion = None

# ==================== BASE DE DATOS MANUAL DE JUGADORES ====================
JUGADORES_MANUALES = {
    "messi": {
        "player": "Lionel Messi",
        "team": "Inter Miami",
        "league": "MLS",
        "position": "Delantero",
        "goals": 12,
        "assists": 8,
        "rating": 8.2,
        "totalShots": 48,
        "shotsOnTarget": 28,
        "keyPasses": 45,
        "successfulDribbles": 62,
        "tackles": 8,
        "interceptions": 4,
        "accuratePassesPercentage": 87.5,
        "yellowCards": 2,
        "redCards": 0,
        "minutesPlayed": 1170,
        "appearances": 13,
        "expectedGoals": 10.5,
        "expectedAssists": 7.2,
        "nota": "Máximo asistidor de la MLS, 100 contribuciones en 64 partidos"
    },
    "cristiano ronaldo": {
        "player": "Cristiano Ronaldo",
        "team": "Al Nassr",
        "league": "Saudi Pro League",
        "position": "Delantero",
        "goals": 28,
        "assists": 6,
        "rating": 7.9,
        "totalShots": 98,
        "shotsOnTarget": 52,
        "keyPasses": 32,
        "successfulDribbles": 28,
        "tackles": 5,
        "interceptions": 2,
        "accuratePassesPercentage": 82.3,
        "yellowCards": 4,
        "redCards": 0,
        "minutesPlayed": 2430,
        "appearances": 27,
        "expectedGoals": 24.5,
        "expectedAssists": 5.8,
        "nota": "Campeón de la Saudi Pro League 2025-2026, 102 goles con Al Nassr"
    },
    "neymar": {
        "player": "Neymar Jr",
        "team": "Al Hilal",
        "league": "Saudi Pro League",
        "position": "Delantero",
        "goals": 15,
        "assists": 12,
        "rating": 7.8,
        "totalShots": 52,
        "shotsOnTarget": 28,
        "keyPasses": 58,
        "successfulDribbles": 72,
        "tackles": 10,
        "interceptions": 3,
        "accuratePassesPercentage": 85.7,
        "yellowCards": 6,
        "redCards": 1,
        "minutesPlayed": 1890,
        "appearances": 21,
        "expectedGoals": 12.8,
        "expectedAssists": 10.2,
        "nota": "Líder en asistencias de la Saudi Pro League"
    },
    "benzema": {
        "player": "Karim Benzema",
        "team": "Al Ittihad",
        "league": "Saudi Pro League",
        "position": "Delantero",
        "goals": 22,
        "assists": 8,
        "rating": 7.7,
        "totalShots": 68,
        "shotsOnTarget": 38,
        "keyPasses": 28,
        "successfulDribbles": 18,
        "tackles": 4,
        "interceptions": 1,
        "accuratePassesPercentage": 83.1,
        "yellowCards": 3,
        "redCards": 0,
        "minutesPlayed": 2160,
        "appearances": 24,
        "expectedGoals": 19.5,
        "expectedAssists": 6.5,
        "nota": "Segundo máximo goleador de la Saudi Pro League"
    }
}

def obtener_selecciones():
    if coleccion is None: return []
    return list(coleccion.find({}, {'_id': 0}))

def obtener_seleccion(nombre):
    if coleccion is None: return None
    return coleccion.find_one({'nombre': nombre}, {'_id': 0})

def buscar_jugadores(termino):
    if coleccion is None: return []
    resultados = []
    for sel in coleccion.find({}, {'_id': 0}):
        for jug in sel.get('plantilla', []):
            if termino.lower() in jug.get('jugador', '').lower():
                resultados.append({
                    'seleccion': sel['nombre'],
                    'jugador': jug['jugador'],
                    'goles': jug['goles'],
                    'asistencias': jug['asistencias'],
                    'rating': jug['rating']
                })
    return resultados

def buscar_jugador_local(nombre_jugador):
    """Busca jugador en base manual"""
    nombre_limpio = nombre_jugador.lower().strip()
    for key, data in JUGADORES_MANUALES.items():
        if key in nombre_limpio or nombre_limpio in key:
            return data
    return None

# ==================== HTML PRINCIPAL ====================
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Mundial 2026 - Estadísticas y Pronósticos</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; color: #4CAF50; margin-bottom: 10px; font-size: 2.5em; }
        .subtitle { text-align: center; color: #aaa; margin-bottom: 30px; }
        
        .nav-links {
            text-align: center;
            margin-bottom: 20px;
        }
        .nav-links a {
            color: #4CAF50;
            text-decoration: none;
            margin: 0 15px;
            padding: 8px 20px;
            border-radius: 25px;
            background: rgba(0,0,0,0.3);
        }
        .nav-links a:hover { background: #4CAF50; color: white; }
        
        .stats-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-card h3 { font-size: 2.5em; color: #4CAF50; }
        .stat-card p { color: #aaa; margin-top: 5px; }
        
        .charts-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        .chart-card {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 20px;
        }
        .chart-card h3 { margin-bottom: 15px; color: #4CAF50; text-align: center; }
        canvas { max-height: 300px; width: 100% !important; }
        
        .search-section, .compare-section, .ranking-section {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
        }
        .search-box {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        .search-box input {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            background: rgba(255,255,255,0.1);
            color: white;
        }
        .search-box input::placeholder { color: #888; }
        .search-box button, .compare-btn {
            padding: 12px 30px;
            background: #4CAF50;
            border: none;
            border-radius: 25px;
            color: white;
            cursor: pointer;
        }
        .compare-btn { background: #2196F3; }
        
        .results {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
            display: none;
            overflow-x: auto;
        }
        .compare-selects {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            margin-top: 15px;
        }
        .compare-selects select {
            flex: 1;
            padding: 12px;
            border-radius: 10px;
            background: rgba(255,255,255,0.1);
            color: white;
            border: 1px solid #4CAF50;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th { background: #4CAF50; }
        tr:hover { background: rgba(255,255,255,0.05); }
        .ver-btn {
            background: #FF9800;
            border: none;
            padding: 5px 15px;
            border-radius: 20px;
            cursor: pointer;
            color: white;
        }
        .close-btn {
            background: #f44336;
            border: none;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            color: white;
            margin-bottom: 15px;
        }
        
        @media (max-width: 768px) {
            .charts-section { grid-template-columns: 1fr; }
            h1 { font-size: 1.8em; }
            .container { padding: 10px; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="nav-links">
        <a href="/">🏆 Ranking</a>
        <a href="/jugador">🔍 Buscar Jugador</a>
    </div>
    
    <h1>🏆 Mundial 2026</h1>
    <div class="subtitle">Análisis estadístico y pronósticos de las selecciones clasificadas</div>
    
    <div class="stats-cards">
        <div class="stat-card"><h3>{{ total_selecciones }}</h3><p>Selecciones</p></div>
        <div class="stat-card"><h3>{{ total_jugadores }}</h3><p>Jugadores</p></div>
        <div class="stat-card"><h3>🔮</h3><p>Pronósticos</p></div>
        <div class="stat-card"><h3>☁️</h3><p>MongoDB Atlas</p></div>
    </div>
    
    <div class="charts-section">
        <div class="chart-card"><h3>⭐ Top 10 - Rating Promedio</h3><canvas id="rankingChart"></canvas></div>
        <div class="chart-card"><h3>⚽ Top 10 - Goles Totales</h3><canvas id="golesChart"></canvas></div>
    </div>
    
    <div class="search-section">
        <h3>🔍 Buscar Jugador en Selecciones</h3>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Ej: Messi, Mbappé, Haaland...">
            <button onclick="buscarJugadorEnSelecciones()">Buscar</button>
        </div>
        <div id="resultadosBusqueda" class="results"></div>
    </div>
    
    <div class="compare-section">
        <h3>⚔️ Comparar Selecciones</h3>
        <div class="compare-selects">
            <select id="equipo1">
                <option value="">Selecciona equipo 1</option>
                {% for s in selecciones %}
                <option value="{{ s.nombre }}">{{ s.nombre }}</option>
                {% endfor %}
            </select>
            <span>VS</span>
            <select id="equipo2">
                <option value="">Selecciona equipo 2</option>
                {% for s in selecciones %}
                <option value="{{ s.nombre }}">{{ s.nombre }}</option>
                {% endfor %}
            </select>
            <button class="compare-btn" onclick="compararSelecciones()">Comparar</button>
        </div>
        <div id="comparacionResultado" class="results"></div>
    </div>
    
    <div class="ranking-section">
        <h3>📊 Ranking de Selecciones</h3>
        <table><thead><tr><th>#</th><th>Selección</th><th>Jugadores</th><th>Goles</th><th>Rating</th><th>Acción</th></tr></thead><tbody>
        {% for s in selecciones %}
        <tr>
            <td>{{ loop.index }}</td>
            <td><strong>{{ s.nombre }}</strong></td>
            <td>{{ s.jugadores }}</td>
            <td>{{ s.goles_total }}</td>
            <td>{{ s.rating_promedio }}</td>
            <td><button class="ver-btn" onclick="verSeleccion('{{ s.nombre }}')">Ver</button></td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
    </div>
</div>

<script>
    let rankingChart = null;
    let golesChart = null;
    
    function buscarJugadorEnSelecciones() {
        let termino = document.getElementById('searchInput').value;
        if (termino.length < 2) { alert("Mínimo 2 caracteres"); return; }
        fetch('/api/buscar?q=' + encodeURIComponent(termino))
            .then(r => r.json())
            .then(data => {
                let div = document.getElementById('resultadosBusqueda');
                if (data.length === 0) {
                    div.innerHTML = '<p>❌ No se encontraron jugadores con "' + termino + '"</p>';
                } else {
                    let html = '<button class="close-btn" onclick="cerrarBusqueda()">Cerrar</button>';
                    html += '<h3>✅ Resultados (' + data.length + ')</h3><tr><thead><tr><th>Jugador</th><th>Selección</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>';
                    for (let j of data) {
                        html += '<tr><td><strong>' + j.jugador + '</strong></td><td>' + j.seleccion + '</td><td>' + j.goles + '</td><td>' + j.asistencias + '</td><td>' + j.rating + '</td></tr>';
                    }
                    html += '</tbody></table>';
                    div.innerHTML = html;
                }
                div.style.display = 'block';
            });
    }
    
    function cerrarBusqueda() { document.getElementById('resultadosBusqueda').style.display = 'none'; }
    function cerrarComparacion() { document.getElementById('comparacionResultado').style.display = 'none'; }
    
    function verSeleccion(nombre) {
        fetch('/api/seleccion/' + encodeURIComponent(nombre))
            .then(r => r.json())
            .then(data => {
                let html = '<button class="close-btn" onclick="cerrarComparacion()">Cerrar</button>';
                html += '<h2>🏆 ' + data.nombre + '</h2>';
                html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:20px 0;">';
                html += '<div style="background:#1a1a2e;padding:15px;border-radius:10px;text-align:center"><h3>' + data.jugadores + '</h3><p>Jugadores</p></div>';
                html += '<div style="background:#1a1a2e;padding:15px;border-radius:10px;text-align:center"><h3>' + data.goles_total + '</h3><p>Goles</p></div>';
                html += '<div style="background:#1a1a2e;padding:15px;border-radius:10px;text-align:center"><h3>' + data.asistencias_total + '</h3><p>Asistencias</p></div>';
                html += '<div style="background:#1a1a2e;padding:15px;border-radius:10px;text-align:center"><h3>' + data.rating_promedio + '</h3><p>Rating</p></div></div>';
                html += '<h3>📋 Plantilla</h3><div style="overflow-x:auto;"><table><thead><tr><th>Jugador</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>';
                for (let j of data.plantilla) {
                    html += '<tr><td>' + j.jugador + '</td><td>' + j.goles + '</td><td>' + j.asistencias + '</td><td>' + j.rating + '</td></tr>';
                }
                html += '</tbody></table></div>';
                document.getElementById('comparacionResultado').innerHTML = html;
                document.getElementById('comparacionResultado').style.display = 'block';
            });
    }
    
    function compararSelecciones() {
        let eq1 = document.getElementById('equipo1').value;
        let eq2 = document.getElementById('equipo2').value;
        if (!eq1 || !eq2) { alert("Selecciona dos equipos"); return; }
        if (eq1 === eq2) { alert("Selecciona equipos diferentes"); return; }
        fetch('/api/comparar?eq1=' + encodeURIComponent(eq1) + '&eq2=' + encodeURIComponent(eq2))
            .then(r => r.json())
            .then(data => {
                let html = '<button class="close-btn" onclick="cerrarComparacion()">Cerrar</button>';
                html += '<div style="display:grid;grid-template-columns:1fr auto 1fr;gap:20px;">';
                html += '<div style="background:#1a1a2e;padding:20px;border-radius:15px;"><h3 style="text-align:center;color:#4CAF50">' + data.equipo1.nombre + '</h3>';
                html += '<div><strong>🏆 Rating:</strong> ' + data.equipo1.rating_promedio + '</div>';
                html += '<div><strong>⚽ Goles:</strong> ' + data.equipo1.goles_total + '</div>';
                html += '<div><strong>⭐ Mejor:</strong> ' + data.equipo1.mejor_rating.nombre + ' (' + data.equipo1.mejor_rating.valor + ')</div>';
                html += '</div><div style="font-size:36px;display:flex;align-items:center;">VS</div>';
                html += '<div style="background:#1a1a2e;padding:20px;border-radius:15px;"><h3 style="text-align:center;color:#4CAF50">' + data.equipo2.nombre + '</h3>';
                html += '<div><strong>🏆 Rating:</strong> ' + data.equipo2.rating_promedio + '</div>';
                html += '<div><strong>⚽ Goles:</strong> ' + data.equipo2.goles_total + '</div>';
                html += '<div><strong>⭐ Mejor:</strong> ' + data.equipo2.mejor_rating.nombre + ' (' + data.equipo2.mejor_rating.valor + ')</div></div></div>';
                document.getElementById('comparacionResultado').innerHTML = html;
                document.getElementById('comparacionResultado').style.display = 'block';
            });
    }
    
    function cargarGraficos() {
        fetch('/api/selecciones')
            .then(r => r.json())
            .then(data => {
                let topRating = [...data].sort((a,b) => b.rating_promedio - a.rating_promedio).slice(0, 10);
                let ctxRanking = document.getElementById('rankingChart').getContext('2d');
                if (rankingChart) rankingChart.destroy();
                rankingChart = new Chart(ctxRanking, {
                    type: 'bar',
                    data: { labels: topRating.map(t => t.nombre), datasets: [{ label: 'Rating Promedio', data: topRating.map(t => t.rating_promedio), backgroundColor: 'rgba(76,175,80,0.7)', borderRadius: 10 }] },
                    options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: 'white' } } }, scales: { y: { ticks: { color: 'white' } }, x: { ticks: { color: 'white', rotation: 45 } } } }
                });
                let topGoles = [...data].sort((a,b) => b.goles_total - a.goles_total).slice(0, 10);
                let ctxGoles = document.getElementById('golesChart').getContext('2d');
                if (golesChart) golesChart.destroy();
                golesChart = new Chart(ctxGoles, {
                    type: 'bar',
                    data: { labels: topGoles.map(t => t.nombre), datasets: [{ label: 'Goles Totales', data: topGoles.map(t => t.goles_total), backgroundColor: 'rgba(33,150,243,0.7)', borderRadius: 10 }] },
                    options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: 'white' } } }, scales: { y: { ticks: { color: 'white' } }, x: { ticks: { color: 'white', rotation: 45 } } } }
                });
            });
    }
    
    window.onload = cargarGraficos;
</script>
</body>
</html>
"""

# ==================== PÁGINA DE JUGADORES ====================
JUGADOR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Buscador de Jugadores - Mundial 2026</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; color: #4CAF50; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #aaa; margin-bottom: 30px; }
        
        .nav-links {
            text-align: center;
            margin-bottom: 20px;
        }
        .nav-links a {
            color: #4CAF50;
            text-decoration: none;
            margin: 0 15px;
            padding: 8px 20px;
            border-radius: 25px;
            background: rgba(0,0,0,0.3);
        }
        
        .search-section, .compare-section {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .search-box input {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            background: rgba(255,255,255,0.1);
            color: white;
        }
        .search-box button, .compare-btn {
            padding: 12px 30px;
            background: #4CAF50;
            border: none;
            border-radius: 25px;
            color: white;
            cursor: pointer;
        }
        .compare-btn { background: #2196F3; }
        
        .results {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
            display: none;
        }
        .compare-selects {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            margin-top: 15px;
        }
        .compare-selects input {
            flex: 1;
            padding: 12px;
            border-radius: 25px;
            border: none;
            background: rgba(255,255,255,0.1);
            color: white;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 15px;
        }
        .stat-card {
            background: #0f3460;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-card h3 { font-size: 2em; color: #4CAF50; }
        .comparacion-grid {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        .comparacion-equipo {
            background: #1a1a2e;
            padding: 15px;
            border-radius: 10px;
        }
        .comparacion-equipo h3 { text-align: center; color: #4CAF50; }
        .vs { font-size: 36px; display: flex; align-items: center; color: #FFC107; }
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #333;
        }
        .close-btn {
            background: #f44336;
            border: none;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            color: white;
            margin-bottom: 15px;
        }
        @media (max-width: 768px) {
            .comparacion-grid { grid-template-columns: 1fr; }
            .vs { text-align: center; padding: 10px 0; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="nav-links">
        <a href="/">🏆 Ranking</a>
        <a href="/jugador">🔍 Buscar Jugador</a>
    </div>
    
    <h1>🔍 Buscador de Jugadores</h1>
    <div class="subtitle">Estadísticas actualizadas 2025-2026</div>
    
    <div class="search-section">
        <h3>🔍 Buscar Jugador</h3>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Ej: Messi, Ronaldo, Mbappé...">
            <button onclick="buscarJugador()">Buscar</button>
        </div>
        <div id="resultadoBusqueda" class="results"></div>
    </div>
    
    <div class="compare-section">
        <h3>⚔️ Comparar Jugadores</h3>
        <div class="compare-selects">
            <input type="text" id="jugador1" placeholder="Primer jugador">
            <span>VS</span>
            <input type="text" id="jugador2" placeholder="Segundo jugador">
            <button class="compare-btn" onclick="compararJugadores()">Comparar</button>
        </div>
        <div id="comparacionResultado" class="results"></div>
    </div>
</div>

<script>
    function buscarJugador() {
        let nombre = document.getElementById('searchInput').value;
        if (nombre.length < 2) { alert("Mínimo 2 caracteres"); return; }
        
        fetch('/api/jugador/buscar?nombre=' + encodeURIComponent(nombre))
            .then(r => r.json())
            .then(data => {
                let div = document.getElementById('resultadoBusqueda');
                if (data.error) {
                    div.innerHTML = '<p>❌ ' + data.error + '</p>';
                } else {
                    let html = '<button class="close-btn" onclick="cerrarBusqueda()">Cerrar</button>';
                    html += '<h3>' + data.player + '</h3>';
                    html += '<div class="stats-grid">';
                    html += '<div class="stat-card"><h3>' + data.goals + '</h3><p>Goles</p></div>';
                    html += '<div class="stat-card"><h3>' + data.assists + '</h3><p>Asistencias</p></div>';
                    html += '<div class="stat-card"><h3>' + data.rating + '</h3><p>Rating</p></div>';
                    html += '<div class="stat-card"><h3>' + data.totalShots + '</h3><p>Tiros</p></div>';
                    html += '<div class="stat-card"><h3>' + data.shotsOnTarget + '</h3><p>Tiros a puerta</p></div>';
                    html += '<div class="stat-card"><h3>' + data.keyPasses + '</h3><p>Pases clave</p></div>';
                    html += '</div>';
                    html += '<p><strong>Equipo:</strong> ' + data.team + ' (' + data.league + ')</p>';
                    if (data.nota) html += '<p><strong>📌 Nota:</strong> ' + data.nota + '</p>';
                    div.innerHTML = html;
                }
                div.style.display = 'block';
            });
    }
    
    function compararJugadores() {
        let j1 = document.getElementById('jugador1').value;
        let j2 = document.getElementById('jugador2').value;
        if (!j1 || !j2) { alert("Ingresa dos jugadores"); return; }
        
        fetch('/api/jugador/comparar?j1=' + encodeURIComponent(j1) + '&j2=' + encodeURIComponent(j2))
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    return;
                }
                
                let html = '<button class="close-btn" onclick="cerrarComparacion()">Cerrar</button>';
                html += '<div class="comparacion-grid">';
                
                html += '<div class="comparacion-equipo">';
                html += '<h3>' + data.jugador1.nombre + '</h3>';
                html += '<p><small>' + data.jugador1.equipo + ' (' + data.jugador1.liga + ')</small></p>';
                html += '<div class="stat-row"><span>⚽ Goles</span><span>' + getValor(data.comparacion, 'goals', 1) + '</span></div>';
                html += '<div class="stat-row"><span>🎯 Asistencias</span><span>' + getValor(data.comparacion, 'assists', 1) + '</span></div>';
                html += '<div class="stat-row"><span>⭐ Rating</span><span>' + getValor(data.comparacion, 'rating', 1) + '</span></div>';
                html += '<div class="stat-row"><span>🎯 Tiros</span><span>' + getValor(data.comparacion, 'totalShots', 1) + '</span></div>';
                html += '<div class="stat-row"><span>🎯 Tiros a puerta</span><span>' + getValor(data.comparacion, 'shotsOnTarget', 1) + '</span></div>';
                html += '<div class="stat-row"><span>🔑 Pases clave</span><span>' + getValor(data.comparacion, 'keyPasses', 1) + '</span></div>';
                html += '</div>';
                
                html += '<div class="vs">VS</div>';
                
                html += '<div class="comparacion-equipo">';
                html += '<h3>' + data.jugador2.nombre + '</h3>';
                html += '<p><small>' + data.jugador2.equipo + ' (' + data.jugador2.liga + ')</small></p>';
                html += '<div class="stat-row"><span>⚽ Goles</span><span>' + getValor(data.comparacion, 'goals', 2) + '</span></div>';
                html += '<div class="stat-row"><span>🎯 Asistencias</span><span>' + getValor(data.comparacion, 'assists', 2) + '</span></div>';
                html += '<div class="stat-row"><span>⭐ Rating</span><span>' + getValor(data.comparacion, 'rating', 2) + '</span></div>';
                html += '<div class="stat-row"><span>🎯 Tiros</span><span>' + getValor(data.comparacion, 'totalShots', 2) + '</span></div>';
                html += '<div class="stat-row"><span>🎯 Tiros a puerta</span><span>' + getValor(data.comparacion, 'shotsOnTarget', 2) + '</span></div>';
                html += '<div class="stat-row"><span>🔑 Pases clave</span><span>' + getValor(data.comparacion, 'keyPasses', 2) + '</span></div>';
                html += '</div>';
                
                html += '</div>';
                document.getElementById('comparacionResultado').innerHTML = html;
                document.getElementById('comparacionResultado').style.display = 'block';
            });
    }
    
    function getValor(comparacion, stat, jugador) {
        let item = comparacion.find(c => c.stat === stat);
        if (!item) return 'N/A';
        return jugador === 1 ? item.valor1 : item.valor2;
    }
    
    function cerrarBusqueda() { document.getElementById('resultadoBusqueda').style.display = 'none'; }
    function cerrarComparacion() { document.getElementById('comparacionResultado').style.display = 'none'; }
</script>
</body>
</html>
"""

# ==================== FUNCIONES DE SELECCIONES ====================
def obtener_selecciones():
    if coleccion is None: return []
    return list(coleccion.find({}, {'_id': 0}))

def obtener_seleccion(nombre):
    if coleccion is None: return None
    return coleccion.find_one({'nombre': nombre}, {'_id': 0})

def buscar_jugadores(termino):
    if coleccion is None: return []
    resultados = []
    for sel in coleccion.find({}, {'_id': 0}):
        for jug in sel.get('plantilla', []):
            if termino.lower() in jug.get('jugador', '').lower():
                resultados.append({
                    'seleccion': sel['nombre'],
                    'jugador': jug['jugador'],
                    'goles': jug['goles'],
                    'asistencias': jug['asistencias'],
                    'rating': jug['rating']
                })
    return resultados

def buscar_jugador_local(nombre_jugador):
    nombre_limpio = nombre_jugador.lower().strip()
    for key, data in JUGADORES_MANUALES.items():
        if key in nombre_limpio or nombre_limpio in key:
            return data
    return None

# ==================== RUTAS ====================
@app.route('/')
def index():
    selecciones = obtener_selecciones()
    total_jugadores = sum(s.get('jugadores', 0) for s in selecciones)
    return render_template_string(INDEX_HTML, selecciones=selecciones, 
                                  total_selecciones=len(selecciones), 
                                  total_jugadores=total_jugadores)

@app.route('/jugador')
def pagina_jugador():
    return render_template_string(JUGADOR_HTML)

@app.route('/api/selecciones')
def api_selecciones():
    return jsonify(obtener_selecciones())

@app.route('/api/seleccion/<nombre>')
def api_seleccion(nombre):
    sel = obtener_seleccion(nombre)
    if not sel:
        return jsonify({'error': 'No encontrada'}), 404
    mejor = max(sel['plantilla'], key=lambda x: x['rating'])
    goleador = max(sel['plantilla'], key=lambda x: x['goles'])
    return jsonify({
        'nombre': sel['nombre'],
        'jugadores': sel['jugadores'],
        'goles_total': sel['goles_total'],
        'asistencias_total': sel['asistencias_total'],
        'rating_promedio': sel['rating_promedio'],
        'plantilla': sel['plantilla'],
        'mejor_rating': {'nombre': mejor['jugador'], 'valor': mejor['rating']},
        'max_goleador': {'nombre': goleador['jugador'], 'goles': goleador['goles']}
    })

@app.route('/api/buscar')
def api_buscar():
    termino = request.args.get('q', '')
    if len(termino) < 2:
        return jsonify([])
    return jsonify(buscar_jugadores(termino))

@app.route('/api/comparar')
def api_comparar():
    eq1 = request.args.get('eq1', '')
    eq2 = request.args.get('eq2', '')
    d1 = obtener_seleccion(eq1)
    d2 = obtener_seleccion(eq2)
    if not d1 or not d2:
        return jsonify({'error': 'Equipo no encontrado'}), 404
    mejor1 = max(d1['plantilla'], key=lambda x: x['rating'])
    mejor2 = max(d2['plantilla'], key=lambda x: x['rating'])
    gol1 = max(d1['plantilla'], key=lambda x: x['goles'])
    gol2 = max(d2['plantilla'], key=lambda x: x['goles'])
    return jsonify({
        'equipo1': {
            'nombre': d1['nombre'],
            'jugadores': d1['jugadores'],
            'goles_total': d1['goles_total'],
            'asistencias_total': d1['asistencias_total'],
            'rating_promedio': d1['rating_promedio'],
            'mejor_rating': {'nombre': mejor1['jugador'], 'valor': mejor1['rating']},
            'max_goleador': {'nombre': gol1['jugador'], 'goles': gol1['goles']}
        },
        'equipo2': {
            'nombre': d2['nombre'],
            'jugadores': d2['jugadores'],
            'goles_total': d2['goles_total'],
            'asistencias_total': d2['asistencias_total'],
            'rating_promedio': d2['rating_promedio'],
            'mejor_rating': {'nombre': mejor2['jugador'], 'valor': mejor2['rating']},
            'max_goleador': {'nombre': gol2['jugador'], 'goles': gol2['goles']}
        }
    })

@app.route('/api/jugador/buscar')
def api_buscar_jugador():
    nombre = request.args.get('nombre', '')
    if not nombre:
        return jsonify({'error': 'Nombre requerido'}), 400
    jugador = buscar_jugador_local(nombre)
    if jugador:
        return jsonify(jugador)
    return jsonify({'error': 'Jugador no encontrado'}), 404

@app.route('/api/jugador/comparar')
def api_comparar_jugadores():
    jugador1 = request.args.get('j1', '')
    jugador2 = request.args.get('j2', '')
    if not jugador1 or not jugador2:
        return jsonify({'error': 'Se necesitan dos jugadores'}), 400
    j1 = buscar_jugador_local(jugador1)
    j2 = buscar_jugador_local(jugador2)
    if not j1:
        return jsonify({'error': f'Jugador "{jugador1}" no encontrado'}), 404
    if not j2:
        return jsonify({'error': f'Jugador "{jugador2}" no encontrado'}), 404
    
    stats = ['goals', 'assists', 'rating', 'totalShots', 'shotsOnTarget', 
             'keyPasses', 'successfulDribbles', 'tackles', 'interceptions',
             'accuratePassesPercentage', 'expectedGoals', 'expectedAssists']
    
    comparacion = []
    for stat in stats:
        val1 = j1.get(stat, 0)
        val2 = j2.get(stat, 0)
        comparacion.append({
            'stat': stat,
            'nombre': stat.replace('_', ' ').title(),
            'valor1': val1,
            'valor2': val2,
            'ganador': 1 if val1 > val2 else (2 if val2 > val1 else 0)
        })
    
    return jsonify({
        'jugador1': {'nombre': j1['player'], 'equipo': j1['team'], 'liga': j1['league']},
        'jugador2': {'nombre': j2['player'], 'equipo': j2['team'], 'liga': j2['league']},
        'comparacion': comparacion
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)