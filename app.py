import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import re

app = Flask(__name__)

# URI correcta para MongoDB Atlas
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://mundial_user:M4nzana2026@cluster666.tqvej0i.mongodb.net/?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true')

try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=15000)
    db = client['mundial_2026']
    coleccion_selecciones = db['selecciones']
    client.admin.command('ping')
    count = coleccion_selecciones.count_documents({})
    print(f"✅ Conectado a MongoDB Atlas: {count} selecciones")
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")
    coleccion_selecciones = None

# ==================== FUNCIONES ====================
def obtener_selecciones():
    if coleccion_selecciones is None: return []
    return sorted([doc for doc in coleccion_selecciones.find({}, {'_id': 0})], 
                  key=lambda x: x.get('rating_promedio', 0), reverse=True)

def obtener_seleccion(nombre):
    if coleccion_selecciones is None: return None
    return coleccion_selecciones.find_one({'nombre': nombre}, {'_id': 0})

def buscar_jugadores(termino):
    if coleccion_selecciones is None: return []
    resultados = []
    for sel in coleccion_selecciones.find({}, {'_id': 0}):
        for jug in sel.get('plantilla', []):
            if termino.lower() in jug.get('jugador', '').lower():
                resultados.append({'seleccion': sel['nombre'], 'jugador': jug['jugador'], 
                                   'goles': jug['goles'], 'asistencias': jug['asistencias'], 'rating': jug['rating']})
    return resultados

def lista_nombres():
    if coleccion_selecciones is None: return []
    return sorted([doc['nombre'] for doc in coleccion_selecciones.find({}, {'_id': 0, 'nombre': 1})])

