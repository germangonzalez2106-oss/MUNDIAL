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

# ==================== JUGADORES MANUALES ====================
JUGADORES_MANUALES = {
    "messi": {"player": "Lionel Messi", "team": "Inter Miami", "league": "MLS", "goals": 12, "assists": 8, "rating": 8.2},
    "cristiano ronaldo": {"player": "Cristiano Ronaldo", "team": "Al Nassr", "league": "Saudi Pro League", "goals": 28, "assists": 6, "rating": 7.9}
}

# ==================== ELIMINATORIAS ====================
ELIMINATORIAS = {
    "Sudamérica": {"clasificados": ["Argentina", "Ecuador", "Uruguay", "Colombia", "Brasil", "Paraguay"]},
    "Europa": {"clasificados": ["España", "Francia", "Alemania", "Inglaterra", "Países Bajos", "Croacia", "Portugal", "Escocia", "Austria", "Bélgica", "Suiza", "Noruega"]},
    "África": {"clasificados": ["Sudáfrica", "Egipto", "Marruecos", "Argelia", "Costa de Marfil", "Ghana"]},
    "Asia": {"clasificados": ["Corea del Sur", "Japón", "Irán", "Australia", "Arabia Saudita", "Uzbekistán", "Qatar", "Jordania"]},
    "Norteamérica": {"clasificados": ["México", "Canadá", "Estados Unidos", "Panamá"]}
}

ODDS_API_KEY = "1928777e3a71509cabffaf3c507876ce"

