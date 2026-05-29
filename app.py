import os
import requests
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
from datetime import datetime, timedelta
import hashlib

app = Flask(__name__)

# ==================== CONEXIÓN MONGODB ====================
MONGO_URI = "mongodb://mundial_user:M4nzana2026@ac-0tfmbvr-shard-00-00.tqvej0i.mongodb.net:27017,ac-0tfmbvr-shard-00-01.tqvej0i.mongodb.net:27017,ac-0tfmbvr-shard-00-02.tqvej0i.mongodb.net:27017/?ssl=true&replicaSet=atlas-fjc1fq-shard-0&authSource=admin&tlsAllowInvalidCertificates=true"

try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
    db = client['mundial_2026']
    coleccion = db['selecciones']
    print(f"✅ Conectado: {coleccion.count_documents({})} selecciones")
except Exception as e:
    print(f"❌ Error MongoDB: {e}")
    coleccion = None

# ==================== DATOS DE RESPALDO ====================
DATOS_RESPALDO = [
    {'nombre': 'Argentina', 'jugadores': 18, 'goles_total': 61, 'rating_promedio': 8.23, 'ranking_fifa': 1},
    {'nombre': 'Francia', 'jugadores': 18, 'goles_total': 69, 'rating_promedio': 8.29, 'ranking_fifa': 2},
    {'nombre': 'Brasil', 'jugadores': 18, 'goles_total': 56, 'rating_promedio': 7.99, 'ranking_fifa': 3},
    {'nombre': 'Inglaterra', 'jugadores': 18, 'goles_total': 51, 'rating_promedio': 7.93, 'ranking_fifa': 4},
    {'nombre': 'Bélgica', 'jugadores': 23, 'goles_total': 76, 'rating_promedio': 8.12, 'ranking_fifa': 5},
    {'nombre': 'Croacia', 'jugadores': 23, 'goles_total': 61, 'rating_promedio': 7.85, 'ranking_fifa': 6},
    {'nombre': 'Países Bajos', 'jugadores': 18, 'goles_total': 60, 'rating_promedio': 7.81, 'ranking_fifa': 7},
    {'nombre': 'Portugal', 'jugadores': 18, 'goles_total': 43, 'rating_promedio': 7.8, 'ranking_fifa': 8},
    {'nombre': 'España', 'jugadores': 18, 'goles_total': 82, 'rating_promedio': 7.55, 'ranking_fifa': 9},
    {'nombre': 'Italia', 'jugadores': 23, 'goles_total': 55, 'rating_promedio': 7.32, 'ranking_fifa': 10},
    {'nombre': 'Alemania', 'jugadores': 18, 'goles_total': 74, 'rating_promedio': 7.5, 'ranking_fifa': 11},
    {'nombre': 'Uruguay', 'jugadores': 23, 'goles_total': 54, 'rating_promedio': 7.35, 'ranking_fifa': 12},
    {'nombre': 'Colombia', 'jugadores': 23, 'goles_total': 72, 'rating_promedio': 7.24, 'ranking_fifa': 13},
    {'nombre': 'México', 'jugadores': 23, 'goles_total': 72, 'rating_promedio': 7.11, 'ranking_fifa': 14},
    {'nombre': 'Estados Unidos', 'jugadores': 23, 'goles_total': 55, 'rating_promedio': 7.23, 'ranking_fifa': 15},
    {'nombre': 'Marruecos', 'jugadores': 23, 'goles_total': 55, 'rating_promedio': 6.81, 'ranking_fifa': 16},
    {'nombre': 'Senegal', 'jugadores': 23, 'goles_total': 70, 'rating_promedio': 6.68, 'ranking_fifa': 17},
    {'nombre': 'Japón', 'jugadores': 23, 'goles_total': 69, 'rating_promedio': 6.86, 'ranking_fifa': 18},
    {'nombre': 'Corea del Sur', 'jugadores': 23, 'goles_total': 82, 'rating_promedio': 6.55, 'ranking_fifa': 19},
    {'nombre': 'Egipto', 'jugadores': 23, 'goles_total': 54, 'rating_promedio': 6.66, 'ranking_fifa': 20},
    {'nombre': 'Australia', 'jugadores': 23, 'goles_total': 61, 'rating_promedio': 6.56, 'ranking_fifa': 21},
    {'nombre': 'Suiza', 'jugadores': 23, 'goles_total': 90, 'rating_promedio': 6.4, 'ranking_fifa': 22},
    {'nombre': 'Dinamarca', 'jugadores': 23, 'goles_total': 81, 'rating_promedio': 6.41, 'ranking_fifa': 23},
    {'nombre': 'Polonia', 'jugadores': 23, 'goles_total': 60, 'rating_promedio': 6.26, 'ranking_fifa': 24},
    {'nombre': 'Canadá', 'jugadores': 23, 'goles_total': 62, 'rating_promedio': 6.17, 'ranking_fifa': 25},
]

