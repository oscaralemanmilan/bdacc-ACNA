"""
Components d'interfície d'usuari per a mapes Folium simplificat.
Proporciona controls mínims i mapa amb funcions natives de Folium.

Autor: Òscar Alemán-Milán 2026
"""

import streamlit as st


def create_folium_controls():
    """
    Crea controls mínims per al mapa Folium.
    
    Retorna:
    --------
    dict
        Configuració simplificada del mapa
    """
    st.markdown("### 🗺️ Mapa d'Accidents per Allaus ACNA")
    
    # Control mínim - només mostrar punts
    show_points = st.checkbox("📍 Mostrar punts", value=True)
    
    return {
        'show_points': show_points,
        'auto_fit': False  # Centrar controlat pel botó del mapa
    }


# Función eliminada - ahora se usa streamlit_folium para interactividad
# La lógica de edición de puntos se retomará más adelante con nuevo enfoque
