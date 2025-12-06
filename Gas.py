import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import streamlit.components.v1 as components

# URL del backend Flask - CORREGIDO AL PUERTO CORRECTO
API_URL = "http://localhost:5000"

st.set_page_config(
    page_title="Sistema IoT - Monitoreo de Gas", 
    page_icon="🔐",
    layout="wide"
)

# Inicialización de la sesión de Streamlit
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'auth_option' not in st.session_state:
    st.session_state['auth_option'] = "Iniciar Sesión" 
if 'id_device' not in st.session_state:
    st.session_state['id_device'] = None # Inicializa IDDevice como None
if "alert_already_ack" not in st.session_state:
    st.session_state.alert_already_ack = False
if "show_alert_popup" not in st.session_state:
    st.session_state.show_alert_popup = False
if 'last_alert_time' not in st.session_state:
    st.session_state.last_alert_time = None
if 'alert_cooldown' not in st.session_state:
    st.session_state.alert_cooldown = False


def pagina_registro():
    st.title("Crear :green[Cuenta] 📝")
    st.write("Completa la información para registrar un nuevo usuario.")

    with st.form("registro_form"):
      
        id_user = st.text_input("ID de Usuario (Debe ser único)", max_chars=15)
        mail = st.text_input("Correo Electrónico")
        fname = st.text_input("Primer Nombre")
        lname = st.text_input("Apellido")
        password = st.text_input("Contraseña", max_chars=10, type="password")

        submit = st.form_submit_button("Registrar Usuario", use_container_width=True)

    if submit:
        if not all([id_user, mail, fname, lname, password]):
            st.warning("⚠️ Todos los campos son obligatorios.")
            return

        payload = {
            "IDUser": id_user,
            "Mail": mail,
            "FName": fname,
            "LName": lname,
            "Password": password
        }

        try:
            with st.spinner("Registrando usuario..."):
             
                response = requests.post(f"{API_URL}/register", json=payload, timeout=5) 
            
            data = response.json()

            if data.get("success"):
                st.success("✅ Usuario registrado correctamente. Serás redirigido a Iniciar Sesión.")
                st.session_state["auth_option"] = "Iniciar Sesión" 
                st.balloons()
                st.rerun() #
            else:
            
                st.error(f"❌ {data.get('message', 'No se pudo registrar el usuario. Verifique el ID de Usuario.')}")
        
        except requests.exceptions.ConnectionError:
            st.error("🔌 No se pudo conectar al servidor Flask. Verifique API_URL.")
        except requests.exceptions.Timeout:
            st.error("⏱️ Tiempo de espera agotado.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ===========================
# PÁGINA DE LOGIN
# ===========================
def pagina_login():
    st.title("Iniciar :red[Sesión] 🔐")
    st.write("Ingresa tu ID de usuario y contraseña para continuar.")
    
    with st.form("login_form"):
        id_user = st.text_input("ID del Usuario", placeholder="Ejemplo: 1")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar sesión", use_container_width=True)
    
    if submit:
        if not id_user or not password:
            st.warning("⚠️ Por favor completa todos los campos")
            return
        
        try:
            with st.spinner("Verificando credenciales..."):
                
                response = requests.post(
                    f"{API_URL}/login",
                    json={"IDUser": id_user, "password": password},
                    timeout=5
                )
            
            data = response.json()
            
            if data.get("success"):
                # Guardar datos del usuario en la sesión
                st.session_state["logged_in"] = True
                st.session_state["id_user"] = data.get("usuario")
                st.session_state["nombre_completo"] = data.get("nombre")
                st.session_state["mail"] = data.get("mail")
                
                st.session_state["id_device"] = data.get("id_device") 
                
                st.success(f"✅ Bienvenido {data.get('nombre')} 🎉")
                st.balloons()
                st.rerun() 
            else:
                st.error(f"❌ {data.get('message', 'ID de usuario o contraseña incorrectos.')}")
        
        except requests.exceptions.ConnectionError:
            st.error("🔌 No se pudo conectar al servidor. Verifica que Flask esté corriendo.")
        except requests.exceptions.Timeout:
            st.error("⏱️ Tiempo de espera agotado")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


# ===========================
# FUNCIONES DEL DASHBOARD 
# ===========================


st.markdown("""
<style>
    .main {
        background: white;
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: black;
        margin-bottom: 0.2rem;
    }
    .emergency-card {
        background: linear-gradient(135deg, #E88989 0%, #D96F6F 100%);
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin: 10px 0;
    }
    .metric-card {
    background: white;
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #A7C7E7; /* azul pastel */
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.info-box {
    background: #A7C7E7; /* verde pastel */
    padding: 15px;
    border-radius: 8px;
    border-left: 3px solid #A7C7E7; /* azul pastel */
    margin: 10px 0;
    color: black;
}

    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Fondo oscuro detrás del popup */
.alert-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.65);
    z-index: 998;
}

/* Caja del popup */
.alert-popup {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 60%;
    max-width: 500px;
    background: #b91c1c; /* Rojo fuerte */
    color: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    text-align: center;
    z-index: 999;
    animation: popup-fade 0.3s ease-out;
}

@keyframes popup-fade {
    from { opacity: 0; scale: 0.9; }
    to   { opacity: 1; scale: 1; }
}

/* Botón */
.alert-close-button {
    background: white;
    color: #b91c1c;
    border: none;
    margin-top: 15px;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    font-size: 1rem;
}
.alert-close-button:hover {
    background: #fef2f2;
}
</style>
""", unsafe_allow_html=True)


#logo
st.image("Imagen de WhatsApp 2025-11-25 a las 07.44.11_472dd4f8 - Editado.png", width=200)
st.sidebar.image("Imagen de WhatsApp 2025-11-25 a las 07.44.11_472dd4f8 - Editado.png", width=200)

# Lógica de las funciones del dashboard
API_DASHBOARD = "http://localhost:5000/api" 
def generate_realtime_data(sensor_type):
    """Descarga los últimos 30 datos de un tipo de sensor (gas, humedad, temperatura)
        asociados al IDDevice del usuario logueado."""
   
    device_id = st.session_state.get("id_device")
    if not device_id:
        
        return pd.DataFrame({
            "TimeStamp": [datetime.now() - timedelta(minutes=i) for i in range(30)], 
            "value": [0.0] * 30
        })

    try:
      
        r = requests.get(f"{API_DASHBOARD}/realtime?type={sensor_type}&device_id={device_id}")
        r.raise_for_status() 
        data = r.json()

        timestamps = [item["TimeStamp"] for item in data]
        values = [item["value"] for item in data]

        df = pd.DataFrame({
            "TimeStamp": pd.to_datetime(timestamps),
            "value": values
        })

        return df

    except Exception as e:
        st.info(f"Advertencia: No se pudieron obtener datos del dispositivo {device_id}. Error: {e}")
        
        return pd.DataFrame({
            "TimeStamp": [datetime.now() - timedelta(minutes=i) for i in range(30)], 
            "value": [0.0] * 30
        })
        
def generate_gas_data(mode='weekly'):
    """Genera datos de consumo de gas."""
    device_id = st.session_state.get("id_device")
    if not device_id:
        days = 7 if mode == 'weekly' else 30
        dates = [datetime.now() - timedelta(days=i) for i in range(days)]
        labels = [d.strftime("%d") for d in dates]
        return pd.DataFrame({
            'date': dates,
            'label': labels,
            'consumption': [0.0] * days
        }).sort_values(by='date')

    try:
        r = requests.get(f"{API_DASHBOARD}/gas/{mode}?device_id={device_id}")
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df["label"] = df["date"].dt.strftime("%d")
        df["consumption"] = df["consumption"].astype(float)
        return df
    except Exception as e:
        st.info(f"Advertencia: No se pudieron obtener datos de consumo para {mode}. Error: {e}")
        
        days = 7 if mode == 'weekly' else 30
        dates = [datetime.now() - timedelta(days=i) for i in range(days)]
        labels = [d.strftime("%d") for d in dates]
        return pd.DataFrame({
            'date': dates,
            'label': labels,
            'consumption': [0.0] * days
        }).sort_values(by='date')

# Header
def render_header(user_name):
    col1, col2 = st.columns([4, 1])
    with col1:
        # Usamos el nombre del usuario logueado
        st.markdown(f'<div class="header-title">Hola, {user_name}</div>', unsafe_allow_html=True)
        st.markdown(f"**{datetime.now().strftime('%d de %B, %Y - %H:%M')}**")
    with col2:
        if st.button("🔔", help="Notificaciones"):
            st.toast("No hay nuevas notificaciones", icon="ℹ️")

# Gráfica en tiempo real
def render_realtime_chart():
    st.markdown("### Monitoreo de Gas en Tiempo Real (PPM)")
    
    data = generate_realtime_data("gas")
    latest_value = data["value"].iloc[-1] if len(data) > 0 else 0
    GAS_LIMIT = 79

    
    st.markdown(f"**DEBUG** - Device: `{st.session_state.get('id_device')}`, Última lectura: **{latest_value}** PPM, Límite: {GAS_LIMIT}")

    
    current_time = datetime.now()
    
    if latest_value > GAS_LIMIT:
       
        if (st.session_state.last_alert_time is None or 
            (current_time - st.session_state.last_alert_time).total_seconds() > 30):
            
            if not st.session_state.alert_already_ack:
                st.session_state.show_alert_popup = True
                st.session_state.last_alert_time = current_time 
    else:
        # Si el nivel baja del límite, resetear los estados
        st.session_state.alert_already_ack = False
        st.session_state.show_alert_popup = False
        st.session_state.alert_cooldown = False

    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['TimeStamp'],
        y=data['value'],
        mode='lines',
        name='PPM',
        line=dict(color="#C8A2C8", width=3),   
        fill='tozeroy',
        fillcolor='rgba(200, 162, 200, 0.4)'
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(
            title=dict(text="Tiempo",font=dict(color="#000000") ),
            showgrid=True,
           gridcolor='#e5e7eb',
            tickfont=dict(color='#000000'),
        ),
        yaxis=dict(
            title=dict(text="Concentración (PPM)",font=dict(color="#000000") ),
            showgrid=True,
            gridcolor='#e5e7eb',
            color= '#000000',
            tickfont=dict(color='#000000'),
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True, key="realtime")

# Gráfica de consumo de gas
def render_gas_chart():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Consumo Histórico de Gas")
    with col2:
        view_mode = st.selectbox(
            "Vista", 
            ["Semanal", "Mensual"],
            key='view_mode',
            label_visibility="collapsed"
        )
    
    current_mode = 'weekly' if view_mode == "Semanal" else 'monthly'
    data = generate_gas_data(current_mode)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data['label'],
        y=data['consumption'],
         marker_color="#AFC3D1",         
         marker_line_color="#8FA6B8", 
        marker_line_width=1.5,
        text=data['consumption'].round(1),
        texttemplate='%{text}',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Consumo: %{y:.1f} m³<extra></extra>'
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(
            title="",
            showgrid=False,
            tickfont=dict(color='#000000'),
        ),
        yaxis=dict(
            title=dict(text="Consumo (m³)", font=dict(color='#000000')),
            showgrid=True,
            gridcolor='#e5e7eb',
            tickfont=dict(color='#000000'),
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True, key="gas")
    return current_mode

# Resumen con métricas
def render_weekly_summary(view_mode):
    period = "Semanal" if view_mode == 'weekly' else "Mensual"
    st.markdown(f"### Resumen {period}")
    
    col1, col2 = st.columns(2)
    
   
    with col1:
          st.markdown("""
        <div class="metric-card">
            <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Pico Máximo</p>
            <h2 style="margin: 10px 0; color: #1e293b;">42.3 m³</h2>
            <p style="color: #ef4444; margin: 0; font-size: 0.85rem;">⚠️ Día viernes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Promedio Diario</p>
            <h2 style="margin: 10px 0; color: #1e293b;">26.5 m³</h2>
            <p style="color: #6b7280; margin: 0; font-size: 0.85rem;">Dentro del rango normal</p>
        </div>
        """, unsafe_allow_html=True)
    
# Contacto de emergencia
def render_emergency_contact():
    st.markdown("""
    <div class="emergency-card">
        <h3 style="margin-top: 0;"> Contacto de Emergencia</h3>
        <h1 style="font-size: 2.5rem; margin: 15px 0;">  911</h1>
        <p style="margin-top: 15px; font-size: 1rem;">
            En caso de fuga de gas o emergencia, llame inmediatamente.
        </p>
        <hr style="border-color: rgba(255,255,255,0.3); margin: 20px 0;">
        <p style="margin: 10px 0; font-size: 0.95rem;">
            <strong>⚠️ Señales de alerta:</strong>
        </p>
        <ul style="margin: 10px 0; padding-left: 20px;">
            <li>Olor a gas o huevo podrido</li>
            <li>Llama amarilla o naranja en lugar de azul</li>
            <li>Manchas de hollín en electrodomésticos</li>
            <li>Aire viciado o dificultad para respirar</l>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚨 Marcar Emergencia", type="primary", use_container_width=True):
        st.warning("⚠️ En una emergencia real, marque 911 directamente desde su teléfono")

# Mapa de ubicación
def render_location_map():
    id_device = st.session_state.get('id_device', 'No Asignado')
    st.markdown("### 📍 Ubicación del Medidor")
    
    # Coordenadas de ejemplo (no usadas si el dispositivo no está asignado)
    if id_device and id_device != 'No Asignado':
        map_data = pd.DataFrame({
            'lat': [20.5471],
            'lon': [-100.4389]
        })
        st.map(map_data, zoom=13, use_container_width=True)
        address_html = """
        Av. Principal #123<br>
        El Pueblito, Querétaro, México
        """
    else:
        st.warning("⚠️ Dispositivo no asignado. La ubicación no está disponible.")
        # Se usa un mapa vacío o placeholder si no hay dispositivo asignado
        st.empty() 
        address_html = "Aún no se recibe la ubicación del dispositivo."
    
    # Muestra el ID del dispositivo, sea asignado o no
    st.markdown(f"""
    <div class="info-box">
        <strong>📍 ID Dispositivo:</strong> {id_device}<br>
        <strong>📍 Dirección:</strong>
        {address_html}
    </div>
    """, unsafe_allow_html=True)



def render_gas_alert_popup():
    if not st.session_state.get("show_alert_popup", False):
        return

    # CSS para el popup que cubre toda la pantalla
    st.markdown("""
    <style>
    .alert-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.65);
        z-index: 9998;
    }
    
    .alert-popup {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 60%;
        max-width: 500px;
        background: #b91c1c;
        color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        text-align: center;
        z-index: 9999;
        animation: popup-fade 0.3s ease-out;
    }
    
    @keyframes popup-fade {
        from { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
        to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
    }
    
    /* Asegurarse de que el popup esté por encima de todo */
    .main > div {
        z-index: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # HTML del popup
    st.markdown("""
    <div class="alert-overlay"></div>
    <div class="alert-popup">
        <h2>🚨 ALERTA DE GAS</h2>
        <p>Se ha detectado una concentración peligrosa de gas.</p>
        <p><b>¡Evacúe de inmediato!</b></p>
        <p><small>Esta alerta se cerrará automáticamente en 3 segundos</small></p>
    </div>
    """, unsafe_allow_html=True)

    # Botón invisible para el cierre automático
    close_placeholder = st.empty()
    
    # Cierre automático después de 3 segundos
    import time
    time.sleep(3)
    
    if st.session_state.get("show_alert_popup", False):
        st.session_state.show_alert_popup = False
        st.session_state.alert_already_ack = True
        st.session_state.last_alert_time = datetime.now()
        close_placeholder.empty()
        st.rerun()






# Botón de prueba para forzar la alerta (solo para desarrollo)
if st.sidebar.button("FORZAR ALERTA (test)", key="force_alert_test"):
    st.session_state["show_alert_popup"] = True
    st.rerun()

# Aplicación principal del Dashboard
def main_dashboard():
    user_name = st.session_state.get('nombre_completo', 'Usuario Desconocido')
    render_header(user_name)

    st.markdown("<br>", unsafe_allow_html=True)

        
    if st.session_state.get("show_alert_popup", False):
      
        js_listener = """
        <script>
        window.addEventListener('message', function(event) {
            if (event.data === 'close_alert') {
                // Enviar click al botón de Streamlit
                const streamlitDoc = window.parent.document;
                const buttons = Array.from(streamlitDoc.querySelectorAll('button'));
                const closeButton = buttons.find(button => 
                    button.innerText.includes('cerrar') || 
                    button.id.includes('close_alert_trigger')
                );
                if (closeButton) {
                    closeButton.click();
                }
            }
        });
        </script>
        """
        components.html(js_listener, height=0)

  
    if st.session_state.get('id_device') is None:
        st.error(f"❌ Dispositivo no asociado. Hola {user_name}, tu cuenta ha sido registrada pero aún no se ha asociado a un medidor de gas.")
        st.info("Para completar la configuración, por favor, enciende tu dispositivo IoT. El sistema lo asociará automáticamente a tu cuenta en cuanto reciba los primeros datos.")

        col_side = st.columns([1])[0]
        with col_side:
            render_emergency_contact()
            render_location_map()
    else:
        # layout principal con columnas
        col_main, col_side = st.columns([2, 1], gap="large")

        with col_main:
            render_realtime_chart()   
            st.markdown("<br>", unsafe_allow_html=True)
            view_mode = render_gas_chart()
            st.markdown("<br>", unsafe_allow_html=True)
            render_weekly_summary(view_mode)

        
        with col_side:
            render_emergency_contact()
            st.markdown("<br>", unsafe_allow_html=True)
            render_location_map()

       
        render_gas_alert_popup()

    # footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #6b7280; padding: 20px;">
        <p>Dashboard de Monitoreo de Gas • Dispositivo: {st.session_state.get('id_device', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Cerrar Sesión", type="secondary", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["auth_option"] = "Iniciar Sesión"
        st.rerun()



if not st.session_state["logged_in"]:
    
    opcion = st.radio(
        "Selecciona una opción:",
        ["Iniciar Sesión", "Registrar Usuario"],
        index=0 if st.session_state["auth_option"] == "Iniciar Sesión" else 1, # Fija el index
        horizontal=True,
        key="auth_selection" # Usamos una key para el radio button
    )
    st.session_state["auth_option"] = opcion 

    if opcion == "Iniciar Sesión":
        pagina_login()
    else:
        pagina_registro()
else:
    # Muestra el dashboard si el usuario está logueado
    main_dashboard()
    
  
        
 


       