def obtener_selecciones():
    """Obtiene selecciones (MongoDB o respaldo)"""
    if coleccion is not None:
        try:
            selecciones = list(coleccion.find({}, {'_id': 0, 'nombre': 1, 'jugadores': 1, 'goles_total': 1, 'rating_promedio': 1, 'ranking_fifa': 1}))
            if selecciones and len(selecciones) > 0:
                selecciones.sort(key=lambda x: x.get('ranking_fifa', 999))
                return selecciones
        except Exception as e:
            print(f"Error MongoDB: {e}")
    return DATOS_RESPALDO

# ==================== HISTORIAL Y PARTIDOS ====================
HISTORIAL_ENFRENTAMIENTOS = {
    ("Argentina", "Brasil"): [
        {"fecha": "2025-11-21", "competicion": "Eliminatorias", "resultado": "Argentina 2-1 Brasil"},
        {"fecha": "2024-07-10", "competicion": "Copa América", "resultado": "Argentina 1-0 Brasil"},
    ],
    ("Argentina", "Francia"): [
        {"fecha": "2022-12-18", "competicion": "Mundial Final", "resultado": "Argentina 3-3 Francia (4-2 pen)"},
    ],
}

def obtener_historial(e1, e2):
    h = HISTORIAL_ENFRENTAMIENTOS.get((e1, e2)) or HISTORIAL_ENFRENTAMIENTOS.get((e2, e1))
    if not h:
        return None
    goles1 = goles2 = 0
    for p in h:
        try:
            if e1 in p['resultado']:
                import re
                nums = re.findall(r'(\d+)-(\d+)', p['resultado'])
                if nums:
                    g1, g2 = map(int, nums[0])
                    if p['resultado'].startswith(e1):
                        goles1 += g1
                        goles2 += g2
                    else:
                        goles1 += g2
                        goles2 += g1
        except:
            pass
    return {"total": len(h), "partidos": h, "goles_local": goles1, "goles_visitante": goles2}

