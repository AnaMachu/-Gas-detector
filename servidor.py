from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# Función para conectar
def conectar_mysql():
    conexion = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='sensores_db'
    )
    return conexion

# Función para guardar
def guardar_en_mysql(sensor_id, temperatura, humedad, gas):
    conexion = conectar_mysql()
    cursor = conexion.cursor()
    
    query = """
    INSERT INTO lecturas_sensor 
    (sensor_id, temperatura, humedad, gas) 
    VALUES (%s, %s, %s, %s)
    """
    
    valores = (sensor_id, temperatura, humedad, gas)
    cursor.execute(query, valores)
    conexion.commit()
    
    cursor.close()
    conexion.close()

# Ruta que recibe datos del ESP32
@app.route('/api/sensor', methods=['POST'])
def recibir_datos():
    # 1. Obtener datos del JSON que envió ESP32
    datos = request.get_json()
    
    # 2. Extraer valores
    sensor_id = datos.get('sensor_id')
    temperatura = datos.get('temperatura')
    humedad = datos.get('humedad')
    gas = datos.get('gas')
    
    # 3. Guardar en MySQL
    guardar_en_mysql(sensor_id, temperatura, humedad, gas)
    
    # 4. Responder al ESP32
    return jsonify({'success': True, 'message': 'Datos guardados'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)pip install mysql-connector-python