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

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Mundial 2026 - Estadísticas</title>
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
        
        /* Tarjetas de estadísticas */
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
        
        /* Gráficos */
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
        
        /* Buscador */
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
            transition: background 0.3s;
        }
        .compare-btn { background: #2196F3; }
        .search-box button:hover, .compare-btn:hover { opacity: 0.8; }
        
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
        .ganador { color: #4CAF50; font-weight: bold; }
        
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
    <h1>🏆 Mundial 2026</h1>
    <div class="subtitle">Análisis estadístico de las 25 selecciones clasificadas</div>
    
    <!-- Tarjetas -->
    <div class="stats-cards">
        <div class="stat-card"><h3>{{ total_selecciones }}</h3><p>Selecciones</p></div>
        <div class="stat-card"><h3>{{ total_jugadores }}</h3><p>Jugadores</p></div>
        <div class="stat-card"><h3>📊</h3><p>Estadísticas</p></div>
        <div class="stat-card"><h3>☁️</h3><p>MongoDB Atlas</p></div>
    </div>
    
    <!-- Gráficos -->
    <div class="charts-section">
        <div class="chart-card">
            <h3>⭐ Top 10 - Rating Promedio</h3>
            <canvas id="ratingChart"></canvas>
        </div>
        <div class="chart-card">
            <h3>⚽ Top 10 - Goles Totales</h3>
            <canvas id="golesChart"></canvas>
        </div>
    </div>
    
    <!-- Buscador -->
    <div class="search-section">
        <h3>🔍 Buscar Jugador</h3>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Ej: Messi, Mbappé, Haaland...">
            <button onclick="buscarJugador()">Buscar</button>
        </div>
        <div id="resultadosBusqueda" class="results"></div>
    </div>
    
    <!-- Comparador -->
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
            <button class="compare-btn" onclick="comparar()">Comparar</button>
        </div>
        <div id="comparacionResultado" class="results"></div>
    </div>
    
    <!-- Ranking -->
    <div class="ranking-section">
        <h3>📊 Ranking de Selecciones</h3>
        <table>
            <thead><tr><th>#</th><th>Selección</th><th>Jugadores</th><th>Goles</th><th>Rating</th><th>Acción</th></tr></thead>
            <tbody>
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
    let ratingChart = null;
    let golesChart = null;
    
    function cargarGraficos() {
        fetch('/api/selecciones')
            .then(response => response.json())
            .then(data => {
                // Top 10 por rating
                let topRating = [...data].sort((a,b) => b.rating_promedio - a.rating_promedio).slice(0, 10);
                let ctxRating = document.getElementById('ratingChart').getContext('2d');
                if (ratingChart) ratingChart.destroy();
                ratingChart = new Chart(ctxRating, {
                    type: 'bar',
                    data: {
                        labels: topRating.map(t => t.nombre),
                        datasets: [{
                            label: 'Rating Promedio',
                            data: topRating.map(t => t.rating_promedio),
                            backgroundColor: 'rgba(76, 175, 80, 0.7)',
                            borderColor: 'rgba(76, 175, 80, 1)',
                            borderWidth: 1,
                            borderRadius: 10
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { labels: { color: 'white' } },
                            tooltip: { callbacks: { label: function(ctx) { return ctx.raw.toFixed(2); } } }
                        },
                        scales: {
                            y: { ticks: { color: 'white' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                            x: { ticks: { color: 'white', rotation: 45, font: { size: 10 } }, grid: { display: false } }
                        }
                    }
                });
                
                // Top 10 por goles
                let topGoles = [...data].sort((a,b) => b.goles_total - a.goles_total).slice(0, 10);
                let ctxGoles = document.getElementById('golesChart').getContext('2d');
                if (golesChart) golesChart.destroy();
                golesChart = new Chart(ctxGoles, {
                    type: 'bar',
                    data: {
                        labels: topGoles.map(t => t.nombre),
                        datasets: [{
                            label: 'Goles Totales',
                            data: topGoles.map(t => t.goles_total),
                            backgroundColor: 'rgba(33, 150, 243, 0.7)',
                            borderColor: 'rgba(33, 150, 243, 1)',
                            borderWidth: 1,
                            borderRadius: 10
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { labels: { color: 'white' } },
                            tooltip: { callbacks: { label: function(ctx) { return ctx.raw.toFixed(0); } } }
                        },
                        scales: {
                            y: { ticks: { color: 'white' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                            x: { ticks: { color: 'white', rotation: 45, font: { size: 10 } }, grid: { display: false } }
                        }
                    }
                });
            });
    }
    
    function buscarJugador() {
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
                    html += '<h3>✅ Resultados (' + data.length + ')</h3>';
                    html += '<table><thead><tr><th>Jugador</th><th>Selección</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>';
                    for (let j of data) {
                        html += '<tr><td><strong>' + j.jugador + '</strong></td><td>' + j.seleccion + '</td><td>' + j.goles + '</td><td>' + j.asistencias + '</td><td>' + j.rating + '</td></tr>';
                    }
                    html += '</tbody></tr>';
                    div.innerHTML = html;
                }
                div.style.display = 'block';
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
    }
    
    function cerrarBusqueda() {
        document.getElementById('resultadosBusqueda').style.display = 'none';
    }
    
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
                html += '<h3>📋 Plantilla</h3>';
                html += '<div style="overflow-x:auto;">';
                html += '<table><thead><tr><th>Jugador</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>';
                for (let j of data.plantilla) {
                    html += '<tr><td>' + j.jugador + '</td><td>' + j.goles + '</td><td>' + j.asistencias + '</td><td>' + j.rating + '</td></tr>';
                }
                html += '</tbody></table></div>';
                
                let div = document.getElementById('comparacionResultado');
                div.innerHTML = html;
                div.style.display = 'block';
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
    }
    
    function cerrarComparacion() {
        document.getElementById('comparacionResultado').style.display = 'none';
    }
    
    function comparar() {
        let eq1 = document.getElementById('equipo1').value;
        let eq2 = document.getElementById('equipo2').value;
        if (!eq1 || !eq2) { alert("Selecciona dos equipos"); return; }
        if (eq1 === eq2) { alert("Selecciona equipos diferentes"); return; }
        
        fetch('/api/comparar?eq1=' + encodeURIComponent(eq1) + '&eq2=' + encodeURIComponent(eq2))
            .then(r => r.json())
            .then(data => {
                let winner1 = data.equipo1.rating_promedio > data.equipo2.rating_promedio ? 'ganador' : '';
                let winner2 = data.equipo2.rating_promedio > data.equipo1.rating_promedio ? 'ganador' : '';
                let html = '<button class="close-btn" onclick="cerrarComparacion()">Cerrar</button>';
                html += '<div style="display:grid;grid-template-columns:1fr auto 1fr;gap:20px;">';
                
                html += '<div style="background:#1a1a2e;padding:20px;border-radius:15px;">';
                html += '<h3 style="text-align:center;color:#4CAF50">' + data.equipo1.nombre + '</h3>';
                html += '<div style="margin:10px 0"><strong>🏆 Rating:</strong> <span class="' + winner1 + '">' + data.equipo1.rating_promedio + '</span></div>';
                html += '<div><strong>⚽ Goles:</strong> ' + data.equipo1.goles_total + '</div>';
                html += '<div><strong>🎯 Asistencias:</strong> ' + data.equipo1.asistencias_total + '</div>';
                html += '<div><strong>⭐ Mejor:</strong> ' + data.equipo1.mejor_rating.nombre + ' (' + data.equipo1.mejor_rating.valor + ')</div>';
                html += '<div><strong>⚽ Goleador:</strong> ' + data.equipo1.max_goleador.nombre + ' (' + data.equipo1.max_goleador.goles + ')</div>';
                html += '</div>';
                
                html += '<div style="font-size:36px;display:flex;align-items:center;">VS</div>';
                
                html += '<div style="background:#1a1a2e;padding:20px;border-radius:15px;">';
                html += '<h3 style="text-align:center;color:#4CAF50">' + data.equipo2.nombre + '</h3>';
                html += '<div style="margin:10px 0"><strong>🏆 Rating:</strong> <span class="' + winner2 + '">' + data.equipo2.rating_promedio + '</span></div>';
                html += '<div><strong>⚽ Goles:</strong> ' + data.equipo2.goles_total + '</div>';
                html += '<div><strong>🎯 Asistencias:</strong> ' + data.equipo2.asistencias_total + '</div>';
                html += '<div><strong>⭐ Mejor:</strong> ' + data.equipo2.mejor_rating.nombre + ' (' + data.equipo2.mejor_rating.valor + ')</div>';
                html += '<div><strong>⚽ Goleador:</strong> ' + data.equipo2.max_goleador.nombre + ' (' + data.equipo2.max_goleador.goles + ')</div>';
                html += '</div>';
                
                html += '</div>';
                
                let div = document.getElementById('comparacionResultado');
                div.innerHTML = html;
                div.style.display = 'block';
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
    }
    
    // Cargar gráficos al iniciar
    window.onload = cargarGraficos;
</script>
</body>
</html>
"""

@app.route('/')
def index():
    selecciones = obtener_selecciones()
    total_jugadores = sum(s.get('jugadores', 0) for s in selecciones)
    return render_template_string(HTML, selecciones=selecciones, total_selecciones=len(selecciones), total_jugadores=total_jugadores)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