# ==================== RUTAS ====================
@app.route('/')
def index():
    selecciones = obtener_selecciones()
    if not selecciones:
        return "<h1>⚠️ No hay datos en MongoDB</h1><p>Carga los datos desde el Excel primero.</p>"
    
    nombres = lista_nombres()
    
    html = """<!DOCTYPE html>
    <html>
    <head><title>Mundial 2026</title><script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; background: #1a1a2e; color: white; padding: 20px; }
        h1 { color: #4CAF50; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #333; }
        th { background: #4CAF50; }
        tr:hover { background: #2a2a3e; }
        a { color: #4CAF50; text-decoration: none; }
        .search-box, .comparador { margin: 20px 0; padding: 15px; background: #0f3460; border-radius: 10px; display: flex; gap: 10px; }
        .search-box input, .comparador select { flex: 1; padding: 10px; border-radius: 5px; }
        button { background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .card { background: #0f3460; border-radius: 10px; padding: 20px; }
        canvas { max-height: 300px; }
        .resultados-busqueda, .comparacion-container { margin-top: 20px; background: #0f3460; border-radius: 10px; padding: 15px; display: none; }
        .comparacion-grid { display: grid; grid-template-columns: 1fr auto 1fr; gap: 20px; margin-top: 20px; }
        .comparacion-equipo { background: #1a1a2e; padding: 15px; border-radius: 10px; }
        .vs { font-size: 24px; font-weight: bold; display: flex; align-items: center; justify-content: center; color: #FFC107; }
        .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; }
        .ganador { color: #4CAF50; font-weight: bold; }
    </style>
    <script>
        let rankingChart = null;
        function buscarJugador() {
            let termino = document.getElementById('searchInput').value;
            if (termino.length < 2) return alert("Mínimo 2 caracteres");
            fetch('/api/buscar?q=' + encodeURIComponent(termino))
                .then(r => r.json()).then(data => {
                    let div = document.getElementById('resultados');
                    if (data.length === 0) div.innerHTML = '<p>❌ No se encontraron resultados</p>';
                    else {
                        let html = '<h3>🔍 Resultados (' + data.length + ')</h3><table><thead><tr><th>Jugador</th><th>Selección</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>';
                        for (let j of data) html += `<tr><td><strong>${j.jugador}</strong></td><td>${j.seleccion}</td><td>${j.goles}</td><td>${j.asistencias}</td><td>${j.rating}</td></tr>`;
                        html += '</tbody></table>';
                        div.innerHTML = html;
                    }
                    document.getElementById('resultados-busqueda').style.display = 'block';
                });
        }
        function compararSelecciones() {
            let eq1 = document.getElementById('equipo1').value, eq2 = document.getElementById('equipo2').value;
            if (!eq1 || !eq2) return alert("Selecciona dos equipos");
            if (eq1 === eq2) return alert("Equipos diferentes");
            fetch(`/api/comparar?eq1=${encodeURIComponent(eq1)}&eq2=${encodeURIComponent(eq2)}`)
                .then(r => r.json()).then(data => {
                    let div = document.getElementById('comparacion');
                    let winner1 = data.equipo1.rating_promedio > data.equipo2.rating_promedio ? 'ganador' : '';
                    let winner2 = data.equipo2.rating_promedio > data.equipo1.rating_promedio ? 'ganador' : '';
                    let html = '<h3>⚔️ Comparación</h3><div class="comparacion-grid">';
                    html += `<div class="comparacion-equipo"><h4>${data.equipo1.nombre}</h4><div class="stat-row"><span>🏆 Rating</span><span class="${winner1}">${data.equipo1.rating_promedio}</span></div><div class="stat-row"><span>⚽ Goles</span><span>${data.equipo1.goles_total}</span></div><div class="stat-row"><span>⭐ Mejor</span><span>${data.equipo1.mejor_rating.nombre} (${data.equipo1.mejor_rating.valor})</span></div></div>`;
                    html += `<div class="vs">VS</div>`;
                    html += `<div class="comparacion-equipo"><h4>${data.equipo2.nombre}</h4><div class="stat-row"><span>🏆 Rating</span><span class="${winner2}">${data.equipo2.rating_promedio}</span></div><div class="stat-row"><span>⚽ Goles</span><span>${data.equipo2.goles_total}</span></div><div class="stat-row"><span>⭐ Mejor</span><span>${data.equipo2.mejor_rating.nombre} (${data.equipo2.mejor_rating.valor})</span></div></div>`;
                    html += '</div>';
                    div.innerHTML = html;
                    document.getElementById('comparacion-container').style.display = 'block';
                });
        }
        function cargarRanking() {
            fetch('/api/selecciones').then(r => r.json()).then(data => {
                let top10 = data.slice(0, 10);
                let ctx = document.getElementById('rankingChart').getContext('2d');
                if (rankingChart) rankingChart.destroy();
                rankingChart = new Chart(ctx, { type: 'bar', data: { labels: top10.map(t => t.nombre), datasets: [{ label: 'Rating', data: top10.map(t => t.rating_promedio), backgroundColor: 'rgba(76,175,80,0.7)' }] }, options: { responsive: true } });
            });
        }
        function cargarGoles() {
            fetch('/api/selecciones').then(r => r.json()).then(data => {
                let top10 = data.sort((a,b) => b.goles_total - a.goles_total).slice(0, 10);
                new Chart(document.getElementById('golesChart'), { type: 'bar', data: { labels: top10.map(t => t.nombre), datasets: [{ label: 'Goles', data: top10.map(t => t.goles_total), backgroundColor: 'rgba(33,150,243,0.7)' }] }, options: { responsive: true } });
            });
        }
        window.onload = () => { cargarRanking(); cargarGoles(); };
    </script>
    </head>
    <body>
        <h1>🏆 Mundial 2026</h1>
        <div class="grid-2"><div class="card"><canvas id="rankingChart"></canvas></div><div class="card"><canvas id="golesChart"></canvas></div></div>
        <div class="search-box"><input id="searchInput" placeholder="🔍 Buscar jugador"><button onclick="buscarJugador()">Buscar</button></div>
        <div class="comparador"><select id="equipo1"><option value="">Equipo 1</option>"""
    
    for n in nombres:
        html += f'<option value="{n}">{n}</option>'
    html += '</select><select id="equipo2"><option value="">Equipo 2</option>'
    for n in nombres:
        html += f'<option value="{n}">{n}</option>'
    html += f"""</select><button onclick="compararSelecciones()">Comparar</button></div>
        <div id="comparacion-container" class="comparacion-container"><div id="comparacion"></div></div>
        <div id="resultados-busqueda" class="resultados-busqueda"><div id="resultados"></div></div>
        <h2>📊 Ranking</h2><table><thead><tr><th>#</th><th>Selección</th><th>Jugadores</th><th>Goles</th><th>Rating</th></tr></thead><tbody>"""
    
    for i, s in enumerate(selecciones, 1):
        html += f'<tr><td>{i}</td><td><strong><a href="/seleccion/{s["nombre"]}">{s["nombre"]}</a></strong></td><td>{s["jugadores"]}</td><td>{s["goles_total"]}</td><td>{s["rating_promedio"]}</td></tr>'
    
    html += '</tbody></table></body></html>'
    return html


