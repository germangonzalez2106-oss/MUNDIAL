import os
from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)

# URI correcta (usa la que funciona)
MONGO_URI = "mongodb://mundial_user:M4nzana2026@ac-0tfmbvr-shard-00-00.tqvej0i.mongodb.net:27017,ac-0tfmbvr-shard-00-01.tqvej0i.mongodb.net:27017,ac-0tfmbvr-shard-00-02.tqvej0i.mongodb.net:27017/?ssl=true&replicaSet=atlas-fjc1fq-shard-0&authSource=admin&tlsAllowInvalidCertificates=true"

try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
    db = client['mundial_2026']
    coleccion = db['selecciones']
    count = coleccion.count_documents({})
    print(f"✅ Conectado a MongoDB Atlas: {count} selecciones")
except Exception as e:
    print(f"❌ Error: {e}")
    coleccion = None

@app.route('/')
def index():
    if coleccion is None:
        return "<h1>Error: No hay conexión a MongoDB</h1>"
    
    # Obtener todas las selecciones
    selecciones = list(coleccion.find({}, {'_id': 0}))
    
    if not selecciones:
        return "<h1>⚠️ No hay datos en MongoDB</h1><p>La conexión funciona pero la colección está vacía.</p>"
    
    # Generar HTML simple con las selecciones
    html = "<h1>🏆 Mundial 2026 - Selecciones</h1><ul>"
    for s in selecciones:
        html += f"<li><strong>{s['nombre']}</strong> - {s['jugadores']} jugadores, {s['goles_total']} goles, rating: {s['rating_promedio']}</li>"
    html += "</ul>"
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)