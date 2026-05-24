import os
import requests
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
from datetime import datetime

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

# ==================== JUGADORES MANUALES ====================
JUGADORES_MANUALES = {
    "messi": {
        "player": "Lionel Messi", "team": "Inter Miami", "league": "MLS",
        "goals": 12, "assists": 8, "rating": 8.2, "totalShots": 48, "shotsOnTarget": 28,
        "keyPasses": 45, "successfulDribbles": 62
    },
    "cristiano ronaldo": {
        "player": "Cristiano Ronaldo", "team": "Al Nassr", "league": "Saudi Pro League",
        "goals": 28, "assists": 6, "rating": 7.9, "totalShots": 98, "shotsOnTarget": 52,
        "keyPasses": 32, "successfulDribbles": 28
    }
}

# ==================== CUOTAS ====================
ODDS_API_KEY = "1928777e3a71509cabffaf3c507876ce"

def obtener_cuotas():
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds"
    params = {"apiKey": ODDS_API_KEY, "regions": "us,uk,eu", "markets": "h2h", "oddsFormat": "decimal"}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

# ==================== FUNCIONES ====================
def obtener_selecciones():
    if coleccion is None: return []
    return list(coleccion.find({}, {'_id': 0}))

def obtener_seleccion(nombre):
    if coleccion is None: return None
    return coleccion.find_one({'nombre': nombre}, {'_id': 0})