@app.route('/seleccion/<nombre>')
def ver_seleccion(nombre):
    s = obtener_seleccion(nombre)
    if not s: return "No encontrada", 404
    html = f"""
    <!DOCTYPE html>
    <html><head><title>{nombre}</title><style>
        body {{ font-family: Arial; background: #1a1a2e; color: white; padding: 20px; }}
        h1 {{ color: #4CAF50; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background: #4CAF50; }}
        .stats {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #0f3460; padding: 15px; border-radius: 10px; text-align: center; }}
        .stat-card h3 {{ font-size: 2em; margin: 0; color: #4CAF50; }}
        .btn {{ background: #4CAF50; color: white; padding: 10px; text-decoration: none; display: inline-block; margin-top: 20px; border-radius: 5px; }}
    </style></head>
    <body>
        <h1>🏆 {nombre}</h1>
        <div class="stats"><div class="stat-card"><h3>{s['jugadores']}</h3><p>Jugadores</p></div>
        <div class="stat-card"><h3>{s['goles_total']}</h3><p>Goles</p></div>
        <div class="stat-card"><h3>{s['asistencias_total']}</h3><p>Asistencias</p></div>
        <div class="stat-card"><h3>{s['rating_promedio']}</h3><p>Rating</p></div></div>
        <table><thead><tr><th>Jugador</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>"""
    for j in s['plantilla']:
        html += f'<tr><td>{j["jugador"]}</td><td>{j["goles"]}</td><td>{j["asistencias"]}</td><td>{j["rating"]}</td></tr>'
    html += '</tbody></table><a href="/" class="btn">← Volver</a></body></html>'
    return html

# API
@app.route('/api/selecciones')
def api_selecciones(): return jsonify(obtener_selecciones())
@app.route('/api/seleccion/<nombre>')
def api_seleccion_(nombre): return jsonify(obtener_seleccion(nombre) or {'error': 'No encontrada'})
@app.route('/api/buscar')
def api_buscar_(): return jsonify(buscar_jugadores(request.args.get('q', '')))
@app.route('/api/comparar')
def api_comparar_():
    eq1, eq2 = request.args.get('eq1'), request.args.get('eq2')
    if not eq1 or not eq2: return jsonify({'error': 'Se necesitan dos equipos'}), 400
    d1, d2 = obtener_seleccion(eq1), obtener_seleccion(eq2)
    if not d1 or not d2: return jsonify({'error': 'Equipo no encontrado'}), 404
    m1 = max(d1['plantilla'], key=lambda x: x['rating'])
    m2 = max(d2['plantilla'], key=lambda x: x['rating'])
    return jsonify({'equipo1': {'nombre': d1['nombre'], 'jugadores': d1['jugadores'], 'goles_total': d1['goles_total'], 'asistencias_total': d1['asistencias_total'], 'rating_promedio': d1['rating_promedio'], 'mejor_rating': {'nombre': m1['jugador'], 'valor': m1['rating']}}, 'equipo2': {'nombre': d2['nombre'], 'jugadores': d2['jugadores'], 'goles_total': d2['goles_total'], 'asistencias_total': d2['asistencias_total'], 'rating_promedio': d2['rating_promedio'], 'mejor_rating': {'nombre': m2['jugador'], 'valor': m2['rating']}}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)