import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

# URL del backend Flask - Debe apuntar al endpoint /api
API_URL = "http://localhost:5000/api"

# ==========================================================
# 1. VERIFICACIÓN DE AUTENTICACIÓN 
# ==========================================================

# Si el usuario no está logueado, se le avisa y se termina la ejecución de esta página.
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.title("Acceso Denegado 🛑")
    st.warning("Debes iniciar sesión para acceder a esta página. Por favor, vuelve a la página principal para autenticarte.")
    st.stop() # Detiene la ejecución de la página
    
# Si la ejecución continúa, el usuario está autenticado.
DEVICE_ID = st.session_state.get('id_device', 'default_device')
USER_NAME = st.session_state.get('nombre_completo', 'Usuario')


st.set_page_config(
    page_title="Sistema IoT - Otros Sensores", 
    page_icon="🌡️",
    layout="wide"
)

st.markdown("""
<style>
    .main {
        background: white;
    }
    .tips-for-kitchen {
        background: #5A8F8A;
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin: 10px 0;
    }
    .standard {
        background: white;
        padding: 10px;
        border-radius: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

#logo
st.image("Imagen de WhatsApp 2025-11-25 a las 07.44.11_472dd4f8 - Editado.png", width=200)
st.sidebar.image("Imagen de WhatsApp 2025-11-25 a las 07.44.11_472dd4f8 - Editado.png", width=200)

st.title(f"Métricas de Humedad y Temperatura para {USER_NAME}")
st.markdown(f"**Dispositivo Asignado:** `{DEVICE_ID}`")

# ==========================================================
# 2. FUNCIONES
# ==========================================================

@st.cache_data(ttl=5) # Cachea los datos por 5 segundos
def get_sensor_data(sensor_type, device_id):
    """
    Descarga los últimos 30 datos de un tipo de sensor y filtra por IDDevice.
    """
    try:
        r = requests.get(f"{API_URL}/realtime?type={sensor_type}&device_id={device_id}")
        r.raise_for_status() 
        data = r.json()

        if not data:
            st.info(f"Advertencia: No se encontraron datos de '{sensor_type}' para el dispositivo `{device_id}`.")
            return pd.DataFrame({"TimeStamp": [], "value": []})


        timestamps = [item["TimeStamp"] for item in data]
        values = [item["value"] for item in data]

        df = pd.DataFrame({
            "TimeStamp": pd.to_datetime(timestamps),
            "value": values
        }).sort_values(by="TimeStamp") 
        return df

    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP al obtener datos: {http_err}. Código: {r.status_code}")
        return pd.DataFrame({"TimeStamp": [], "value": []})
    except requests.exceptions.ConnectionError:
        st.error("🔌 Error de conexión. Asegúrate que el servidor Flask está corriendo en el puerto 5000.")
        return pd.DataFrame({"TimeStamp": [], "value": []})
    except Exception as e:
        st.error(f"Error inesperado al obtener datos: {e}")
        return pd.DataFrame({"TimeStamp": [], "value": []})


def humchart():  # Humedad gráfica de líneas
    st.markdown("### Monitoreo de Humedad en Tiempo Real (%)")
    data = get_sensor_data("hum", DEVICE_ID)

    if data.empty:
        st.warning("No hay datos de Humedad para mostrar.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['TimeStamp'],
        y=data['value'],
        mode='lines',
        name='Medición',
        line=dict(color="#B5EAD7", width=3),         
        fill='tozeroy',
        fillcolor='rgba(181, 234, 215, 0.3)' 
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(
            title=dict(text="Tiempo", font=dict(color="#000000")),
            showgrid=True,
            gridcolor='#e5e7eb',
            tickfont=dict(color='#000000'),
        ),
        yaxis=dict(
            title=dict(text="Valor (%)", font=dict(color="#000000")), 
            showgrid=True,
            gridcolor='#e5e7eb',
            color='#000000',
            tickfont=dict(color='#000000'),
            range=[0, 100] # porcentaje de humedad
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True, key="humedad_realtime")


def humstandard(view_mode):
    st.markdown("### Rangos de Humedad")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="standard">
            <p style="color: #71be00; margin: 0; font-size: 0.9rem;">Hum. Baja</p>
            <h2 style="margin: 10px 0; color: #71be00;"> &lt;30% </h2>
            
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="standard">
            <p style="color: #ffbe00; margin: 0; font-size: 0.9rem;">Hum. Ideal</p>
            <h2 style="margin: 10px 0; color: #ffbe00;">30-50%</h2>
            <p style="color: #ffbe00; margin: 0; font-size: 0.85rem;">Dentro del rango normal</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="standard">
            <p style="color: #b20000; margin: 0; font-size: 0.9rem;">Hum. Alta</p>
            <h2 style="margin: 10px 0; color:#b20000;"> &gt;50% </h2>
        </div>
        """, unsafe_allow_html=True)