def pronostico(local, visitante):
    selecciones = {s['nombre']: s for s in obtener_selecciones()}
    d1 = selecciones.get(local)
    d2 = selecciones.get(visitante)
    if not d1 or not d2:
        return None
    ranking1 = d1.get('ranking_fifa', 15)
    ranking2 = d2.get('ranking_fifa', 15)
    fuerza1 = max(0, 100 - (ranking1 - 1) * 3)
    fuerza2 = max(0, 100 - (ranking2 - 1) * 3)
    total = fuerza1 + fuerza2
    prob1 = round((fuerza1 / total) * 70, 1)
    prob2 = round((fuerza2 / total) * 70, 1)
    probE = round(100 - prob1 - prob2, 1)
    if prob1 < 5: prob1 = 5
    if prob2 < 5: prob2 = 5
    probE = 100 - prob1 - prob2
    if prob1 > 50:
        rec = f"💰 Apostar por {local} - Prob: {prob1}% (Ranking #{ranking1})"
    elif prob2 > 50:
        rec = f"💰 Apostar por {visitante} - Prob: {prob2}% (Ranking #{ranking2})"
    else:
        rec = f"🤝 Apostar al empate - Partido parejo"
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
        body { font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 20px; }
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
        select, button, input { padding: 10px 20px; border-radius: 25px; border: none; background: #0f3460; color: white; cursor: pointer; }
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
        <div class="chart-box"><h3>⭐ Top 10 - Rating Promedio</h3><canvas id="ratingChart"></canvas></div>
        <div class="chart-box"><h3>⚽ Top 10 - Goles Totales</h3><canvas id="golesChart"></canvas></div>
    </div>
    
    <h2>🔮 Pronóstico</h2>
    <div class="flex">
        <select id="eqLocal"><option value="">Local</option>{% for s in selecciones %}<option value="{{ s.nombre }}">{{ s.nombre }}</option>{% endfor %}</select>
        <span>VS</span>
        <select id="eqVisitante"><option value="">Visitante</option>{% for s in selecciones %}<option value="{{ s.nombre }}">{{ s.nombre }}</option>{% endfor %}</select>
        <button class="btn-orange" onclick="calcularPronostico()">🔮 Calcular</button>
    </div>
    <div id="pronosticoResultado" class="results"></div>
    
    <h2>📜 Historial de Enfrentamientos</h2>
    <div class="flex">
        <select id="histLocal"><option value="">Equipo</option>{% for s in selecciones %}<option value="{{ s.nombre }}">{{ s.nombre }}</option>{% endfor %}</select>
        <span>VS</span>
        <select id="histVisit"><option value="">Equipo</option>{% for s in selecciones %}<option value="{{ s.nombre }}">{{ s.nombre }}</option>{% endfor %}</select>
        <button class="btn-blue" onclick="cargarHistorial()">📜 Ver</button>
    </div>
    <div id="historialResultado" class="results"></div>
    
    <h2>📋 Ranking</h2>
    <table><thead>运转<th>#</th><th>Selección</th><th>Jugadores</th><th>Goles</th><th>Rating</th></tr></thead>
    <tbody>{% for s in selecciones %}
    <tr><td>{{ loop.index }}</td><td><strong>{{ s.nombre }}</strong></td><td>{{ s.jugadores }}</td><td>{{ s.goles_total }}</td><td>{{ s.rating_promedio }}</td></tr>
    {% endfor %}</tbody>
    </table>
</div>

<script>
    function cargarGraficos() {
        fetch('/api/selecciones').then(r=>r.json()).then(data=>{
            let topRating = [...data].sort((a,b)=>b.rating_promedio - a.rating_promedio).slice(0,10);
            new Chart(document.getElementById('ratingChart'), {
                type: 'bar', data: { labels: topRating.map(t=>t.nombre), datasets: [{ label: 'Rating', data: topRating.map(t=>t.rating_promedio), backgroundColor: '#4CAF50' }] },
                options: { responsive: true, plugins: { legend: { labels: { color: 'white' } } }, scales: { y: { ticks: { color: 'white' } }, x: { ticks: { color: 'white', rotation: 45 } } } }
            });
            let topGoles = [...data].sort((a,b)=>b.goles_total - a.goles_total).slice(0,10);
            new Chart(document.getElementById('golesChart'), {
                type: 'bar', data: { labels: topGoles.map(t=>t.nombre), datasets: [{ label: 'Goles', data: topGoles.map(t=>t.goles_total), backgroundColor: '#2196F3' }] },
                options: { responsive: true, plugins: { legend: { labels: { color: 'white' } } }, scales: { y: { ticks: { color: 'white' } }, x: { ticks: { color: 'white', rotation: 45 } } } }
            });
        }).catch(e=>console.error(e));
    }
    
    function calcularPronostico() {
        let local = document.getElementById('eqLocal').value;
        let visitante = document.getElementById('eqVisitante').value;
        if (!local || !visitante || local===visitante) { alert("Selecciona dos equipos diferentes"); return; }
        let div = document.getElementById('pronosticoResultado');
        div.innerHTML = '<p>Cargando...</p>';
        div.style.display = 'block';
        fetch(`/api/pronostico?local=${encodeURIComponent(local)}&visitante=${encodeURIComponent(visitante)}`)
            .then(r=>r.json()).then(data=>{
                div.innerHTML = `<div class="grid-3"><div class="stat-card"><div class="big-number">${data.local}%</div><div>🏠 ${local}</div></div>
                    <div class="stat-card"><div class="big-number">${data.empate}%</div><div>🤝 Empate</div></div>
                    <div class="stat-card"><div class="big-number">${data.visitante}%</div><div>✈️ ${visitante}</div></div>
                </div><div style="background:#1a1a2e;padding:15px;border-radius:10px;text-align:center">${data.recomendacion}</div>`;
            }).catch(e=>div.innerHTML='<p>Error</p>');
    }
    
    function cargarHistorial() {
        let local = document.getElementById('histLocal').value;
        let visitante = document.getElementById('histVisit').value;
        if (!local || !visitante) { alert("Selecciona dos equipos"); return; }
        let div = document.getElementById('historialResultado');
        div.innerHTML = '<p>Cargando...</p>';
        div.style.display = 'block';
        fetch(`/api/historial?eq1=${encodeURIComponent(local)}&eq2=${encodeURIComponent(visitante)}`)
            .then(r=>r.json()).then(data=>{
                if (data.error) { div.innerHTML = `<p>${data.error}</p>`; return; }
                let html = `<h3>📊 ${local} vs ${visitante}</h3><div class="grid-3"><div class="stat-card">🏆 Total<br><span class="big-number">${data.total}</span><br>partidos</div>
                    <div class="stat-card">⚽ Goles ${local}<br><span class="big-number">${data.goles_local}</span></div>
                    <div class="stat-card">⚽ Goles ${visitante}<br><span class="big-number">${data.goles_visitante}</span></div></div>
                    <h4>📋 Partidos</h4><table><thead><tr><th>Fecha</th><th>Competición</th><th>Resultado</th></tr></thead><tbody>`;
                for (let p of data.partidos) html += `<tr><td>${p.fecha}</td><td>${p.competicion}</td><td>${p.resultado}</td></tr>`;
                html += `</tbody></table>`;
                div.innerHTML = html;
            }).catch(e=>div.innerHTML='<p>Error</p>');
    }
    
    document.addEventListener('DOMContentLoaded', () => { cargarGraficos(); });
</script>
</body>
</html>
"""

HTML_JUGADOR = "<!DOCTYPE html><html><head><title>Jugadores</title></head><body><h1>🔍 Buscador</h1><input id='search'><button onclick='buscar()'>Buscar</button><div id='res'></div><script>function buscar(){fetch('/api/jugador/buscar?nombre='+document.getElementById('search').value).then(r=>r.json()).then(d=>{document.getElementById('res').innerHTML=d.error?d.error:`<h3>${d.player}</h3><p>Goles: ${d.goals}</p>`;})}</script></body></html>"

# ==================== RUTAS ====================
@app.route('/')
def index():
    selecciones = obtener_selecciones()
    total_jugadores = sum(s.get('jugadores', 0) for s in selecciones)
    return render_template_string(HTML, selecciones=selecciones, total_selecciones=len(selecciones), total_jugadores=total_jugadores)

@app.route('/api/selecciones')
def api_selecciones():
    return jsonify(obtener_selecciones())

@app.route('/api/pronostico')
def api_pronostico():
    local = request.args.get('local', '')
    visitante = request.args.get('visitante', '')
    p = pronostico(local, visitante)
    return jsonify(p) if p else jsonify({'error': 'Error'}), 404

@app.route('/api/historial')
def api_historial():
    e1, e2 = request.args.get('eq1', ''), request.args.get('eq2', '')
    h = obtener_historial(e1, e2)
    return jsonify(h) if h else jsonify({'error': 'No hay historial'}), 404

@app.route('/jugador')
def jugador():
    return render_template_string(HTML_JUGADOR)

@app.route('/eliminatorias')
def eliminatorias():
    return "<h1>Eliminatorias</h1><p>Próximamente</p>"

@app.route('/resultados')
def resultados():
    return "<h1>Resultados</h1><p>Próximamente</p>"

@app.route('/api/odds')
def api_odds():
    return jsonify({'success': True, 'games': []})

@app.route('/api/jugador/buscar')
def api_buscar_jugador():
    return jsonify({'error': 'No encontrado'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
