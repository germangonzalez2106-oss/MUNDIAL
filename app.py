import os
import requests
from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient

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

# ==================== DATOS COMPLETOS ====================
DATOS_COMPLETOS = [
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
    return DATOS_COMPLETOS

# ==================== HISTORIAL ====================
HISTORIAL = {
    ("Argentina", "Brasil"): [
        {"fecha": "2025-11-21", "competicion": "Eliminatorias", "resultado": "Argentina 2-1 Brasil"},
        {"fecha": "2024-07-10", "competicion": "Copa América", "resultado": "Argentina 1-0 Brasil"},
    ],
    ("Argentina", "Francia"): [
        {"fecha": "2022-12-18", "competicion": "Final Mundial", "resultado": "Argentina 3-3 Francia (4-2 pen)"},
    ],
}

def obtener_historial(e1, e2):
    partidos = HISTORIAL.get((e1, e2)) or HISTORIAL.get((e2, e1))
    if not partidos:
        return None
    return {"total": len(partidos), "partidos": partidos, "goles_local": 0, "goles_visitante": 0}

def pronostico(local, visitante):
    equipos = {e['nombre']: e for e in DATOS_COMPLETOS}
    d1 = equipos.get(local)
    d2 = equipos.get(visitante)
    if not d1 or not d2:
        return None
    r1 = d1['ranking_fifa']
    r2 = d2['ranking_fifa']
    p1 = max(0, 100 - (r1 - 1) * 3)
    p2 = max(0, 100 - (r2 - 1) * 3)
    total = p1 + p2
    prob1 = round((p1 / total) * 70, 1)
    prob2 = round((p2 / total) * 70, 1)
    probE = round(100 - prob1 - prob2, 1)
    if prob1 > 50:
        rec = f"💰 Favorito: {local} ({prob1}%)"
    elif prob2 > 50:
        rec = f"💰 Favorito: {visitante} ({prob2}%)"
    else:
        rec = f"🤝 Partido parejo"
    return {'local': prob1, 'empate': probE, 'visitante': prob2, 'recomendacion': rec}

# ==================== HTML COMPLETO (CON MENÚS FUNCIONALES) ====================
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
        fetch('/api/selecciones').then(r => r.json()).then(data => {
            let topRating = [...data].sort((a,b)=>b.rating_promedio - a.rating_promedio).slice(0,10);
            let ctx1 = document.getElementById('ratingChart').getContext('2d');
            if (ratingChart) ratingChart.destroy();
            ratingChart = new Chart(ctx1, {
                type: 'bar',
                data: { labels: topRating.map(t=>t.nombre), datasets: [{ label: 'Rating', data: topRating.map(t=>t.rating_promedio), backgroundColor: 'rgba(76,175,80,0.7)' }] },
                options: { responsive: true }
            });
            let topGoles = [...data].sort((a,b)=>b.goles_total - a.goles_total).slice(0,10);
            let ctx2 = document.getElementById('golesChart').getContext('2d');
            if (golesChart) golesChart.destroy();
            golesChart = new Chart(ctx2, {
                type: 'bar',
                data: { labels: topGoles.map(t=>t.nombre), datasets: [{ label: 'Goles', data: topGoles.map(t=>t.goles_total), backgroundColor: 'rgba(33,150,243,0.7)' }] },
                options: { responsive: true }
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
    <div class="nav"><a href="/">🏆 Ranking</a><a href="/jugador">🔍 Jugadores</a><a href="/eliminatorias">🌍 Eliminatorias</a></div>
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
        <tr><td>1</td><td>Argentina</td><td>38</td></tr>
        <tr><td>2</td><td>Ecuador</td><td>29</td></tr>
        <tr><td>3</td><td>Colombia</td><td>28</td></tr>
        <tr><td>4</td><td>Uruguay</td><td>28</td></tr>
        <tr><td>5</td><td>Brasil</td><td>28</td></tr>
        <tr><td>6</td><td>Paraguay</td><td>25</td></tr>
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
    <div class="nav"><a href="/">🏆 Ranking</a><a href="/jugador">🔍 Jugadores</a><a href="/eliminatorias">🌍 Eliminatorias</a></div>
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

@app.route('/')
def index():
    selecciones = obtener_selecciones()
    total_jugadores = sum(s.get('jugadores', 0) for s in selecciones)
    return render_template_string(HTML, 
                                  selecciones=selecciones, 
                                  total_selecciones=len(selecciones), 
                                  total_jugadores=total_jugadores)

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
    return "<h1>🔍 Jugadores</h1><p>Próximamente</p>"

@app.route('/eliminatorias')
def eliminatorias():
    return "<h1>🌍 Eliminatorias</h1><p>Próximamente</p>"

@app.route('/resultados')
def resultados():
    return "<h1>📋 Resultados</h1><p>Próximamente</p>"

@app.route('/api/odds')
def api_odds():
    return jsonify({'success': True, 'games': []})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
