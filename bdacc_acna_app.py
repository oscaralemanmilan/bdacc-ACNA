"""
Base de Dades d'Accidents per Allaus - ACNA
==========================================

Aplicació Streamlit per a l'anàlisi visual de dades d'accidents d'allaus.

Arquitectura modular:
- src/data_processing.py: Processament i càrrega de dades
- src/visualization.py: Visualitzacions (mapes, gràfics)
- src/ui_components.py: Components d'interfície
- src/utils.py: Utilitats generals
- config/settings.py: Configuració global

Autor: Òscar Alemán-Milán © 2026
"""

import streamlit as st
import pandas as pd

# Importacions dels mòduls modulars
from src.data_processing import VARS_PERCENT, apply_filters
from src.visualization import (
    create_map_layer, create_temporal_chart, create_composition_charts,
    create_kpi_dashboard, render_kpi_boxes, create_data_table
)
from src.ui_components import (
    inject_custom_styles, create_data_source_sidebar, create_filters_sidebar,
    create_map_controls, create_page_header, create_composition_chart_controls,
    sidebar_error, sidebar_success, sidebar_info, create_footer, show_empty_data_message
)
from config.settings import PAGE_CONFIG, HTML_TEMPLATES


def main():
    """
    Funció principal de l'aplicació.
    """
    # Configuració de la pàgina
    st.set_page_config(**PAGE_CONFIG)
    
    # Injecta estils personalitzats
    inject_custom_styles()
    
    # Capçalera de la pàgina
    create_page_header()
    
    # Barra lateral - Origen de dades
    df, has_data = create_data_source_sidebar()
    
    # Barra lateral - Filtres
    if has_data:
        filter_config = create_filters_sidebar(df)
        
        # Aplica filtres a les dades
        dff = apply_filters(
            df, 
            filter_config['filters'], 
            filter_config['metrica']
        )
    else:
        dff = pd.DataFrame()
        filter_config = {
            'metrica': 'Accidents',
            'tipus_grafic_temporal': 'Barres'
        }
    
    # Comprova si hi ha dades després de filtrar
    if dff.empty:
        show_empty_data_message(has_data)
    else:
        # Secció del mapa
        render_map_section(dff)
        
        # Secció de KPIs
        render_kpi_section(dff)
        
        # Secció de gràfics temporals
        render_temporal_chart_section(dff, filter_config['tipus_grafic_temporal'])
        
        # Secció de gràfics de composició
        render_composition_charts_section(dff)
        
        # Secció de taula de dades
        render_data_table_section(dff)
    
    # Peu de pàgina
    create_footer()


def render_map_section(dff):
    """
    Renderitza la secció del mapa interactiu.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades per mostrar
    """
    # Controls del mapa
    map_config = create_map_controls()
    
    # Crea el mapa
    deck = create_map_layer(
        dff,
        show_points=map_config['show_points'],
        show_heatmap=map_config['show_heatmap'],
        point_radius=map_config['point_radius'],
        point_opacity=map_config['point_opacity'],
        heat_radius=map_config['heat_radius'],
        heat_intensity=map_config['heat_intensity']
    )
    
    if deck:
        st.pydeck_chart(deck, use_container_width=True)


def render_kpi_section(dff):
    """
    Renderitza la secció de KPIs.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades
    """
    # Calcula KPIs
    kpi_data = create_kpi_dashboard(dff)
    
    # Renderitza les caixes de KPI
    render_kpi_boxes(kpi_data)


def render_temporal_chart_section(dff, chart_type):
    """
    Renderitza la secció del gràfic temporal.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades
    chart_type : str
        Tipus de gràfic ("Barres" o "Línia")
    """
    st.markdown(HTML_TEMPLATES['main_padding'], unsafe_allow_html=True)
    
    st.markdown("### Evolució temporal (Accidents i Morts)")
    
    # Crea el gràfic temporal
    fig = create_temporal_chart(dff, chart_type)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)


def render_composition_charts_section(dff):
    """
    Renderitza la secció de gràfics de composició.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades
    """
    st.markdown("---")
    st.markdown("### Anàlisi de Variables Categòriques")
    
    # Controls dels gràfics
    chart_config = create_composition_chart_controls(VARS_PERCENT)
    
    # Converteix tipus de gràfic a índexs
    type_map = {"Pastís": 0, "Barres (V)": 1, "Barres (H)": 2}
    type1_index = type_map[chart_config['type1']]
    type2_index = type_map[chart_config['type2']]
    
    # Troba els índexs de les variables
    var1_index = VARS_PERCENT.index(chart_config['var1'])
    var2_index = VARS_PERCENT.index(chart_config['var2'])
    
    # Crea els gràfics
    fig1, fig2 = create_composition_charts(
        dff, VARS_PERCENT, 
        var1_index, var2_index,
        type1_index, type2_index
    )
    
    if fig1 and fig2:
        col_esquerra, col_dreta = st.columns(2)
        
        with col_esquerra:
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_dreta:
            st.plotly_chart(fig2, use_container_width=True)


def render_data_table_section(dff):
    """
    Renderitza la secció de la taula de dades.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades
    """
    with st.expander("📄 Dades filtrades"):
        create_data_table(dff)


if __name__ == "__main__":
    main()