def tempchart():  # Temperatura gráfica de líneas
    st.markdown("### Monitoreo de Temperatura en Tiempo Real (°C)")
    
    data = get_sensor_data("temp", DEVICE_ID)

    if data.empty:
        st.warning("No hay datos de Temperatura para mostrar.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['TimeStamp'],
        y=data['value'],
        mode='lines',
        name='Medición',
        line=dict(color="#F7C6D0", width=3),              
        fill='tozeroy',
        fillcolor='rgba(247, 198, 208, 0.35)' 
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=20, b=40),
        xaxis=dict(
            title=dict(text="Tiempo", font=dict(color="#000000")),
            showgrid=True,
            gridcolor='#e5e7eb',
            tickfont=dict(color='#000000'),
        ),
        yaxis=dict(
            title=dict(text="Valor (°C)", font=dict(color="#000000")), 
            showgrid=True,
            gridcolor='#e5e7eb',
            color='#000000',
            tickfont=dict(color='#000000'),
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True, key="temperatura_realtime")


def tempstandard(view_mode):

    st.markdown("### Rangos de Temperatura")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="standard">
            <p style="color: #71be00; margin: 0; font-size: 0.9rem;">Temp. Baja</p>
            <h2 style="margin: 10px 0; color: #71be00;"> &lt;20 </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="standard">
            <p style="color: #ffbe00; margin: 0; font-size: 0.9rem;">Temp. Normal</p>
            <h2 style="margin: 10px 0; color: #ffbe00;">21-23°C</h2>
            <p style="color: #ffbe00; margin: 0; font-size: 0.85rem;">Dentro del rango normal</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="standard">
            <p style="color: #b20000; margin: 0; font-size: 0.9rem;">Temp. Alta</p>
            <h2 style="margin: 10px 0; color: #b20000;">&gt;25</h2>
        </div>
        """, unsafe_allow_html=True)


def tipsforkitchen(): 

    st.markdown("""
    <div class="tips-for-kitchen">
        <h3 style="margin-top: 0;"> Cocinas saludables </h3>
        <h4 style="font-size: 1.2rem; margin: 15px 0;">Ventajas de mantener condiciones favorables:</h4>
        <ul style="margin-top: 15px; font-size: 1rem;">
            <li>Mantiene los alimentos más tiempo</li>
            <li>Previene la proliferación de bacterias</li>
            <li>Menor temperatura reduce los accidentes por gas</li>     
        </ul>
        <hr style="border-color: rgba(255,255,255,0.3); margin: 10px 0;">
        <p style="margin: 10px 0; font-size: 0.95rem;">
            <strong>¿Cómo?:</strong>
        </p>
        <ul style="margin: 10px 0; padding-left: 20px;">
            <li>Mantén vías de ventilación (con mosquitero)</li>
            <li>Desecha los productos expirados</li>
            <li>No dejes que se acumulen los trastes sucios</li>
            <li>Desinfecta e higieniza el fregadero</li>
        </ul>
         <a href="https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/como-las-temperaturas-afectan-a" 
                   target="_blank" 
                   style="display:inline-block; padding:10px 20px; background:#4A90E2; color:white; border-radius:8px; text-decoration:none; font-weight:bold;">Saber más
         </a>
    </div>
    """, unsafe_allow_html=True)

      
# Aplicación principal
def main():
    # Layout principal con columnas
    col_main, col_side = st.columns([2, 1], gap="large")
    
    with col_main:
        humchart()
        st.markdown("<br>", unsafe_allow_html=True)
        humstandard(None)
        st.markdown("<br>", unsafe_allow_html=True)
        
        tempchart()
        st.markdown("<br>", unsafe_allow_html=True)
        tempstandard(None)
        
    with col_side:
        tipsforkitchen()
        st.markdown("<br>", unsafe_allow_html=True)
        
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #6b7280; padding: 20px;">
        <p>Dashboard de Monitoreo de Sensores Secundarios • Dispositivo: {DEVICE_ID}</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

# Se añade botón de Cerrar Sesión en el sidebar para conveniencia
if st.sidebar.button("Cerrar Sesión", type="secondary", use_container_width=True):

    if 'logged_in' in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state.pop("id_device", None)
        st.session_state.pop("nombre_completo", None)
    st.rerun()
        
    
   
          

           
   
            
    
    
    
   



            
        
        
