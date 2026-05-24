import os
from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)

# URI de MongoDB Atlas (configurada en Render como variable de entorno)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://mundial_user:M4nzana2026@cluster666.tqvej0i.mongodb.net/?tls=true&tlsAllowInvalidCertificates=true&retryWrites=true&w=majority&appName=Cluster666')

try:
    client = MongoClient(MONGO_URI, 
                         tls=True,
                         tlsAllowInvalidCertificates=True,
                         tlsAllowInvalidHostnames=True,
                         serverSelectionTimeoutMS=15000)
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
    
    selecciones = list(coleccion.find({}, {'_id': 0}))
    
    if not selecciones:
        return "<h1>⚠️ No hay datos en MongoDB</h1>"
    
    html = "<h1>🏆 Mundial 2026 - Selecciones</h1><ul>"
    for s in selecciones:
        html += f"<li><strong>{s['nombre']}</strong> - {s['jugadores']} jugadores, {s['goles_total']} goles</li>"
    html += "</ul>"
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)