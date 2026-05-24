import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
import re

app = Flask(__name__)

# URI de MongoDB Atlas
MONGO_URI = "mongodb://mundial_user:M4nzana2026@ac-0tfmbvr-shard-00-00.tqvej0i.mongodb.net:27017,ac-0tfmbvr-shard-00-01.tqvej0i.mongodb.net:27017,ac-0tfmbvr-shard-00-02.tqvej0i.mongodb.net:27017/?ssl=true&replicaSet=atlas-fjc1fq-shard-0&authSource=admin&tlsAllowInvalidCertificates=true"

try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=15000)
    db = client['mundial_2026']
    coleccion = db['selecciones']
    count = coleccion.count_documents({})
    print(f"✅ Conectado a MongoDB Atlas: {count} selecciones")
except Exception as e:
    print(f"❌ Error: {e}")
    coleccion = None

def obtener_selecciones():
    if coleccion is None: return []
    return sorted([doc for doc in coleccion.find({}, {'_id': 0})], key=lambda x: x.get('rating_promedio', 0), reverse=True)

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

@app.route('/')
def index():
    selecciones = obtener_selecciones()
    if not selecciones:
        return "<h1>⚠️ No hay datos</h1>"
    
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mundial 2026 - Estadísticas</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #fff;
                min-height: 100vh;
            }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            
            .header {
                text-align: center;
                padding: 30px 20px;
                background: rgba(0,0,0,0.3);
                border-radius: 20px;
                margin-bottom: 30px;
            }
            .header h1 {
                font-size: 2.5em;
                background: linear-gradient(90deg, #4CAF50, #2196F3);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 10px;
            }
            .header p { color: #aaa; font-size: 1.1em; }
            
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
            
            .charts {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .chart-card {
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                padding: 20px;
            }
            .chart-card h3 { margin-bottom: 15px; color: #4CAF50; }
            canvas { max-height: 300px; }
            
            .search-section {
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 30px;
            }
            .search-box {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 10px;
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
            .search-box button {
                padding: 12px 30px;
                background: #4CAF50;
                border: none;
                border-radius: 25px;
                color: white;
                cursor: pointer;
                transition: background 0.3s;
            }
            .search-box button:hover { background: #45a049; }
            
            .results {
                margin-top: 20px;
                background: rgba(0,0,0,0.3);
                border-radius: 15px;
                padding: 20px;
                display: none;
            }
            .results table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            .results th, .results td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            .results th { background: #4CAF50; border-radius: 10px; }
            .results tr:hover { background: rgba(255,255,255,0.05); }
            
            .compare-section {
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 30px;
            }
            .compare-selects {
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
                margin-top: 15px;
                align-items: center;
            }
            .compare-selects select {
                flex: 1;
                padding: 12px;
                border-radius: 10px;
                border: none;
                background: rgba(255,255,255,0.1);
                color: white;
                font-size: 16px;
            }
            .compare-selects button {
                padding: 12px 30px;
                background: #2196F3;
                border: none;
                border-radius: 25px;
                color: white;
                cursor: pointer;
            }
            .compare-selects button:hover { background: #1976D2; }
            
            .ranking-section {
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                padding: 20px;
                overflow-x: auto;
            }
            .ranking-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            .ranking-table th, .ranking-table td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            .ranking-table th { background: #4CAF50; position: sticky; top: 0; }
            .ranking-table tr:hover { background: rgba(255,255,255,0.05); }
            .ranking-table button {
                background: #4CAF50;
                border: none;
                padding: 5px 15px;
                border-radius: 20px;
                cursor: pointer;
                color: white;
            }
            .rating-high { color: #4CAF50; font-weight: bold; }
            .rating-mid { color: #FFC107; font-weight: bold; }
            .rating-low { color: #f44336; }
            
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                z-index: 1000;
                justify-content: center;
                align-items: center;
            }
            .modal-content {
                background: #1a1a2e;
                border-radius: 20px;
                padding: 30px;
                max-width: 800px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
            }
            .modal-content h2 { color: #4CAF50; margin-bottom: 20px; }
            .modal-content .close {
                float: right;
                font-size: 28px;
                cursor: pointer;
                color: #aaa;
            }
            .modal-content .close:hover { color: white; }
            .modal-content table { width: 100%; border-collapse: collapse; }
            .modal-content th, .modal-content td { padding: 8px; text-align: left; border-bottom: 1px solid #333; }
            .modal-content th { background: #4CAF50; }
            
            @media (max-width: 768px) {
                .container { padding: 10px; }
                .header h1 { font-size: 1.8em; }
                .charts { grid-template-columns: 1fr; }
            }
        </style>
        <script>
            let rankingChart = null;
            let golesChart = null;
            
            function buscarJugador() {
                let termino = document.getElementById('searchInput').value;
                if (termino.length < 2) {
                    alert("Escribe al menos 2 caracteres");
                    return;
                }
                fetch('/api/buscar?q=' + encodeURIComponent(termino))
                    .then(r => r.json())
                    .then(data => {
                        let div = document.getElementById('resultados');
                        if (data.length === 0) {
                            div.innerHTML = '<p>❌ No se encontraron jugadores con "' + termino + '"</p>';
                        } else {
                            let html = '<h3>🔍 Resultados (' + data.length + ' jugadores)</h3>';
                            html += '<table><thead><tr><th>Jugador</th><th>Selección</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>';
                            for (let j of data) {
                                html += `<tr><td><strong>${j.jugador}</strong></td><td>${j.seleccion}</td><td>${j.goles}</td><td>${j.asistencias}</td><td>${j.rating}</td></tr>`;
                            }
                            html += '</tbody></table>';
                            div.innerHTML = html;
                        }
                        document.getElementById('resultados-busqueda').style.display = 'block';
                    });
            }
            
            function verSeleccion(nombre) {
                fetch('/api/seleccion/' + encodeURIComponent(nombre))
                    .then(r => r.json())
                    .then(data => {
                        if (data.error) return;
                        let html = '<span class="close" onclick="document.getElementById(\'modal\').style.display=\'none\'">&times;</span>';
                        html += '<h2>🏆 ' + data.nombre + '</h2>';
                        html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin:20px 0;">';
                        html += `<div style="background:#0f3460;padding:15px;border-radius:10px;"><h3>${data.jugadores}</h3><p>Jugadores</p></div>`;
                        html += `<div style="background:#0f3460;padding:15px;border-radius:10px;"><h3>${data.goles_total}</h3><p>Goles</p></div>`;
                        html += `<div style="background:#0f3460;padding:15px;border-radius:10px;"><h3>${data.asistencias_total}</h3><p>Asistencias</p></div>`;
                        html += `<div style="background:#0f3460;padding:15px;border-radius:10px;"><h3>${data.rating_promedio}</h3><p>Rating</p></div></div>`;
                        html += '<h3>📋 Plantilla</h3><table><thead><tr><th>Jugador</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>';
                        for (let j of data.plantilla) {
                            html += `<tr><td>${j.jugador}</td><td>${j.goles}</td><td>${j.asistencias}</td><td>${j.rating}</td></tr>`;
                        }
                        html += '</tbody></table>';
                        document.getElementById('modal-content').innerHTML = html;
                        document.getElementById('modal').style.display = 'flex';
                    });
            }
            
            function compararSelecciones() {
                let eq1 = document.getElementById('equipo1').value;
                let eq2 = document.getElementById('equipo2').value;
                if (!eq1 || !eq2) { alert("Selecciona dos equipos"); return; }
                if (eq1 === eq2) { alert("Selecciona equipos diferentes"); return; }
                
                fetch(`/api/comparar?eq1=${encodeURIComponent(eq1)}&eq2=${encodeURIComponent(eq2)}`)
                    .then(r => r.json())
                    .then(data => {
                        let winner1 = data.equipo1.rating_promedio > data.equipo2.rating_promedio ? 'ganador' : '';
                        let winner2 = data.equipo2.rating_promedio > data.equipo1.rating_promedio ? 'ganador' : '';
                        let html = '<h3>⚔️ Comparación</h3><div style="display:grid;grid-template-columns:1fr auto 1fr;gap:20px;margin-top:20px;">';
                        html += `<div style="background:#1a1a2e;padding:15px;border-radius:10px;"><h4 style="color:#4CAF50;text-align:center">${data.equipo1.nombre}</h4>`;
                        html += `<div style="display:flex;justify-content:space-between;padding:8px 0"><span>🏆 Rating</span><span class="${winner1}">${data.equipo1.rating_promedio}</span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;padding:8px 0"><span>⚽ Goles</span><span>${data.equipo1.goles_total}</span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;padding:8px 0"><span>🎯 Asistencias</span><span>${data.equipo1.asistencias_total}</span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;padding:8px 0"><span>⭐ Mejor Rating</span><span>${data.equipo1.mejor_rating.nombre} (${data.equipo1.mejor_rating.valor})</span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;padding:8px 0"><span>⚽ Máximo Goleador</span><span>${data.equipo1.max_goleador.nombre} (${data.equipo1.max_goleador.goles})</span></div></div>`;
                        html += '<div style="font-size:24px;display:flex;align-items:center;justify-content:center;color:#FFC107">VS</div>';
                        html += `<div style="background:#1a1a2e;padding:15px;border-radius:10px;"><h4 style="color:#4CAF50;text-align:center">${data.equipo2.nombre}</h4>`;
                        html += `<div style="display:flex;justify-content:space-between;padding:8px 0"><span>🏆 Rating</span><span class="${winner2}">${data.equipo2.rating_promedio}</span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;padding:8px 0"><span>⚽ Goles</span><span>${data.equipo2.goles_total}</span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;padding:8px 0"><span>🎯 Asistencias</span><span>${data.equipo2.asistencias_total}</span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;padding:8px 0"><span>⭐ Mejor Rating</span><span>${data.equipo2.mejor_rating.nombre} (${data.equipo2.mejor_rating.valor})</span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;padding:8px 0"><span>⚽ Máximo Goleador</span><span>${data.equipo2.max_goleador.nombre} (${data.equipo2.max_goleador.goles})</span></div></div>`;
                        html += '</div>';
                        document.getElementById('comparacion-resultado').innerHTML = html;
                        document.getElementById('comparacion-container').style.display = 'block';
                    });
            }
            
            function cargarGraficos() {
                fetch('/api/selecciones')
                    .then(r => r.json())
                    .then(data => {
                        let top10 = data.slice(0, 10);
                        let ctxRanking = document.getElementById('rankingChart').getContext('2d');
                        let ctxGoles = document.getElementById('golesChart').getContext('2d');
                        
                        if (rankingChart) rankingChart.destroy();
                        if (golesChart) golesChart.destroy();
                        
                        rankingChart = new Chart(ctxRanking, {
                            type: 'bar',
                            data: { labels: top10.map(t => t.nombre), datasets: [{ label: 'Rating Promedio', data: top10.map(t => t.rating_promedio), backgroundColor: 'rgba(76,175,80,0.7)', borderRadius: 10 }] },
                            options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: 'white' } } }, scales: { y: { ticks: { color: 'white' } }, x: { ticks: { color: 'white', rotation: 45 } } } }
                        });
                        
                        let topGoles = data.sort((a,b) => b.goles_total - a.goles_total).slice(0, 10);
                        golesChart = new Chart(ctxGoles, {
                            type: 'bar',
                            data: { labels: topGoles.map(t => t.nombre), datasets: [{ label: 'Goles Totales', data: topGoles.map(t => t.goles_total), backgroundColor: 'rgba(33,150,243,0.7)', borderRadius: 10 }] },
                            options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: 'white' } } }, scales: { y: { ticks: { color: 'white' } }, x: { ticks: { color: 'white', rotation: 45 } } } }
                        });
                    });
            }
            
            window.onload = () => { cargarGraficos(); };
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏆 Mundial 2026</h1>
                <p>Análisis estadístico de las 25 selecciones clasificadas</p>
            </div>
            
            <div class="stats-cards">
                <div class="stat-card"><h3>25</h3><p>Selecciones</p></div>
                <div class="stat-card"><h3>~650</h3><p>Jugadores</p></div>
                <div class="stat-card"><h3>📊</h3><p>Datos en tiempo real</p></div>
                <div class="stat-card"><h3>☁️</h3><p>MongoDB Atlas</p></div>
            </div>
            
            <div class="charts">
                <div class="chart-card"><h3>⭐ Top 10 - Rating Promedio</h3><canvas id="rankingChart"></canvas></div>
                <div class="chart-card"><h3>⚽ Top 10 - Goles Totales</h3><canvas id="golesChart"></canvas></div>
            </div>
            
            <div class="search-section">
                <h3>🔍 Buscar Jugador</h3>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Ej: Messi, Mbappé, Haaland...">
                    <button onclick="buscarJugador()">Buscar</button>
                </div>
                <div id="resultados-busqueda" class="results"><div id="resultados"></div></div>
            </div>
            
            <div class="compare-section">
                <h3>⚔️ Comparar Selecciones</h3>
                <div class="compare-selects">
                    <select id="equipo1"><option value="">Selecciona equipo 1</option>"""
    
    for s in selecciones:
        html += f'<option value="{s["nombre"]}">{s["nombre"]}</option>'
    
    html += '</select><select id="equipo2"><option value="">Selecciona equipo 2</option>'
    
    for s in selecciones:
        html += f'<option value="{s["nombre"]}">{s["nombre"]}</option>'
    
    html += """
                    </select>
                    <button onclick="compararSelecciones()">Comparar</button>
                </div>
                <div id="comparacion-container" class="results"><div id="comparacion-resultado"></div></div>
            </div>
            
            <div class="ranking-section">
                <h3>📊 Ranking de Selecciones</h3>
                <table class="ranking-table">
                    <thead>
                        <tr><th>#</th><th>Selección</th><th>Jugadores</th><th>Goles</th><th>Rating</th><th>Acción</th></tr>
                    </thead>
                    <tbody>
    """
    
    for i, s in enumerate(selecciones, 1):
        rating_class = 'rating-high' if s['rating_promedio'] >= 6.8 else ('rating-mid' if s['rating_promedio'] >= 6.5 else 'rating-low')
        html += f"""
                        <tr>
                            <td>{i}</td>
                            <td><strong>{s['nombre']}</strong></td>
                            <td>{s['jugadores']}</td>
                            <td>{s['goles_total']}</td>
                            <td class="{rating_class}">{s['rating_promedio']}</td>
                            <td><button onclick="verSeleccion('{s['nombre']}')">Ver</button></td>
                        </tr>
        """
    
    html += """
                    </tbody>
                </table>
            </div>
        </div>
        
        <div id="modal" class="modal">
            <div class="modal-content" id="modal-content"></div>
        </div>
        
        <script>
            document.getElementById('modal').onclick = function(e) {
                if (e.target === document.getElementById('modal')) {
                    document.getElementById('modal').style.display = 'none';
                }
            };
        </script>
    </body>
    </html>
    """
    return html

# ==================== API ENDPOINTS ====================
@app.route('/api/selecciones')
def api_selecciones():
    return jsonify(obtener_selecciones())

@app.route('/api/seleccion/<nombre>')
def api_seleccion(nombre):
    sel = obtener_seleccion(nombre)
    if not sel:
        return jsonify({'error': 'No encontrada'}), 404
    mejor_rating = max(sel['plantilla'], key=lambda x: x['rating'])
    max_goleador = max(sel['plantilla'], key=lambda x: x['goles'])
    return jsonify({
        'nombre': sel['nombre'],
        'jugadores': sel['jugadores'],
        'goles_total': sel['goles_total'],
        'asistencias_total': sel['asistencias_total'],
        'rating_promedio': sel['rating_promedio'],
        'plantilla': sel['plantilla'],
        'mejor_jugador': mejor_rating['jugador'],
        'mejor_rating': mejor_rating['rating'],
        'max_goleador': max_goleador['jugador'],
        'max_goles': max_goleador['goles']
    })

@app.route('/api/buscar')
def api_buscar():
    termino = request.args.get('q', '')
    return jsonify(buscar_jugadores(termino) if len(termino) >= 2 else [])

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
    max_gol1 = max(d1['plantilla'], key=lambda x: x['goles'])
    max_gol2 = max(d2['plantilla'], key=lambda x: x['goles'])
    return jsonify({
        'equipo1': {
            'nombre': d1['nombre'],
            'jugadores': d1['jugadores'],
            'goles_total': d1['goles_total'],
            'asistencias_total': d1['asistencias_total'],
            'rating_promedio': d1['rating_promedio'],
            'mejor_rating': {'nombre': mejor1['jugador'], 'valor': mejor1['rating']},
            'max_goleador': {'nombre': max_gol1['jugador'], 'goles': max_gol1['goles']}
        },
        'equipo2': {
            'nombre': d2['nombre'],
            'jugadores': d2['jugadores'],
            'goles_total': d2['goles_total'],
            'asistencias_total': d2['asistencias_total'],
            'rating_promedio': d2['rating_promedio'],
            'mejor_rating': {'nombre': mejor2['jugador'], 'valor': mejor2['rating']},
            'max_goleador': {'nombre': max_gol2['jugador'], 'goles': max_gol2['goles']}
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)