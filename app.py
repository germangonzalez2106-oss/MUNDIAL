import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from pymongo import MongoClient
import re

# ==================== CONFIGURACIÓN ====================
app = Flask(__name__)

# ==================== CONEXIÓN A MONGODB ATLAS ====================
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://mundial_user:M4nzana_3*@cluster666.tqvej0i.mongodb.net/?retryWrites=true&w=majority')
NOMBRE_DB = "mundial_2026"
NOMBRE_COLECCION = "selecciones"

try:
    client = MongoClient(MONGO_URI)
    db = client[NOMBRE_DB]
    coleccion_selecciones = db[NOMBRE_COLECCION]
    client.admin.command('ping')
    print("✅ Conectado a MongoDB Atlas correctamente")
    print(f"📊 Selecciones en BD: {coleccion_selecciones.count_documents({})}")
except Exception as e:
    print(f"❌ Error conectando a MongoDB Atlas: {e}")

# ==================== FUNCIONES ====================
def obtener_selecciones_desde_mongodb():
    selecciones = []
    for doc in coleccion_selecciones.find({}, {'_id': 0}):
        selecciones.append(doc)
    return sorted(selecciones, key=lambda x: x.get('rating_promedio', 0), reverse=True)

def obtener_seleccion_por_nombre(nombre):
    return coleccion_selecciones.find_one({'nombre': nombre}, {'_id': 0})

def buscar_jugadores(termino):
    resultados = []
    for seleccion in coleccion_selecciones.find({}, {'_id': 0}):
        for jugador in seleccion.get('plantilla', []):
            if termino.lower() in jugador.get('jugador', '').lower():
                resultados.append({
                    'seleccion': seleccion['nombre'],
                    'jugador': jugador['jugador'],
                    'goles': jugador['goles'],
                    'asistencias': jugador['asistencias'],
                    'rating': jugador['rating']
                })
    return resultados

def obtener_lista_nombres_selecciones():
    nombres = []
    for doc in coleccion_selecciones.find({}, {'_id': 0, 'nombre': 1}):
        nombres.append(doc['nombre'])
    return sorted(nombres)