def obtener_selecciones():
    if coleccion is None: return []
    return list(coleccion.find({}, {'_id': 0}))

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
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{font-family:'Segoe UI',Arial,sans-serif;background:#1a1a2e;color:white;padding:20px;}
        .container{max-width:1200px;margin:0 auto;}
        h1{text-align:center;color:#4CAF50;margin-bottom:10px;}
        .nav{text-align:center;margin-bottom:20px;}
        .nav a{color:#4CAF50;text-decoration:none;margin:0 10px;padding:8px 20px;background:#0f3460;border-radius:25px;display:inline-block;}
        .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px;margin-bottom:30px;}
        .card{background:#0f3460;padding:15px;border-radius:15px;text-align:center;}
        .card h3{font-size:2em;color:#4CAF50;}
        .flex{display:flex;gap:10px;flex-wrap:wrap;margin:15px 0;}
        select,button{padding:10px 20px;border-radius:25px;border:none;background:#0f3460;color:white;cursor:pointer;}
        button{background:#4CAF50;}
        .btn-blue{background:#2196F3;}
        .btn-orange{background:#FF9800;}
        .results{background:#0f3460;border-radius:15px;padding:20px;margin-top:15px;display:none;}
        .grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin:15px 0;}
        .stat-card{background:#1a1a2e;padding:15px;border-radius:10px;text-align:center;}
        .big-number{font-size:2em;font-weight:bold;color:#FFC107;}
        table{width:100%;background:#0f3460;border-radius:15px;border-collapse:collapse;}
        th,td{padding:10px;text-align:left;border-bottom:1px solid #1a1a2e;}
        th{background:#4CAF50;}
        @media (max-width:600px){.grid-3{grid-template-columns:1fr;}}
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
    
    <h2>🔮 Pronóstico</h2>
    <div class="flex">
        <select id="eqLocal"><option value="">Local</option>{% for s in selecciones %}<option>{{ s.nombre }}</option>{% endfor %}</select>
        <span>VS</span>
        <select id="eqVisitante"><option value="">Visitante</option>{% for s in selecciones %}<option>{{ s.nombre }}</option>{% endfor %}</select>
        <button class="btn-orange" onclick="calcularPronostico()">🔮 Calcular</button>
    </div>
    <div id="pronosticoResultado" class="results"></div>
    
    <h2>📊 Cuotas Tiempo Real</h2>
    <button class="btn-blue" onclick="cargarCuotas()">🔄 Actualizar</button>
    <div id="cuotasResultado" style="margin-top:15px;"></div>
    
    <h2>📋 Ranking</h2>
    <table><thead><tr><th>#</th><th>Selección</th><th>Jugadores</th><th>Goles</th><th>Rating</th></tr></thead><tbody>
    {% for s in selecciones %}
    <tr><td>{{ loop.index }}</td><td><strong>{{ s.nombre }}</strong></td><td>{{ s.jugadores }}</td><td>{{ s.goles_total }}</td><td>{{ s.rating_promedio }}</td></tr>
    {% endfor %}</tbody></table>
</div>

<script>
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
                div.innerHTML = `<div class="grid-3"><div class="stat-card"><div class="big-number">${data.local}%</div><div>🏠 ${local}</div></div>
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
        });
    }
</script>
</body>
</html>
"""

# ==================== PÁGINA JUGADORES ====================
HTML_JUGADOR = """
<!DOCTYPE html>
<html>
<head><title>Buscador de Jugadores</title><meta charset="UTF-8"><style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:'Segoe UI',Arial,sans-serif;background:#1a1a2e;color:white;padding:20px;}
    .container{max-width:600px;margin:0 auto;}
    h1{text-align:center;color:#4CAF50;margin-bottom:20px;}
    .nav{text-align:center;margin-bottom:20px;}
    .nav a{color:#4CAF50;text-decoration:none;margin:0 10px;padding:8px 20px;background:#0f3460;border-radius:25px;}
    .flex{display:flex;gap:10px;margin:20px 0;}
    input,button{padding:10px 20px;border-radius:25px;border:none;}
    input{background:#0f3460;color:white;flex:1;}
    button{background:#4CAF50;color:white;cursor:pointer;}
    .results{background:#0f3460;border-radius:15px;padding:20px;margin-top:20px;display:none;}
    .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:15px 0;}
    .card{background:#1a1a2e;padding:15px;border-radius:10px;text-align:center;}
    .card h3{font-size:2em;color:#4CAF50;}
</style>
</head>
<body>
<div class="container"><div class="nav"><a href="/">🏆 Ranking</a><a href="/jugador">🔍 Jugadores</a><a href="/eliminatorias">🌍 Eliminatorias</a></div>
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

# ==================== PÁGINA ELIMINATORIAS ====================
HTML_ELIMINATORIAS = """
<!DOCTYPE html>
<html>
<head><title>Eliminatorias - Mundial 2026</title><meta charset="UTF-8"><style>
    *{margin:0;padding:0;box-sizing:border-box;}
    body{font-family:'Segoe UI',Arial,sans-serif;background:#1a1a2e;color:white;padding:20px;}
    .container{max-width:800px;margin:0 auto;}
    h1{text-align:center;color:#4CAF50;margin-bottom:20px;}
    .nav{text-align:center;margin-bottom:20px;}
    .nav a{color:#4CAF50;text-decoration:none;margin:0 10px;padding:8px 20px;background:#0f3460;border-radius:25px;}
    .continente{background:#0f3460;border-radius:15px;padding:20px;margin-bottom:20px;}
    .continente h3{color:#4CAF50;margin-bottom:10px;}
    .badge{background:#1a1a2e;padding:10px;border-radius:10px;margin:5px 0;}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:10px 0;}
</style>
</head>
<body>
<div class="container"><div class="nav"><a href="/">🏆 Ranking</a><a href="/jugador">🔍 Jugadores</a><a href="/eliminatorias">🌍 Eliminatorias</a></div>
<h1>🌍 Eliminatorias por Continente</h1>
{% for continente, datos in eliminatorias.items() %}
<div class="continente"><h3>{{ continente }}</h3><div class="grid">
    {% for equipo in datos.clasificados %}<div class="badge">✅ {{ equipo }}</div>{% endfor %}
</div></div>
{% endfor %}
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
    return render_template_string(HTML_ELIMINATORIAS, eliminatorias=ELIMINATORIAS)

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

@app.route('/api/jugador/buscar')
def api_buscar_jugador():
    nombre = request.args.get('nombre', '').lower()
    for k, v in JUGADORES_MANUALES.items():
        if k in nombre or nombre in k:
            return jsonify(v)
    return jsonify({'error': 'No encontrado'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
