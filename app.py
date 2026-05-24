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
    <title>Mundial 2026</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a2e;
            color: white;
            padding: 20px;
            margin: 0;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #4CAF50; text-align: center; }
        .card {
            background: #0f3460;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .search-box input {
            flex: 1;
            padding: 10px;
            border-radius: 5px;
            border: none;
            font-size: 16px;
            min-width: 200px;
        }
        .search-box button, .compare-btn, .ver-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
        }
        .compare-btn { background: #2196F3; }
        .ver-btn { background: #FF9800; padding: 5px 10px; font-size: 12px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            overflow-x: auto;
            display: block;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #333;
        }
        th { background: #4CAF50; }
        tr:hover { background: #1a1a3e; }
        .results {
            background: #0f3460;
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
            display: none;
            overflow-x: auto;
        }
        .compare-selects {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }
        .compare-selects select {
            padding: 10px;
            border-radius: 5px;
            background: #1a1a2e;
            color: white;
            border: 1px solid #4CAF50;
            flex: 1;
            min-width: 150px;
        }
        .ganador { color: #4CAF50; font-weight: bold; }
        .plantilla-container {
            background: #0f3460;
            border-radius: 10px;
            padding: 15px;
            margin-top: 10px;
            overflow-x: auto;
        }
        .close-btn {
            background: #f44336;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 10px;
        }
        @media (max-width: 600px) {
            th, td { font-size: 12px; padding: 5px; }
            .search-box button, .compare-btn { padding: 8px 16px; font-size: 12px; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>🏆 Mundial 2026 - Estadísticas</h1>
    <p style="text-align:center">Datos: {{ total_selecciones }} selecciones | {{ total_jugadores }} jugadores</p>
    
    <!-- Buscador -->
    <div class="card">
        <h3>🔍 Buscar Jugador</h3>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Ej: Messi, Mbappé...">
            <button onclick="buscarJugador()">Buscar</button>
        </div>
        <div id="resultadosBusqueda" class="results"></div>
    </div>
    
    <!-- Comparador -->
    <div class="card">
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
    
    <!-- Tabla de ranking -->
    <div class="card">
        <h3>📊 Ranking de Selecciones</h3>
        <table>
            <thead>
                <tr><th>#</th><th>Selección</th><th>Jugadores</th><th>Goles</th><th>Rating</th><th>Acción</th></tr>
            </thead>
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
    function buscarJugador() {
        let termino = document.getElementById('searchInput').value;
        if (termino.length < 2) {
            alert("Escribe al menos 2 caracteres");
            return;
        }
        
        fetch('/api/buscar?q=' + encodeURIComponent(termino))
            .then(response => response.json())
            .then(data => {
                let div = document.getElementById('resultadosBusqueda');
                if (data.length === 0) {
                    div.innerHTML = '<p>❌ No se encontraron jugadores con "' + termino + '"</p>';
                } else {
                    let html = '<h4>✅ Resultados (' + data.length + ')</h4>';
                    html += '<table><thead><tr><th>Jugador</th><th>Selección</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>';
                    for (let j of data) {
                        html += '<tr>';
                        html += '<td><strong>' + j.jugador + '</strong></td>';
                        html += '<td>' + j.seleccion + '</td>';
                        html += '<td>' + j.goles + '</td>';
                        html += '<td>' + j.asistencias + '</td>';
                        html += '<td>' + j.rating + '</td>';
                        html += '</tr>';
                    }
                    html += '</tbody></table>';
                    div.innerHTML = html;
                }
                div.style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al buscar jugadores');
            });
    }
    
    function verSeleccion(nombre) {
        fetch('/api/seleccion/' + encodeURIComponent(nombre))
            .then(response => response.json())
            .then(data => {
                let html = '<button class="close-btn" onclick="cerrarPlantilla()">Cerrar</button>';
                html += '<h2>🏆 ' + data.nombre + '</h2>';
                html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:15px 0;">';
                html += '<div style="background:#1a1a2e;padding:10px;border-radius:8px;text-align:center"><h3>' + data.jugadores + '</h3><p>Jugadores</p></div>';
                html += '<div style="background:#1a1a2e;padding:10px;border-radius:8px;text-align:center"><h3>' + data.goles_total + '</h3><p>Goles</p></div>';
                html += '<div style="background:#1a1a2e;padding:10px;border-radius:8px;text-align:center"><h3>' + data.asistencias_total + '</h3><p>Asistencias</p></div>';
                html += '<div style="background:#1a1a2e;padding:10px;border-radius:8px;text-align:center"><h3>' + data.rating_promedio + '</h3><p>Rating</p></div></div>';
                html += '<h3>📋 Plantilla</h3>';
                html += '<div class="plantilla-container">';
                html += '<table><thead><tr><th>Jugador</th><th>Goles</th><th>Asistencias</th><th>Rating</th></tr></thead><tbody>';
                for (let j of data.plantilla) {
                    html += '<tr><td>' + j.jugador + '</td><td>' + j.goles + '</td><td>' + j.asistencias + '</td><td>' + j.rating + '</td></tr>';
                }
                html += '</tbody></table></div>';
                
                let modalDiv = document.getElementById('resultadosBusqueda');
                modalDiv.innerHTML = html;
                modalDiv.style.display = 'block';
                
                // Scroll al top
                window.scrollTo({ top: 0, behavior: 'smooth' });
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al cargar la selección');
            });
    }
    
    function cerrarPlantilla() {
        document.getElementById('resultadosBusqueda').style.display = 'none';
        document.getElementById('resultadosBusqueda').innerHTML = '';
    }
    
    function comparar() {
        let eq1 = document.getElementById('equipo1').value;
        let eq2 = document.getElementById('equipo2').value;
        if (!eq1 || !eq2) {
            alert("Selecciona dos equipos");
            return;
        }
        if (eq1 === eq2) {
            alert("Selecciona equipos diferentes");
            return;
        }
        
        fetch('/api/comparar?eq1=' + encodeURIComponent(eq1) + '&eq2=' + encodeURIComponent(eq2))
            .then(response => response.json())
            .then(data => {
                let winner1 = data.equipo1.rating_promedio > data.equipo2.rating_promedio ? 'ganador' : '';
                let winner2 = data.equipo2.rating_promedio > data.equipo1.rating_promedio ? 'ganador' : '';
                
                let html = '<button class="close-btn" onclick="cerrarComparacion()">Cerrar</button>';
                html += '<div style="display:grid;grid-template-columns:1fr auto 1fr;gap:15px;">';
                
                // Equipo 1
                html += '<div style="background:#1a1a2e;padding:15px;border-radius:10px;">';
                html += '<h3 style="text-align:center;color:#4CAF50">' + data.equipo1.nombre + '</h3>';
                html += '<div style="margin:10px 0"><strong>🏆 Rating:</strong> <span class="' + winner1 + '">' + data.equipo1.rating_promedio + '</span></div>';
                html += '<div><strong>⚽ Goles:</strong> ' + data.equipo1.goles_total + '</div>';
                html += '<div><strong>🎯 Asistencias:</strong> ' + data.equipo1.asistencias_total + '</div>';
                html += '<div><strong>⭐ Mejor:</strong> ' + data.equipo1.mejor_rating.nombre + ' (' + data.equipo1.mejor_rating.valor + ')</div>';
                html += '<div><strong>⚽ Goleador:</strong> ' + data.equipo1.max_goleador.nombre + ' (' + data.equipo1.max_goleador.goles + ')</div>';
                html += '</div>';
                
                // VS
                html += '<div style="font-size:30px;display:flex;align-items:center;">VS</div>';
                
                // Equipo 2
                html += '<div style="background:#1a1a2e;padding:15px;border-radius:10px;">';
                html += '<h3 style="text-align:center;color:#4CAF50">' + data.equipo2.nombre + '</h3>';
                html += '<div style="margin:10px 0"><strong>🏆 Rating:</strong> <span class="' + winner2 + '">' + data.equipo2.rating_promedio + '</span></div>';
                html += '<div><strong>⚽ Goles:</strong> ' + data.equipo2.goles_total + '</div>';
                html += '<div><strong>🎯 Asistencias:</strong> ' + data.equipo2.asistencias_total + '</div>';
                html += '<div><strong>⭐ Mejor:</strong> ' + data.equipo2.mejor_rating.nombre + ' (' + data.equipo2.mejor_rating.valor + ')</div>';
                html += '<div><strong>⚽ Goleador:</strong> ' + data.equipo2.max_goleador.nombre + ' (' + data.equipo2.max_goleador.goles + ')</div>';
                html += '</div>';
                
                html += '</div>';
                
                document.getElementById('comparacionResultado').innerHTML = html;
                document.getElementById('comparacionResultado').style.display = 'block';
                
                // Scroll al top
                window.scrollTo({ top: 0, behavior: 'smooth' });
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al comparar selecciones');
            });
    }
    
    function cerrarComparacion() {
        document.getElementById('comparacionResultado').style.display = 'none';
        document.getElementById('comparacionResultado').innerHTML = '';
    }
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