# ==================== RUTAS ====================
@app.route('/')
def index():
    try:
        selecciones = obtener_selecciones_desde_mongodb()
    except:
        selecciones = []
    
    if not selecciones:
        return "<h1>⚠️ Error: No se encontraron datos</h1>"
    
    nombres_selecciones = obtener_lista_nombres_selecciones()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mundial 2026</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: #1a1a2e; 
                color: white; 
                padding: 20px; 
            }
            h1, h2 { color: #4CAF50; }
            .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
            .card { background: #0f3460; border-radius: 10px; padding: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #333; }
            th { background: #4CAF50; }
            tr:hover { background: #2a2a3e; }
            a { color: #4CAF50; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .search-box, .comparador {
                margin: 20px 0; padding: 15px; background: #0f3460; border-radius: 10px;
                display: flex; gap: 10px; flex-wrap: wrap;
            }
            .search-box input, .comparador select {
                flex: 1; padding: 10px; border: none; border-radius: 5px;
                font-size: 16px; min-width: 200px;
            }
            .search-box button, .comparador button {
                background: #4CAF50; color: white; border: none;
                padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 16px;
            }
            .comparador button { background: #2196F3; }
            .comparador button:hover { background: #1976D2; }
            .resultados-busqueda, .comparacion-container {
                margin-top: 20px; background: #0f3460; border-radius: 10px;
                padding: 15px; display: none;
            }
            .resultados-busqueda h3, .comparacion-container h3 { margin-top: 0; color: #4CAF50; }
            .comparacion-grid { display: grid; grid-template-columns: 1fr auto 1fr; gap: 20px; margin-top: 20px; }
            .comparacion-equipo { background: #1a1a2e; padding: 15px; border-radius: 10px; }
            .comparacion-equipo h4 { text-align: center; color: #4CAF50; }
            .vs { font-size: 24px; font-weight: bold; display: flex; align-items: center; justify-content: center; color: #FFC107; }
            .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; }
            .ganador { color: #4CAF50; font-weight: bold; }
            canvas { max-height: 300px; }
        </style>
        <script>
            let rankingChart = null;
            
            function buscarJugador() {
                let termino = document.getElementById('searchInput').value;
                if (termino.length < 2) { alert("Escribe al menos 2 caracteres"); return; }
                
                fetch('/api/buscar?q=' + encodeURIComponent(termino))
                    .then(response => response.json())
                    .then(data => {
                        let resultadosDiv = document.getElementById('resultados');
                        if (data.length === 0) {
                            resultadosDiv.innerHTML = '<p>❌ No se encontraron jugadores con "' + termino + '"</p>';
                        } else {
                            let html = '<h3>🔍 Resultados (' + data.length + ' jugadores)</h3>';
                            html += '<table style="width:100%; margin-top:10px;"><thead><tr><th>Jugador</th><th>Selección</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>';
                            for (let j of data) {
                                html += '<tr><td><strong>' + j.jugador + '</strong></td><td>' + j.seleccion + '</td><td>' + j.goles + '</td><td>' + j.asistencias + '</td><td>' + j.rating + '</td></tr>';
                            }
                            html += '</tbody></table>';
                            resultadosDiv.innerHTML = html;
                        }
                        document.getElementById('resultados-busqueda').style.display = 'block';
                    });
            }
            
            function compararSelecciones() {
                let eq1 = document.getElementById('equipo1').value;
                let eq2 = document.getElementById('equipo2').value;
                if (!eq1 || !eq2) { alert("Selecciona dos equipos para comparar"); return; }
                if (eq1 === eq2) { alert("Selecciona dos equipos diferentes"); return; }
                
                fetch('/api/comparar?eq1=' + encodeURIComponent(eq1) + '&eq2=' + encodeURIComponent(eq2))
                    .then(response => response.json())
                    .then(data => {
                        let div = document.getElementById('comparacion');
                        let html = '<h3>⚔️ Comparación: ' + data.equipo1.nombre + ' vs ' + data.equipo2.nombre + '</h3>';
                        html += '<div class="comparacion-grid">';
                        html += '<div class="comparacion-equipo"><h4>' + data.equipo1.nombre + '</h4>';
                        html += '<div class="stat-row"><span>🏆 Rating Promedio</span><span class="' + (data.equipo1.rating_promedio > data.equipo2.rating_promedio ? 'ganador' : '') + '">' + data.equipo1.rating_promedio + '</span></div>';
                        html += '<div class="stat-row"><span>⚽ Goles Totales</span><span class="' + (data.equipo1.goles_total > data.equipo2.goles_total ? 'ganador' : '') + '">' + data.equipo1.goles_total + '</span></div>';
                        html += '<div class="stat-row"><span>🎯 Asistencias</span><span class="' + (data.equipo1.asistencias_total > data.equipo2.asistencias_total ? 'ganador' : '') + '">' + data.equipo1.asistencias_total + '</span></div>';
                        html += '<div class="stat-row"><span>👥 Jugadores</span><span>' + data.equipo1.jugadores + '</span></div>';
                        html += '<div class="stat-row"><span>⭐ Mejor Rating</span><span>' + data.equipo1.mejor_rating.nombre + ' (' + data.equipo1.mejor_rating.valor + ')</span></div>';
                        html += '<div class="stat-row"><span>⚽ Máximo Goleador</span><span>' + data.equipo1.max_goleador.nombre + ' (' + data.equipo1.max_goleador.goles + ' goles)</span></div></div>';
                        html += '<div class="vs">VS</div>';
                        html += '<div class="comparacion-equipo"><h4>' + data.equipo2.nombre + '</h4>';
                        html += '<div class="stat-row"><span>🏆 Rating Promedio</span><span class="' + (data.equipo2.rating_promedio > data.equipo1.rating_promedio ? 'ganador' : '') + '">' + data.equipo2.rating_promedio + '</span></div>';
                        html += '<div class="stat-row"><span>⚽ Goles Totales</span><span class="' + (data.equipo2.goles_total > data.equipo1.goles_total ? 'ganador' : '') + '">' + data.equipo2.goles_total + '</span></div>';
                        html += '<div class="stat-row"><span>🎯 Asistencias</span><span class="' + (data.equipo2.asistencias_total > data.equipo1.asistencias_total ? 'ganador' : '') + '">' + data.equipo2.asistencias_total + '</span></div>';
                        html += '<div class="stat-row"><span>👥 Jugadores</span><span>' + data.equipo2.jugadores + '</span></div>';
                        html += '<div class="stat-row"><span>⭐ Mejor Rating</span><span>' + data.equipo2.mejor_rating.nombre + ' (' + data.equipo2.mejor_rating.valor + ')</span></div>';
                        html += '<div class="stat-row"><span>⚽ Máximo Goleador</span><span>' + data.equipo2.max_goleador.nombre + ' (' + data.equipo2.max_goleador.goles + ' goles)</span></div></div>';
                        html += '</div>';
                        div.innerHTML = html;
                        document.getElementById('comparacion-container').style.display = 'block';
                    });
            }
            
            function cargarRankingChart() {
                fetch('/api/selecciones')
                    .then(response => response.json())
                    .then(data => {
                        let top10 = data.slice(0, 10);
                        let ctx = document.getElementById('rankingChart').getContext('2d');
                        if (rankingChart) { rankingChart.destroy(); }
                        rankingChart = new Chart(ctx, {
                            type: 'bar',
                            data: { labels: top10.map(t => t.nombre), datasets: [{ label: 'Rating Promedio', data: top10.map(t => t.rating_promedio), backgroundColor: 'rgba(76, 175, 80, 0.7)', borderColor: 'rgba(76, 175, 80, 1)', borderWidth: 1 }] },
                            options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: 'white' } }, title: { display: true, text: 'Top 10 - Rating Promedio', color: 'white' } }, scales: { y: { title: { display: true, text: 'Rating', color: 'white' }, ticks: { color: 'white' } }, x: { ticks: { color: 'white', rotation: 45, font: { size: 10 } } } } }
                        });
                    });
            }
            
            function cargarGolesChart() {
                fetch('/api/selecciones')
                    .then(response => response.json())
                    .then(data => {
                        let top10 = data.sort((a,b) => b.goles_total - a.goles_total).slice(0, 10);
                        let ctx = document.getElementById('golesChart').getContext('2d');
                        new Chart(ctx, {
                            type: 'bar',
                            data: { labels: top10.map(t => t.nombre), datasets: [{ label: 'Goles Totales', data: top10.map(t => t.goles_total), backgroundColor: 'rgba(33, 150, 243, 0.7)', borderColor: 'rgba(33, 150, 243, 1)', borderWidth: 1 }] },
                            options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: 'white' } }, title: { display: true, text: 'Top 10 - Goles Totales', color: 'white' } }, scales: { y: { title: { display: true, text: 'Goles', color: 'white' }, ticks: { color: 'white' } }, x: { ticks: { color: 'white', rotation: 45, font: { size: 10 } } } } }
                        });
                    });
            }
            
            window.onload = function() { cargarRankingChart(); cargarGolesChart(); };
        </script>
    </head>
    <body>
        <h1>🏆 Mundial 2026 - Análisis Estadístico</h1>
        <p>Datos almacenados en <strong>MongoDB Atlas ☁️</strong> | Total: """ + str(len(selecciones)) + """ selecciones</p>
        
        <div class="grid-2">
            <div class="card"><canvas id="rankingChart"></canvas></div>
            <div class="card"><canvas id="golesChart"></canvas></div>
        </div>
        
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Buscar jugador (ej: Messi, Mbappé, Haaland, etc.)">
            <button onclick="buscarJugador()">Buscar</button>
        </div>
        
        <div class="comparador">
            <select id="equipo1"><option value="">Selecciona equipo 1</option>
    """
    
    for nombre in nombres_selecciones:
        html += f'<option value="{nombre}">{nombre}</option>\n'
    
    html += """
            </select>
            <span>vs</span>
            <select id="equipo2"><option value="">Selecciona equipo 2</option>
    """
    
    for nombre in nombres_selecciones:
        html += f'<option value="{nombre}">{nombre}</option>\n'
    
    html += """
            </select>
            <button onclick="compararSelecciones()">Comparar</button>
        </div>
        
        <div id="comparacion-container" class="comparacion-container"><div id="comparacion"></div></div>
        <div id="resultados-busqueda" class="resultados-busqueda"><div id="resultados"></div></div>
        
        <h2>📊 Ranking de Selecciones</h2>
        <table><thead><tr><th>#</th><th>Selección</th><th>Jugadores</th><th>Goles</th><th>Rating</th></tr></thead><tbody>
    """
    
    for i, seleccion in enumerate(selecciones, 1):
        html += f'<tr><td>{i}</td><td><strong><a href="/seleccion/{seleccion["nombre"]}">{seleccion["nombre"]}</a></strong></td><td>{seleccion["jugadores"]}</td><td>{seleccion["goles_total"]}</td><td>{seleccion["rating_promedio"]}</td></tr>'
    
    html += """
        </tbody>
    </table>
    </body>
    </html>
    """
    
    return html


@app.route('/seleccion/<nombre>')
def ver_seleccion(nombre):
    seleccion = obtener_seleccion_por_nombre(nombre)
    if not seleccion:
        return f"<h1>Error: Selección '{nombre}' no encontrada</h1>", 404
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>{nombre} - Mundial 2026</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: white; padding: 20px; }}
        h1 {{ color: #4CAF50; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background: #4CAF50; }}
        tr:hover {{ background: #2a2a3e; }}
        .btn {{ display: inline-block; background: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
        .btn:hover {{ background: #45a049; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #0f3460; padding: 15px; border-radius: 10px; text-align: center; }}
        .stat-card h3 {{ font-size: 2em; margin: 0; color: #4CAF50; }}
    </style>
    </head>
    <body>
        <h1>🏆 {nombre}</h1>
        <div class="stats">
            <div class="stat-card"><h3>{seleccion['jugadores']}</h3><p>Jugadores</p></div>
            <div class="stat-card"><h3>{seleccion['goles_total']}</h3><p>Goles Totales</p></div>
            <div class="stat-card"><h3>{seleccion['asistencias_total']}</h3><p>Asistencias</p></div>
            <div class="stat-card"><h3>{seleccion['rating_promedio']}</h3><p>Rating Promedio</p></div>
        </div>
        <h2>📋 Plantilla de Jugadores</h2>
        <tr><thead><tr><th>Jugador</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>
    """
    
    for jugador in seleccion['plantilla']:
        html += f"<tr><td>{jugador['jugador']}</td><td>{jugador['goles']}</td><td>{jugador['asistencias']}</td><td>{jugador['rating']}</td></tr>"
    
    html += """
        </tbody>
    </table>
    <a href="/" class="btn">← Volver al ranking</a>
    </body>
    </html>
    """
    
    return html


# ==================== API REST ====================
@app.route('/api/selecciones')
def api_selecciones():
    try:
        return jsonify(obtener_selecciones_desde_mongodb())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/seleccion/<nombre>')
def api_seleccion(nombre):
    seleccion = obtener_seleccion_por_nombre(nombre)
    if seleccion:
        return jsonify(seleccion)
    return jsonify({'error': 'Selección no encontrada'}), 404

@app.route('/api/buscar')
def api_buscar():
    termino = request.args.get('q', '')
    if len(termino) < 2:
        return jsonify([])
    return jsonify(buscar_jugadores(termino))

@app.route('/api/comparar')
def api_comparar():
    eq1_nombre = request.args.get('eq1', '')
    eq2_nombre = request.args.get('eq2', '')
    
    if not eq1_nombre or not eq2_nombre:
        return jsonify({'error': 'Se necesitan dos equipos'}), 400
    
    eq1 = obtener_seleccion_por_nombre(eq1_nombre)
    eq2 = obtener_seleccion_por_nombre(eq2_nombre)
    
    if not eq1 or not eq2:
        return jsonify({'error': 'Equipo no encontrado'}), 404
    
    mejor_eq1 = max(eq1['plantilla'], key=lambda x: x['rating'])
    mejor_eq2 = max(eq2['plantilla'], key=lambda x: x['rating'])
    max_gol_eq1 = max(eq1['plantilla'], key=lambda x: x['goles'])
    max_gol_eq2 = max(eq2['plantilla'], key=lambda x: x['goles'])
    
    return jsonify({
        'equipo1': {
            'nombre': eq1['nombre'],
            'jugadores': eq1['jugadores'],
            'goles_total': eq1['goles_total'],
            'asistencias_total': eq1['asistencias_total'],
            'rating_promedio': eq1['rating_promedio'],
            'mejor_rating': {'nombre': mejor_eq1['jugador'], 'valor': mejor_eq1['rating']},
            'max_goleador': {'nombre': max_gol_eq1['jugador'], 'goles': max_gol_eq1['goles']}
        },
        'equipo2': {
            'nombre': eq2['nombre'],
            'jugadores': eq2['jugadores'],
            'goles_total': eq2['goles_total'],
            'asistencias_total': eq2['asistencias_total'],
            'rating_promedio': eq2['rating_promedio'],
            'mejor_rating': {'nombre': mejor_eq2['jugador'], 'valor': mejor_eq2['rating']},
            'max_goleador': {'nombre': max_gol_eq2['jugador'], 'goles': max_gol_eq2['goles']}
        }
    })

# ==================== EJECUCIÓN ====================
if __name__ == '__main__':
    print("="*50)
    print("🏆 MUNDIAL 2026 - APP CON GRÁFICOS")
    print("="*50)
    print("☁️ Base de datos: MongoDB Atlas (Cloud)")
    print("🌐 Abre http://localhost:5000")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=10000)