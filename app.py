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

# ==================== DATOS ====================
# ==================== ELIMINATORIAS POR CONTINENTE ====================

ELIMINATORIAS = {
    "Sudamérica": {
        "clasificados": ["Argentina", "Ecuador", "Uruguay", "Colombia", "Brasil", "Paraguay"],
        "repechaje": ["Bolivia"],
        "eliminados": ["Venezuela", "Perú", "Chile"],
        "max_goleador": {"jugador": "Lionel Messi", "goles": 8},
        "fecha_final": "2025-09-10"
    },
    "Europa": {
        "clasificados_directos": ["España", "Francia", "Alemania", "Inglaterra", "Países Bajos", 
                                  "Croacia", "Portugal", "Escocia", "Austria", "Bélgica", 
                                  "Suiza", "Noruega"],
        "clasificados_repechaje": ["Bosnia", "República Checa", "Suecia", "Turquía"],
        "finales_repechaje": [
            {"partido": "Bosnia vs Italia", "resultado": "1-1 (4-1 pen)", "ganador": "Bosnia"},
            {"partido": "Suecia vs Polonia", "resultado": "3-2", "ganador": "Suecia"},
            {"partido": "Kosovo vs Turquía", "resultado": "0-1", "ganador": "Turquía"},
            {"partido": "Dinamarca vs Rep. Checa", "resultado": "2-2 (1-3 pen)", "ganador": "República Checa"}
        ],
        "fecha_final": "2026-03-31"
    },
    "África": {
        "clasificados_confirmados": ["Sudáfrica", "Egipto", "Marruecos", "Argelia", "Costa de Marfil", "Ghana"],
        "grupos": {
            "Grupo C": {"primero": "Sudáfrica", "puntos": 18, "segundo": "Nigeria", "tercero": "Benín"},
            "Grupo 1": {"primero": "Egipto", "puntos": 13},
            "Grupo 4": {"primero": "Marruecos", "puntos": 12},
            "Grupo 7": {"primero": "Argelia", "puntos": 12},
            "Grupo 6": {"primero": "Costa de Marfil"},
            "Grupo 9": {"primero": "Ghana"}
        },
        "fecha_final": "2025-10-14"
    },
    "Asia": {
        "clasificados": ["Corea del Sur", "Japón", "Irán", "Australia", "Arabia Saudita", "Uzbekistán", "Qatar", "Jordania"],
        "grupo_c": {
            "primero": "Corea del Sur",
            "puntos": 16,
            "record": "20 goles a favor, 1 en contra"
        },
        "resultados_destacados": [
            {"partido": "Australia vs China", "resultado": "3-1"},
            {"partido": "Corea del Sur vs China", "resultado": "3-0"},
            {"partido": "Corea del Sur vs Tailandia", "resultado": "1-1"}
        ]
    },
    "Norteamérica": {
        "clasificados": ["México", "Canadá", "Estados Unidos", "Panamá"],
        "grupo_c": {
            "segundo": "Honduras",
            "tercero": "Costa Rica",
            "resultado_final": "Costa Rica 0-0 Honduras"
        },
        "fecha_final": "2025-11-18"
    }
}

def obtener_resumen_eliminatorias(continente=None):
    """Obtiene resumen de eliminatorias por continente"""
    if continente:
        return ELIMINATORIAS.get(continente, {})
    return ELIMINATORIAS



JUGADORES_MANUALES = {
    "messi": {"player": "Lionel Messi", "team": "Inter Miami", "league": "MLS", "goals": 12, "assists": 8, "rating": 8.2},
    "cristiano ronaldo": {"player": "Cristiano Ronaldo", "team": "Al Nassr", "league": "Saudi Pro League", "goals": 28, "assists": 6, "rating": 7.9}
}