def buscar_jugador_local(nombre):
    nombre_limpio = nombre.lower().strip()
    for key, data in JUGADORES_MANUALES.items():
        if key in nombre_limpio or nombre_limpio in key:
            return data
    return None

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
            background: #1a1a2e;
            color: white;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; color: #4CAF50; margin-bottom: 10px; }
        h2 { margin: 20px 0 10px; color: #4CAF50; font-size: 1.5em; }
        .nav {
            text-align: center;
            margin-bottom: 20px;
        }
        .nav a {
            color: #4CAF50;
            text-decoration: none;
            margin: 0 15px;
            padding: 8px 20px;
            background: #0f3460;
            border-radius: 25px;
        }
        .stats-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .card {
            background: #0f3460;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .card h3 { font-size: 2em; color: #4CAF50; }
        .charts {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .chart-box {
            background: #0f3460;
            padding: 15px;
            border-radius: 10px;
        }
        canvas { max-height: 250px; width: 100% !important; }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #0f3460;
            border-radius: 10px;
            overflow: hidden;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #1a1a2e;
        }
        th { background: #4CAF50; }
        tr:hover { background: #1a2a4e; }
        button, .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
        }
        .btn-blue { background: #2196F3; }
        .btn-orange { background: #FF9800; }
        input, select {
            padding: 8px 15px;
            border-radius: 20px;
            border: none;
            background: #0f3460;
            color: white;
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin: 15px 0;
            flex-wrap: wrap;
        }
        .results {
            background: #0f3460;
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            display: none;
        }
        .odds-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .odds-item {
            background: #1a1a2e;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
        }
        .odds-value { font-size: 1.5em; font-weight: bold; color: #FFC107; }
        .pronostico-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 15px 0;
        }
        .pronostico-item {
            background: #1a1a2e;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .pronostico-item .prob { font-size: 2em; font-weight: bold; color: #FFC107; }
        .recomendacion {
            background: #1a1a2e;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-top: 15px;
        }
        @media (max-width: 600px) {
            .pronostico-grid { grid-template-columns: 1fr; }
            .charts { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <a href="/">🏆 Ranking</a>
        <a href="/jugador">🔍 Jugadores</a>
    </div>
    
    <h1>🏆 Mundial 2026</h1>
    <p style="text-align:center">Análisis estadístico y cuotas en tiempo real</p>
    
    <div class="stats-cards">
        <div class="card"><h3>{{ total_selecciones }}</h3><p>Selecciones</p></div>
        <div class="card"><h3>{{ total_jugadores }}</h3><p>Jugadores</p></div>
        <div class="card"><h3>📊</h3><p>Pronósticos</p></div>
        <div class="card"><h3>⚽</h3><p>Cuotas TR</p></div>
    </div>
    
    <!-- Gráficos -->
    <div class="charts">
        <div class="chart-box"><h3>⭐ Rating Promedio</h3><canvas id="ratingChart"></canvas></div>
        <div class="chart-box"><h3>⚽ Goles Totales</h3><canvas id="golesChart"></canvas></div>
    </div>
    
    <!-- Pronóstico -->
    <h2>🔮 Pronóstico de Partido</h2>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px;">
        <select id="eqLocal">
            <option value="">Local</option>
            {% for s in selecciones %}<option value="{{ s.nombre }}">{{ s.nombre }}</option>{% endfor %}
        </select>
        <span>VS</span>
        <select id="eqVisitante">
            <option value="">Visitante</option>
            {% for s in selecciones %}<option value="{{ s.nombre }}">{{ s.nombre }}</option>{% endfor %}
        </select>
        <button class="btn-orange" onclick="calcularPronostico()">🔮 Calcular</button>
    </div>
    <div id="pronosticoResultado" style="display:none;"></div>
    
    <!-- Cuotas -->
    <h2>📊 Cuotas en Tiempo Real</h2>
    <button class="btn-blue" onclick="cargarCuotas()">🔄 Actualizar Cuotas</button>
    <div id="cuotasResultado" style="margin-top: 15px;"></div>
    
    <!-- Ranking -->
    <h2>📋 Ranking de Selecciones</h2>
    <table><thead><tr><th>#</th><th>Selección</th><th>Jugadores</th><th>Goles</th><th>Rating</th></tr></thead><tbody>
    {% for s in selecciones %}
    <tr><td>{{ loop.index }}</td><td><strong>{{ s.nombre }}</strong></td><td>{{ s.jugadores }}</td><td>{{ s.goles_total }}</td><td>{{ s.rating_promedio }}</td></tr>
    {% endfor %}
    </tbody></table>
</div>

<script>
    let ratingChart, golesChart;
    
    function cargarGraficos() {
        fetch('/api/selecciones')
            .then(r => r.json())
            .then(data => {
                let topRating = [...data].sort((a,b) => b.rating_promedio - a.rating_promedio).slice(0, 10);
                let ctx1 = document.getElementById('ratingChart').getContext('2d');
                if (ratingChart) ratingChart.destroy();
                ratingChart = new Chart(ctx1, {
                    type: 'bar',
                    data: { labels: topRating.map(t => t.nombre), datasets: [{ label: 'Rating', data: topRating.map(t => t.rating_promedio), backgroundColor: 'rgba(76,175,80,0.7)' }] },
                    options: { responsive: true }
                });
                
                let topGoles = [...data].sort((a,b) => b.goles_total - a.goles_total).slice(0, 10);
                let ctx2 = document.getElementById('golesChart').getContext('2d');
                if (golesChart) golesChart.destroy();
                golesChart = new Chart(ctx2, {
                    type: 'bar',
                    data: { labels: topGoles.map(t => t.nombre), datasets: [{ label: 'Goles', data: topGoles.map(t => t.goles_total), backgroundColor: 'rgba(33,150,243,0.7)' }] },
                    options: { responsive: true }
                });
            });
    }
    
    function cargarCuotas() {
        let div = document.getElementById('cuotasResultado');
        div.innerHTML = '<p>Cargando...</p>';
        fetch('/api/odds')
            .then(r => r.json())
            .then(data => {
                if (!data.success || data.games.length === 0) {
                    div.innerHTML = '<p>No hay partidos disponibles</p>';
                    return;
                }
                let html = '<div style="max-height:400px;overflow-y:auto;">';
                for (let g of data.games.slice(0, 10)) {
                    html += '<div style="background:#0f3460;margin-bottom:10px;padding:15px;border-radius:10px;">';
                    html += '<strong>' + g.home_team + ' 🆚 ' + g.away_team + '</strong>';
                    html += '<div class="odds-grid">';
                    html += '<div class="odds-item"><div>🏠 Local</div><div class="odds-value">' + (g.cuotas.home > 0 ? g.cuotas.home.toFixed(2) : 'N/A') + '</div><small>' + g.mejores_casas.home + '</small></div>';
                    html += '<div class="odds-item"><div>🤝 Empate</div><div class="odds-value">' + (g.cuotas.draw > 0 ? g.cuotas.draw.toFixed(2) : 'N/A') + '</div><small>' + g.mejores_casas.draw + '</small></div>';
                    html += '<div class="odds-item"><div>✈️ Visitante</div><div class="odds-value">' + (g.cuotas.away > 0 ? g.cuotas.away.toFixed(2) : 'N/A') + '</div><small>' + g.mejores_casas.away + '</small></div>';
                    html += '</div></div>';
                }
                html += '</div>';
                div.innerHTML = html;
            })
            .catch(e => div.innerHTML = '<p>Error: ' + e.message + '</p>');
    }
    
    function calcularPronostico() {
        let local = document.getElementById('eqLocal').value;
        let visitante = document.getElementById('eqVisitante').value;
        if (!local || !visitante) { alert("Selecciona ambos equipos"); return; }
        if (local === visitante) { alert("Equipos diferentes"); return; }
        
        let div = document.getElementById('pronosticoResultado');
        div.innerHTML = '<p>Calculando...</p>';
        div.style.display = 'block';
        
        fetch('/api/pronostico?local=' + encodeURIComponent(local) + '&visitante=' + encodeURIComponent(visitante))
            .then(r => r.json())
            .then(data => {
                let html = '<div class="pronostico-grid">';
                html += '<div class="pronostico-item"><div class="prob">' + data.local.probabilidad + '%</div><div>🏠 ' + data.local.nombre + '</div></div>';
                html += '<div class="pronostico-item"><div class="prob">' + data.empate.probabilidad + '%</div><div>🤝 Empate</div></div>';
                html += '<div class="pronostico-item"><div class="prob">' + data.visitante.probabilidad + '%</div><div>✈️ ' + data.visitante.nombre + '</div></div>';
                html += '</div><div class="recomendacion">' + data.recomendacion + '</div>';
                div.innerHTML = html;
            })
            .catch(e => div.innerHTML = '<p>Error: ' + e.message + '</p>');
    }
    
    cargarGraficos();
    setTimeout(cargarCuotas, 500);
</script>
</body>
</html>
"""

# ==================== PÁGINA DE JUGADORES ====================
HTML_JUGADOR = """
<!DOCTYPE html>
<html>
<head>
    <title>Buscador de Jugadores</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #1a1a2e;
            color: white;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { text-align: center; color: #4CAF50; margin-bottom: 20px; }
        .nav { text-align: center; margin-bottom: 20px; }
        .nav a { color: #4CAF50; text-decoration: none; margin: 0 15px; padding: 8px 20px; background: #0f3460; border-radius: 25px; }
        input, button {
            padding: 10px 20px;
            border-radius: 25px;
            border: none;
        }
        input { background: #0f3460; color: white; flex: 1; }
        button { background: #4CAF50; color: white; cursor: pointer; }
        .search-box { display: flex; gap: 10px; margin: 20px 0; }
        .results { background: #0f3460; border-radius: 10px; padding: 20px; margin-top: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 15px 0; }
        .stat-card { background: #1a1a2e; padding: 15px; border-radius: 10px; text-align: center; }
        .stat-card h3 { font-size: 2em; color: #4CAF50; }
        .close-btn { background: #f44336; padding: 5px 15px; font-size: 12px; margin-bottom: 15px; }
    </style>
</head>
<body>
<div class="container">
    <div class="nav">
        <a href="/">🏆 Ranking</a>
        <a href="/jugador">🔍 Jugadores</a>
    </div>
    <h1>🔍 Buscador de Jugadores</h1>
    
    <div class="search-box">
        <input type="text" id="searchInput" placeholder="Ej: Messi, Ronaldo...">
        <button onclick="buscarJugador()">Buscar</button>
    </div>
    <div id="resultado" class="results" style="display:none;"></div>
</div>
<script>
    function buscarJugador() {
        let nombre = document.getElementById('searchInput').value;
        if (nombre.length < 2) { alert("Mínimo 2 caracteres"); return; }
        fetch('/api/jugador/buscar?nombre=' + encodeURIComponent(nombre))
            .then(r => r.json())
            .then(data => {
                let div = document.getElementById('resultado');
                if (data.error) { div.innerHTML = '<p>❌ ' + data.error + '</p>'; }
                else {
                    let html = '<button class="close-btn" onclick="cerrar()">Cerrar</button>';
                    html += '<h3>' + data.player + '</h3>';
                    html += '<div class="stats-grid">';
                    html += '<div class="stat-card"><h3>' + data.goals + '</h3><p>Goles</p></div>';
                    html += '<div class="stat-card"><h3>' + data.assists + '</h3><p>Asistencias</p></div>';
                    html += '<div class="stat-card"><h3>' + data.rating + '</h3><p>Rating</p></div>';
                    html += '</div><p><strong>Equipo:</strong> ' + data.team + ' (' + data.league + ')</p>';
                    div.innerHTML = html;
                }
                div.style.display = 'block';
            });
    }
    function cerrar() { document.getElementById('resultado').style.display = 'none'; }
</script>
</body>
</html>
"""

# ==================== RUTAS ====================
@app.route('/')
def index():
    selecciones = obtener_selecciones()
    total_jugadores = sum(s.get('jugadores', 0) for s in selecciones)
    return render_template_string(HTML, selecciones=selecciones, 
                                  total_selecciones=len(selecciones), 
                                  total_jugadores=total_jugadores)

@app.route('/jugador')
def jugador():
    return render_template_string(HTML_JUGADOR)

@app.route('/api/selecciones')
def api_selecciones():
    return jsonify(obtener_selecciones())

@app.route('/api/odds')
def api_odds():
    data = obtener_cuotas()
    if not data:
        return jsonify({'success': False, 'error': 'No se pudieron obtener las cuotas'}), 500
    
    partidos = []
    for partido in data:
        cuotas = {'home': 0, 'draw': 0, 'away': 0}
        mejores_casas = {'home': '', 'draw': '', 'away': ''}
        for bookmaker in partido.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market.get('key') == 'h2h':
                    for outcome in market.get('outcomes', []):
                        nombre = outcome.get('name', '')
                        precio = outcome.get('price', 0)
                        if nombre == partido.get('home_team'):
                            if precio > cuotas['home']:
                                cuotas['home'] = precio
                                mejores_casas['home'] = bookmaker.get('title', '')
                        elif nombre == 'Draw':
                            if precio > cuotas['draw']:
                                cuotas['draw'] = precio
                                mejores_casas['draw'] = bookmaker.get('title', '')
                        else:
                            if precio > cuotas['away']:
                                cuotas['away'] = precio
                                mejores_casas['away'] = bookmaker.get('title', '')
        partidos.append({
            'home_team': partido.get('home_team'),
            'away_team': partido.get('away_team'),
            'cuotas': cuotas,
            'mejores_casas': mejores_casas
        })
    return jsonify({'success': True, 'games': partidos, 'count': len(partidos)})

@app.route('/api/pronostico')
def api_pronostico():
    local = request.args.get('local', '')
    visitante = request.args.get('visitante', '')
    d1 = obtener_seleccion(local)
    d2 = obtener_seleccion(visitante)
    if not d1 or not d2:
        return jsonify({'error': 'Equipo no encontrado'}), 404
    
    rating_local = d1.get('rating_promedio', 6.5) * 10
    rating_visitante = d2.get('rating_promedio', 6.5) * 10
    goles_local = d1.get('goles_total', 0) / d1.get('jugadores', 1)
    goles_visitante = d2.get('goles_total', 0) / d2.get('jugadores', 1)
    
    fuerza_local = rating_local * 0.5 + goles_local * 30
    fuerza_visitante = rating_visitante * 0.5 + goles_visitante * 30
    
    total = fuerza_local + fuerza_visitante
    prob_local = round((fuerza_local / total) * 70, 1)
    prob_visitante = round((fuerza_visitante / total) * 70, 1)
    prob_empate = round(100 - prob_local - prob_visitante, 1)
    
    if prob_local > 50:
        recomendacion = f"💰 Apostar por {local} - Probabilidad: {prob_local}%"
        color = "green"
    elif prob_visitante > 50:
        recomendacion = f"💰 Apostar por {visitante} - Probabilidad: {prob_visitante}%"
        color = "blue"
    else:
        recomendacion = f"🤝 Apostar al empate - Probabilidad: {prob_empate}%"
        color = "orange"
    
    return jsonify({
        'local': {'nombre': local, 'probabilidad': prob_local},
        'empate': {'probabilidad': prob_empate},
        'visitante': {'nombre': visitante, 'probabilidad': prob_visitante},
        'recomendacion': recomendacion,
        'color': color
    })

@app.route('/api/jugador/buscar')
def api_buscar_jugador():
    nombre = request.args.get('nombre', '')
    jugador = buscar_jugador_local(nombre)
    if jugador:
        return jsonify(jugador)
    return jsonify({'error': 'Jugador no encontrado'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
