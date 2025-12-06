from flask import Flask, request, jsonify
import mysql.connector 
from datetime import datetime
import json 



app = Flask(__name__)


DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'iot'
}

GAS_ALARM_THRESHOLD = 500  

# Función de conexión a la BD
def get_db_connection():
    # Intenta la conexión
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        
        raise

# ==================================================================
# RUTAS DE AUTENTICACIÓN
# ==================================================================

@app.route('/register', methods=['POST'])
def register_user():
    """
    Ruta para registrar un nuevo usuario.
    Requiere: IDUser, Mail, FName, LName, Password.
    El campo IDDevice se deja NULL al inicio y se asigna después.
    """
    conn = None
    cursor = None 
    try:
        data = request.json
        # Validación
        required_fields = ["IDUser", "Mail", "FName", "LName", "Password"]
        if not all(field in data for field in required_fields):
            return jsonify({"success": False, "message": "Faltan campos obligatorios"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        id_user = data['IDUser']
        
        #verificar si el IDUser ya existe
        cursor.execute("SELECT IDUser FROM user WHERE IDUser = %s", (id_user,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": f"El ID de usuario '{id_user}' ya está registrado"}), 409

        # Insertar nuevo usuario. 
        insert_query = """
            INSERT INTO user (IDUser, Mail, FName, LName, Password, IDDevice)
            VALUES (%s, %s, %s, %s, %s, NULL) -- Se inserta NULL en IDDevice
        """
        user_data = (
            data['IDUser'], data['Mail'], data['FName'], data['LName'], data['Password']
        )
        
        cursor.execute(insert_query, user_data)
        conn.commit()
        
        return jsonify({"success": True, "message": "Usuario registrado exitosamente. Asigne un dispositivo al iniciar sesión."}), 201

    except mysql.connector.Error as err:
        print(f"Error de MySQL en registro: {err}")
        return jsonify({"success": False, "message": f"Error de base de datos: {err.msg}"}), 500
    except Exception as e:
        print(f"Error en registro: {e}")
        return jsonify({"success": False, "message": "Error interno del servidor"}), 500
    finally:
        if cursor: 
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@app.route('/login', methods=['POST'])
def login_user():
    """
    Ruta para iniciar sesión.
    Verifica IDUser y Password. Si es exitoso, retorna IDDevice.
    """
    conn = None
    cursor = None 
    try:
        data = request.json
        id_user = data.get('IDUser')
        password = data.get('password')

        if not id_user or not password:
            return jsonify({"success": False, "message": "Faltan ID de usuario o contraseña"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) 

        # Buscar el usuario por IDUser
        query = "SELECT IDUser, IDDevice, FName, LName, Mail, Password FROM user WHERE IDUser = %s"
        cursor.execute(query, (id_user,))
        user_row = cursor.fetchone()
        
        if user_row:
            # 1. Verificar la contraseña (
            if user_row['Password'] == password:
                # Retornar los datos necesarios para el frontend (Streamlit)
                nombre_completo = f"{user_row['FName']} {user_row['LName']}"
                
                current_device = user_row['IDDevice']
                if not current_device:
                   
                    cursor.execute("""
                        SELECT IDDevice FROM device 
                        WHERE IDDevice NOT IN (SELECT IDDevice FROM user WHERE IDDevice IS NOT NULL)
                        ORDER BY IDDevice ASC 
                        LIMIT 1
                    """)
                    unassigned_device = cursor.fetchone()

                    if unassigned_device:
                        new_device_id = unassigned_device['IDDevice']
                        # Asignar el dispositivo al usuario
                        update_query = "UPDATE user SET IDDevice = %s WHERE IDUser = %s"
                        cursor.execute(update_query, (new_device_id, id_user))
                        conn.commit()
                        current_device = new_device_id
                        print(f"Dispositivo {new_device_id} asignado automáticamente al usuario {id_user} durante el login.")

                
                return jsonify({
                    "success": True,
                    "message": "Inicio de sesión exitoso",
                    "usuario": user_row['IDUser'],
                    "nombre": nombre_completo,
                    "mail": user_row['Mail'],
                    "id_device": current_device 
                }), 200
            else:
                # Contraseña incorrecta
                return jsonify({"success": False, "message": "Contraseña incorrecta"}), 401
        else:
            # Usuario no encontrado
            return jsonify({"success": False, "message": "Usuario no encontrado"}), 404

    except mysql.connector.Error as err:
        print(f"Error de MySQL en login: {err}")
        return jsonify({"success": False, "message": f"Error de base de datos: {err.msg}"}), 500
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({"success": False, "message": "Error interno del servidor"}), 500
    finally:
        if cursor: # Cierra el cursor de forma segura
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# ==================================================================
# RUTAS DE DATOS DE SENSORES
# ==================================================================

@app.route('/datos', methods=['POST'])
def receive_data():
    conn = None
    cursor = None
    
    try:
      
        try:
            data = request.json
        except Exception:
            
            return jsonify({"status": "error", "message": "JSON inválido"}), 400
        
        # 1. Extraer la MAC base y lecturas
        mac_base = data.get('mac_base')
        lecturas = data.get('lecturas')
        
        if not mac_base or not lecturas:
            return jsonify({"status": "error", "message": "Faltan datos esenciales (mac_base/lecturas)"}), 400
            
        insert_data = []

        # 2. PROCESAR CADA LECTURA INDIVIDUALMENTE
        for lectura in lecturas:
            sensor_type = lectura.get('type')
            lecture_value = lectura.get('Lecture')
            timestamp_str = lectura.get('TimeStamp')
            id_suffix = lectura.get('id_suffix')
            is_alarm = False
            
            # ** CONSTRUCCIÓN DEL ID SENSOR ÚNICO **
            id_sensor_unico = mac_base + id_suffix
            
            # Lógica de Alarma para gas
            if sensor_type == 'gas':
                try:
                    
                    if lecture_value is not None and float(lecture_value) > GAS_ALARM_THRESHOLD:
                        is_alarm = True
                except (TypeError, ValueError):
                    
                    continue

            # Almacenar la tupla de inserción
            insert_data.append((mac_base, id_sensor_unico, sensor_type, lecture_value, timestamp_str, is_alarm))
            
        
        # 3. CONEXIÓN Y VERIFICACIÓN/REGISTRO DEL DISPOSITIVO
        if insert_data:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # A. Verificar si el IDDevice ya existe en la tabla 'device'
            cursor.execute("SELECT IDDevice FROM device WHERE IDDevice = %s", (mac_base,))
            device_exists = cursor.fetchone()
            
            # B. Si NO existe, lo registramos automáticamente Y lo asignamos a un usuario.
            if device_exists is None:
                print(f"Dispositivo nuevo detectado: {mac_base}. Registrando en la tabla 'device'.")
                
                # 1. Insertar en la tabla 'device'
                insert_device_query = "INSERT INTO device (IDDevice) VALUES (%s)"
                try:
                    cursor.execute(insert_device_query, (mac_base,)) 
                    conn.commit()
                    print(f"Dispositivo {mac_base} registrado exitosamente en la tabla 'device'.")
                except mysql.connector.Error as db_err_device:
                    print(f"Error al registrar dispositivo {mac_base} en 'device': {db_err_device}")
                    return jsonify({"status": "error", "message": f"Error al registrar dispositivo: {db_err_device.msg}"}), 500

                # 2. Asignar el nuevo IDDevice al usuario MÁS RECIENTE sin IDDevice
                # NOTA: Asumimos que la tabla 'user' tiene un campo de autoincremento (ID) 
                # o TimeStamp para determinar el más reciente. Aquí usamos un ORDER BY IDUser DESC 
                # asumiendo que IDUser es secuencial o lo más cercano a 'reciente'.
                # Si tienes un campo 'CreationDate' o 'ID' de autoincremento, úsalo.
                
               
                find_user_query = """
                    SELECT IDUser 
                    FROM user 
                    WHERE IDDevice IS NULL 
                    ORDER BY IDUser DESC 
                    LIMIT 1
                """
                cursor.execute(find_user_query)
                user_to_link = cursor.fetchone()
                
                if user_to_link:
                    id_user = user_to_link[0]
                    update_user_query = "UPDATE user SET IDDevice = %s WHERE IDUser = %s"
                    cursor.execute(update_user_query, (mac_base, id_user))
                    conn.commit()
                    print(f"Dispositivo {mac_base} ASIGNADO exitosamente al usuario más reciente sin dispositivo: {id_user}")
                else:
                    print(f"Dispositivo {mac_base} registrado, pero NO HAY usuarios sin dispositivo para asignar.")
            
            # C. Proseguir con la inserción de datos del sensor
            sql_query = "INSERT INTO sensor (IDDevice, IDSensor, type, Lecture, TimeStamp, alarm) VALUES (%s, %s, %s, %s, %s, %s)"
            
            # ejecutamos todos los datos recopilados en un solo lote
            cursor.executemany(sql_query, insert_data) 
            
            conn.commit()
            
            print(f"Datos insertados exitosamente del dispositivo base: {mac_base}")
            return jsonify({"status": "success", "message": "Datos insertados correctamente"}), 200
        else:
            return jsonify({"status": "error", "message": "No hay datos válidos para insertar"}), 400

    except mysql.connector.Error as db_err:
        print(f"Error de base de datos: {db_err}")
        return jsonify({"status": "error", "message": f"Error al insertar en la BD: {db_err.msg}"}), 500
    except Exception as e:
        print(f"Error inesperado en receive_data: {e}")
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500
    
    finally:
        if cursor: # Cierra el cursor de forma segura
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# ==================================================================
# RUTAS DE STREAMLIT
# ==================================================================

# ENDPOINT PARA STREAMLIT → DATOS EN TIEMPO REAL
@app.route('/api/realtime', methods=['GET'])
def api_realtime():
    """Obtiene los últimos 30 datos filtrados por tipo de sensor Y IDDevice."""
    conn = None
    cursor = None
    try:
        sensor_type = request.args.get("type", None)
        device_id = request.args.get("device_id", None) # Parámetro OBLIGATORIO para filtrar

        if not sensor_type or not device_id:
            return jsonify([]) # Devolver lista vacía si faltan parámetros

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Consulta SQL ACTUALIZADA para filtrar por IDDevice
        query = """
            SELECT TimeStamp, Lecture AS value
            FROM sensor
            WHERE type=%s AND IDDevice=%s
            ORDER BY TimeStamp DESC
            LIMIT 30
        """
        cursor.execute(query, (sensor_type, device_id)) # Se pasa IDDevice para el filtrado
        rows = cursor.fetchall()

        # Convertir objetos datetime a string ISO para JSON
        for row in rows:
            if isinstance(row['TimeStamp'], datetime):
                row['TimeStamp'] = row['TimeStamp'].isoformat()

        return jsonify(rows)

    except Exception as e:
        print("Error realtime:", e)
        return jsonify({"error": "Error al obtener datos"}), 500
    finally:
        if cursor: # Cierra el cursor de forma segura
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    
# ENDPOINT PARA STREAMLIT → CONSUMO GAS SEMANAL/MENSUAL
@app.route('/api/gas/<mode>', methods=['GET'])
def api_gas(mode):
    """Obtiene el consumo promedio de gas agrupado por día, filtrado por IDDevice."""
    conn = None
    cursor = None # Inicializado a None para un cierre seguro
    try:
        device_id = request.args.get("device_id", None) # Parámetro OBLIGATORIO para filtrar

        if not device_id:
            return jsonify([]) # Devolver lista vacía si falta el parámetro

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Base de la consulta, incluyendo IDDevice
        base_query = """
            SELECT DATE(TimeStamp) AS date,
                   AVG(Lecture) AS consumption
            FROM sensor
            WHERE type='gas' AND IDDevice=%s
        """
        
        # Filtro de tiempo
        if mode == "weekly":
            time_filter = "AND TimeStamp >= NOW() - INTERVAL 7 DAY"
        elif mode == "monthly":
            time_filter = "AND TimeStamp >= NOW() - INTERVAL 30 DAY"
        else:
            return jsonify({"error": "Modo de gas inválido. Use 'weekly' o 'monthly'"}), 400
        
        # Construcción final de la consulta
        query = f"""
            {base_query}
            {time_filter}
            GROUP BY DATE(TimeStamp)
            ORDER BY date ASC
        """
        
        cursor.execute(query, (device_id,)) # Se pasa IDDevice para el filtrado
        rows = cursor.fetchall()

        return jsonify(rows)

    except Exception as e:
        print("Error gas:", e)
        return jsonify({"error": "Error al obtener datos"}), 500
    finally:
        if cursor: # Cierra el cursor de forma segura
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# ==================================================================
# RUTAS DE ALARMAS (COMPATIBILIDAD CON GAS2.PY)
# ==================================================================

@app.route('/api/alarms', methods=['GET'])
def api_alarms():
    """
    Obtiene el historial de las últimas 50 alarmas de gas registradas
    para un dispositivo específico. Ideal para mostrar en Streamlit.
    """
    conn = None
    cursor = None
    try:
        device_id = request.args.get("device_id", None) 
        if not device_id:
            return jsonify({"error": "Falta el parámetro 'device_id'"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Consulta SQL para obtener lecturas donde 'alarm' sea True (1) y el tipo sea 'gas'
        query = """
            SELECT TimeStamp, IDSensor, Lecture AS value
            FROM sensor
            WHERE type='gas' AND alarm=1 AND IDDevice=%s
            ORDER BY TimeStamp DESC
            LIMIT 50
        """
        cursor.execute(query, (device_id,)) 
        rows = cursor.fetchall()

        # Convertir objetos datetime a string ISO para JSON
        for row in rows:
            if isinstance(row['TimeStamp'], datetime):
                row['TimeStamp'] = row['TimeStamp'].isoformat()
            # Renombrar para ser más legible en el frontend
            row['gas_ppm'] = row.pop('value')

        return jsonify(rows)

    except Exception as e:
        print("Error en api_alarms:", e)
        return jsonify({"error": "Error al obtener el historial de alarmas"}), 500
    finally:
        if cursor: 
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
   
  