HISTORIAL = {
    
    ("Argentina", "Brasil"): [{"fecha": "2025-11-21", "competicion": "Eliminatorias", "resultado": "Argentina 2-1 Brasil"}],
    ("Argentina", "Francia"): [{"fecha": "2022-12-18", "competicion": "Mundial Final", "resultado": "Argentina 3-3 Francia (4-2 pen)"}],
    ("Argentina", "Alemania"): [{"fecha": "2014-07-13", "competicion": "Mundial Final", "resultado": "Alemania 1-0 Argentina"}],
    ("Brasil", "Alemania"): [{"fecha": "2014-07-08", "competicion": "Mundial Semifinal", "resultado": "Brasil 1-7 Alemania"}],
    ("Inglaterra", "Francia"): [{"fecha": "2022-12-10", "competicion": "Mundial", "resultado": "Francia 2-1 Inglaterra"}],
    ("Portugal", "España"): [{"fecha": "2018-06-15", "competicion": "Mundial", "resultado": "Portugal 3-3 España"}],
    ("Inglaterra", "Alemania"): [{"fecha": "2021-06-29", "competicion": "Eurocopa", "resultado": "Inglaterra 2-0 Alemania"}],




}

ODDS_API_KEY = "1928777e3a71509cabffaf3c507876ce"


# ==================== FUNCIONES ====================
def api_eliminatorias():
    continente = request.args.get('continente', '')
    if continente:
        data = ELIMINATORIAS.get(continente)
        if not data:
            return jsonify({'error': 'Continente no encontrado'}), 404
        return jsonify({'continente': continente, 'datos': data})
    return jsonify(ELIMINATORIAS)

def obtener_selecciones():
    if coleccion is None: return []
    return list(coleccion.find({}, {'_id': 0}))

def obtener_historial(e1, e2):
    h = HISTORIAL.get((e1, e2)) or HISTORIAL.get((e2, e1))
    if not h: return None
    return {"total": len(h), "partidos": h}

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
    <h2>📜 Historial</h2>
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
        div.innerHTML = '<p>Cargando...</p>';
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

# ==================== PÁGINA JUGADORES ====================
HTML_JUGADOR = """
<!DOCTYPE html>
<html>
<head><title>Buscador de Jugadores</title><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
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
    .close{background:#f44336;padding:5px 15px;font-size:12px;margin-bottom:15px;}
</style>
</head>
<body>
<div class="container">
    <div class="nav"><a href="/">🏆 Ranking</a><a href="/jugador">🔍 Jugadores</a></div>
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
                let html='<button class="close" onclick="cerrar()">Cerrar</button><h3>'+data.player+'</h3>';
                html+='<div class="grid"><div class="card"><h3>'+data.goals+'</h3><p>Goles</p></div>';
                html+='<div class="card"><h3>'+data.assists+'</h3><p>Asistencias</p></div>';
                html+='<div class="card"><h3>'+data.rating+'</h3><p>Rating</p></div></div>';
                html+='<p><strong>Equipo:</strong> '+data.team+' ('+data.league+')</p>';
                div.innerHTML=html;
            }
            div.style.display='block';
        });
    }
    function cerrar(){document.getElementById('resultado').style.display='none';}
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
        g1 = sum(int(p['resultado'].split('-')[0].split()[-1]) for p in h['partidos'] if p['resultado'].split('-')[0].strip().split()[-1].isdigit())
        g2 = sum(int(p['resultado'].split('-')[1].split()[0]) for p in h['partidos'] if p['resultado'].split('-')[1].strip().split()[0].isdigit())
        return jsonify({'total': h['total'], 'partidos': h['partidos'], 'goles_local': g1, 'goles_visitante': g2})
    return jsonify({'error': 'No hay historial'}), 404

@app.route('/api/jugador/buscar')
def api_buscar_jugador():
    nombre = request.args.get('nombre', '').lower()
    for k, v in JUGADORES_MANUALES.items():
        if k in nombre or nombre in k:
            return jsonify(v)
    return jsonify({'error': 'No encontrado'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
