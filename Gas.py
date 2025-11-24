import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta


# Configuración básica de la página
st.set_page_config(
    page_title="Dashboard de Monitoreo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
<style>
    .main {
        background: white;
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: black;
        margin-bottom: 0.5rem;
    }
    .emergency-card {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin: 10px 0;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
       
    }
    .info-box {
        background: #eff6ff;
        padding: 15px;
        border-radius: 8px;
        border-left: 3px solid #3b82f6;
        margin: 10px 0;
        color: black;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Funciones para generar datos de ejemplo
def generate_realtime_data():
    now = datetime.now()
    times = [now - timedelta(minutes=i) for i in range(30, 0, -1)]
    values = np.random.uniform(20, 80, 30) + np.sin(np.linspace(0, 4*np.pi, 30)) * 10
    return pd.DataFrame({
        'timestamp': times,
        'value': values
    })

def generate_gas_data(mode='weekly'):
    if mode == 'weekly':
        days = 7
        dates = [datetime.now() - timedelta(days=i) for i in range(days-1, -1, -1)]
        labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    else:
        days = 30
        dates = [datetime.now() - timedelta(days=i) for i in range(days-1, -1, -1)]
        labels = [d.strftime('%d') for d in dates]
    
    return pd.DataFrame({
        'date': dates,
        'label': labels,
        'consumption': np.random.uniform(15, 45, days)
    })

# Header
def render_header(user_name):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f'<div class="header-title">Hola, {user_name}</div>', unsafe_allow_html=True)
        st.markdown(f"**{datetime.now().strftime('%d de %B, %Y - %H:%M')}**")
    with col2:
        if st.button("🔔", help="Notificaciones"):
            st.toast("No hay nuevas notificaciones", icon="ℹ️")

# Gráfica en tiempo real
def render_realtime_chart():
    st.markdown("### Monitoreo en Tiempo Real")
    
    data = generate_realtime_data()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['value'],
        mode='lines',
        name='Medición',
        line=dict(color='#3b82f6', width=3),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)'
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
            title=dict(text="Valor (unidades)",font=dict(color="#000000") ),
            showgrid=True,
            gridcolor='#e5e7eb',
            color= '#000000',
            tickfont=dict(color='#000000'),
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white'
    ),
    
    st.plotly_chart(fig, use_container_width=True, key="realtime")

# Gráfica de consumo de gas
def render_gas_chart():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Consumo de Gas")
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
        marker_color="#d8b1e0",
        marker_line_color="#EBAFE9",
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Consumo Total</p>
            <h2 style="margin: 10px 0; color: #1e293b;">185.5 m³</h2>
            <p style="color: #10b981; margin: 0; font-size: 0.85rem;">↓ 12% vs período anterior</p>
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
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Pico Máximo</p>
            <h2 style="margin: 10px 0; color: #1e293b;">42.3 m³</h2>
            <p style="color: #ef4444; margin: 0; font-size: 0.85rem;">⚠️ Día viernes</p>
        </div>
        """, unsafe_allow_html=True)

# Contacto de emergencia
def render_emergency_contact():
    st.markdown("""
    <div class="emergency-card">
        <h3 style="margin-top: 0;">🚨 Contacto de Emergencia</h3>
        <h1 style="font-size: 2.5rem; margin: 15px 0;">📞 911</h1>
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
            <li>Aire viciado o dificultad para respirar</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚨 Marcar Emergencia", type="primary", use_container_width=True):
        st.warning("⚠️ En una emergencia real, marque 911 directamente desde su teléfono")

# Mapa de ubicación
def render_location_map():
    st.markdown("### 📍 Ubicación del Medidor")
    
    # Coordenadas de ejemplo (Ciudad de México, El Pueblito, Querétaro, MX)
    map_data = pd.DataFrame({
        'lat': [20.5471],
        'lon': [-100.4389]
    })
    
    st.map(map_data, zoom=13, use_container_width=True)
    
    st.markdown("""
    <div class="info-box">
        <strong>📍 Dirección:</strong><br>
        Av. Principal #123<br>
        El Pueblito, Querétaro, México
    </div>
    """, unsafe_allow_html=True)

# Aplicación principal
def main():
    # Header
    render_header("María García")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Layout principal con columnas
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
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280; padding: 20px;">
        <p>Dashboard de Monitoreo de Gas • Actualizado en tiempo real</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()