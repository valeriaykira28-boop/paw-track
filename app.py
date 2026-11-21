from flask import Flask, request, jsonify, render_template
import sqlite3
import re
from datetime import datetime
import os

app = Flask(__name__)
DB_NAME = "pawtrack.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ubicaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitud REAL NOT NULL,
            longitud REAL NOT NULL,
            mensaje_original TEXT,
            fecha_hora TEXT NOT NULL
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM ubicaciones')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO ubicaciones (latitud, longitud, mensaje_original, fecha_hora)
            VALUES (?, ?, ?, ?)
        ''', (13.7013, -89.2244, "Ubicación inicial (UFG San Salvador)", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

init_db()

def extraer_coordenadas(texto_sms):
    coordenadas = re.findall(r'-?\d+\.\d+', texto_sms)
    if len(coordenadas) >= 2:
        return float(coordenadas[0]), float(coordenadas[1])
    return None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ubicaciones', methods=['GET'])
def obtener_ubicaciones():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, latitud, longitud, mensaje_original, fecha_hora FROM ubicaciones ORDER BY id DESC LIMIT 20')
    filas = cursor.fetchall()
    conn.close()
    
    lista = []
    for fila in filas:
        lista.append({
            "id": fila[0],
            "lat": fila[1],
            "lon": fila[2],
            "mensaje": fila[3],
            "fecha": fila[4]
        })
    return jsonify(lista)

@app.route('/api/recibir-sms', methods=['POST'])
def recibir_sms():
    data = request.get_json(silent=True) or request.form
    texto_sms = data.get('mensaje') or data.get('Body') or data.get('text') or ""
    
    lat, lon = extraer_coordenadas(texto_sms)
    
    if lat is not None and lon is not None:
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ubicaciones (latitud, longitud, mensaje_original, fecha_hora)
            VALUES (?, ?, ?, ?)
        ''', (lat, lon, texto_sms, fecha_actual))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "lat": lat, "lon": lon, "mensaje": "Ubicación actualizada"}), 200
    else:
        return jsonify({"status": "error", "mensaje": "No se encontraron coordenadas válidas en el SMS"}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

    
