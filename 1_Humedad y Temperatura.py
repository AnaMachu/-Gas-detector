import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.markdown("""
<style>
    .main {
        background: white;
    }
    .tips-for-kitchen {
        background:#3cb371;
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin: 10px 0;
    }
    .standard {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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


def humchart():  # Humedad gráfica de líneas
    st.markdown("### Monitoreo de Humedad en Tiempo Real")
    fig = go.Figure()
    
    data = generate_realtime_data()

    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['value'],
        mode='lines',
        name='Medición',
        line=dict(color="#3bf68f", width=3),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)'
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
            title=dict(text="Valor (unidades)", font=dict(color="#000000")),
            showgrid=True,
            gridcolor='#e5e7eb',
            color='#000000',
            tickfont=dict(color='#000000'),
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True, key="humedad_realtime")


def humstandard(view_mode):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="standard">
            <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Hum. Baja</p>
            <h2 style="margin: 10px 0; color: #1e293b;"> &lt;30% </h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="standard">
            <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Hum. Normal</p>
            <h2 style="margin: 10px 0; color: #1e293b;">30-50%</h2>
            <p style="color: #6b7280; margin: 0; font-size: 0.85rem;">Dentro del rango normal</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="standard">
            <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Hum. Alta</p>
            <h2 style="margin: 10px 0; color: #1e293b;"> &gt;50% </h2>
            <p style="color: #ef4444; margin: 0; font-size: 0.85rem;">⚠️ Día viernes</p>
        </div>
        """, unsafe_allow_html=True)


def tempchart():  # Temperatura gráfica de líneas
    st.markdown("### Monitoreo de Temperatura en Tiempo Real")
    fig = go.Figure()
    
    data = generate_realtime_data()

    fig.add_trace(go.Scatter(
        x=data['timestamp'],
        y=data['value'],
        mode='lines',
        name='Medición',
        line=dict(color="#ec5bc0", width=3),
        fill='tozeroy',
        fillcolor='rgba(236, 91, 192, 0.1)'
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
            title=dict(text="Valor (unidades)", font=dict(color="#000000")),
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
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="standard">
            <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Temp. Baja</p>
            <h2 style="margin: 10px 0; color: #1e293b;">185.5 m³</h2>
            <p style="color: #10b981; margin: 0; font-size: 0.85rem;">↓ 12% vs período anterior</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="standard">
            <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Temp. Normal</p>
            <h2 style="margin: 10px 0; color: #1e293b;">26.5 m³</h2>
            <p style="color: #6b7280; margin: 0; font-size: 0.85rem;">Dentro del rango normal</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="standard">
            <p style="color: #6b7280; margin: 0; font-size: 0.9rem;">Temp. Alta</p>
            <h2 style="margin: 10px 0; color: #1e293b;">42.3 m³</h2>
            <p style="color: #ef4444; margin: 0; font-size: 0.85rem;">⚠️ Día viernes</p>
        </div>
        """, unsafe_allow_html=True)


def tipsforkitchen():  # Conseguir información para poner ahí y poner un link para mayores informes
    st.markdown("""
    <div class="tipsforkitchen">
        <h3 style="margin-top: 0;">Condiciones favorables para la cocina</h3>
        <h4 style="font-size: 1.2rem; margin: 15px 0;">Ventajas:</h4>
        <ul style="margin-top: 15px; font-size: 1rem;">
           <li>Mantiene los alimentos más tiempo</li>
           <li>Previene la proliferación de bacterias</li>
           <li>Menor temperatura reduce los accidentes por gas</li>    
        </ul>
        <hr style="border-color: rgba(255,255,255,0.3); margin: 20px 0;">
        <p style="margin: 10px 0; font-size: 0.95rem;">
            <strong>Señales de alerta en la cocina:</strong>
        </p>
        <ul style="margin: 10px 0; padding-left: 20px;">
            <li>Olor a gas o huevo podrido</li>
            <li>Llama amarilla o naranja en lugar de azul</li>
            <li>Manchas de hollín en electrodomésticos</li>
            <li>Aire viciado o dificultad para respirar</li>
        </ul>
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
    st.markdown("""
    <div style="text-align: center; color: #6b7280; padding: 20px;">
        <p>Dashboard de Monitoreo de Gas • Actualizado en tiempo real</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
