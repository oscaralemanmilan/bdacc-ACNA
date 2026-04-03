"""
Mòdul de Visualitzacions per a BDACC ACNA
===========================================

Funcionalitat:
- Creació de mapes interactius amb pydeck
- Gràfics temporals amb plotly
- Gràfics de composició (pastís, barres)
- KPI Dashboard amb mètriques clau

Autor: Òscar Alemán-Milán © 2026
"""

import pandas as pd
import streamlit as st
import pydeck as pdk
import plotly.express as px
from config.settings import MAP_CONFIG, COLORS


def create_map_layer(dff, show_points=True, show_heatmap=False, 
                    point_radius=5, point_opacity=0.8, 
                    heat_radius=6, heat_intensity=10.0):
    """
    Crea les capes de visualització per al mapa interactiu.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades per mostrar al mapa
    show_points : bool
        Mostrar punts individuals
    show_heatmap : bool
        Mostrar mapa de calor
    point_radius : int
        Radi dels punts en píxels
    point_opacity : float
        Opacitat dels punts (0.1-1.0)
    heat_radius : int
        Radi del mapa de calor
    heat_intensity : float
        Intensitat del mapa de calor
    
    Retorna:
    --------
    pydeck.Deck
        Objecte de mapa pydeck configurat
    """
    
    if dff.empty:
        return None
    
    # Configuració de la vista del mapa
    center, zoom = get_map_center_zoom(dff)
    view_state = pdk.ViewState(
        latitude=center["lat"], 
        longitude=center["lon"], 
        zoom=zoom
    )
    
    layers = []
    
    # Capa de punts
    if show_points:
        # Prepara les dades per als tooltips
        dff_tooltip = dff.copy()
        tooltip_cols = [
            "Lloc","Data_str","Temporada","Grau de perill","Orientacio",
            "Origen","Desencadenant","Mida allau","Tipus activitat",
            "Morts","Ferits","Arrossegats"
        ]
        
        for col in tooltip_cols:
            if col in dff_tooltip.columns:
                dff_tooltip[col] = dff_tooltip[col].astype(str).replace({"nan":"Desconegut"})
        
        # Converteix opacitat a format 0-255
        alpha = int(point_opacity * 255)
        
        layer_points = pdk.Layer(
            "ScatterplotLayer",
            data=dff_tooltip,
            get_position='[Longitud, Latitud]',
            get_radius=point_radius,
            get_fill_color=[COLORS['turquoise_rgb'][0], 
                           COLORS['turquoise_rgb'][1], 
                           COLORS['turquoise_rgb'][2], 
                           alpha],
            radius_units="pixels",
            stroked=True,
            pickable=True
        )
        layers.append(layer_points)
    
    # Capa de mapa de calor
    if show_heatmap:
        dff_heat = dff.copy()
        dff_heat["_weight"] = 1.0
        
        layer_heat = pdk.Layer(
            "HeatmapLayer",
            data=dff_heat,
            get_position='[Longitud, Latitud]',
            get_weight="_weight",
            radiusPixels=heat_radius,
            intensity=heat_intensity,
            threshold=0,
            colorRange=COLORS['heatmap_gradient']
        )
        layers.append(layer_heat)
    
    # Crea el mapa
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=MAP_CONFIG['base_map'],
        tooltip={
            "html": get_map_tooltip_html(),
            "style": {"backgroundColor":"rgba(14,17,23,0.92)","color":"white"}
        }
    )
    
    return deck


def get_map_center_zoom(dff):
    """
    Calcula el centre i zoom òptims per al mapa.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades per calcular el centre
    
    Retorna:
    --------
    tuple
        (center_dict, zoom_level)
    """
    # Actualment fixat a la Península Ibèrica
    # En el futur es podria fer dinàmic segons les dades
    center = {"lat": MAP_CONFIG['default_center']['lat'], 
             "lon": MAP_CONFIG['default_center']['lon']}
    zoom = MAP_CONFIG['default_zoom']
    
    return center, zoom


def get_map_tooltip_html():
    """
    Genera l'HTML per als tooltips del mapa.
    
    Retorna:
    --------
    str
        Template HTML per als tooltips
    """
    return """
    <b>{Lloc}</b><br/>
    Data: {Data_str}<br/>
    Temporada: {Temporada}<br/>
    Perill: {Grau de perill}<br/>
    Orientació: {Orientacio}<br/>
    Origen: {Origen}<br/>
    Desencadenant: {Desencadenant}<br/>
    Mida d'allau: {Mida allau}<br/>
    Activitat: {Tipus activitat}<br/><br/>
    Morts: {Morts} · Ferits: {Ferits} · Arrossegats: {Arrossegats}
    """


def create_temporal_chart(dff, chart_type="Barres"):
    """
    Crea el gràfic d'evolució temporal d'accidents i morts.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades
    chart_type : str
        "Barres" o "Línia"
    
    Retorna:
    --------
    plotly.graph_objects.Figure
        Gràfic de plotly configurat
    """
    
    if dff.empty:
        return None
    
    # Prepara les dades temporals
    serie = (
        dff.dropna(subset=["Temporada"])
           .assign(Temp=lambda x: pd.to_numeric(x["Temporada"], errors="coerce"))
           .groupby("Temporada", as_index=False)
           .agg(Accidents=("Accidents","sum"),
                Morts=("Morts","sum"))
           .sort_values("Temporada")
    )
    
    if chart_type == "Línia":
        fig = px.line(
            serie, x="Temporada", y=["Accidents","Morts"],
            markers=True, template="plotly",
            title="Evolució per Temporada"
        )
    else:  # Barres
        long_df = serie.melt(id_vars=["Temporada"], value_vars=["Accidents","Morts"])
        fig = px.bar(
            long_df, x="Temporada", y="value", color="variable",
            barmode="group", template="plotly",
            title="Evolució per Temporada"
        )
        fig.update_traces(marker_line_width=0)
    
    fig.update_layout(height=480)
    return fig


def create_composition_charts(dff, vars_percent, var1_index=0, var2_index=2, 
                            type1_index=2, type2_index=0):
    """
    Crea dos gràfics de composició comparatius.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades
    vars_percent : list
        Llista de variables categòriques disponibles
    var1_index, var2_index : int
        Índexs de les variables seleccionades
    type1_index, type2_index : int
        Índexs dels tipus de gràfic (0=Pastís, 1=Barres V, 2=Barres H)
    
    Retorna:
    --------
    tuple
        (fig1, fig2) - Figures de plotly
    """
    
    if dff.empty:
        return None, None
    
    # Variables seleccionades
    v1 = vars_percent[var1_index]
    v2 = vars_percent[var2_index]
    
    # Tipus de gràfic
    chart_types = ["Pastís", "Barres (V)", "Barres (H)"]
    t1 = chart_types[type1_index]
    t2 = chart_types[type2_index]
    
    # Prepara dades per al primer gràfic
    comp1 = dff[v1].value_counts(normalize=True).mul(100).reset_index()
    comp1.columns = [v1, 'Percent']
    
    # Crea el primer gràfic
    if t1 == "Pastís":
        fig1 = px.pie(comp1, names=v1, values="Percent", hole=0.45, template="plotly_dark")
    elif t1 == "Barres (V)":
        fig1 = px.bar(comp1, x=v1, y="Percent", template="plotly_dark", text_auto='.1f')
        fig1.update_traces(marker_line_width=0)
    else:  # Barres (H)
        fig1 = px.bar(comp1, y=v1, x="Percent", orientation="h", template="plotly_dark", text_auto='.1f')
        fig1.update_traces(marker_line_width=0)
    
    # Prepara dades per al segon gràfic
    comp2 = dff[v2].value_counts(normalize=True).mul(100).reset_index()
    comp2.columns = [v2, 'Percent']
    
    # Crea el segon gràfic
    if t2 == "Pastís":
        fig2 = px.pie(comp2, names=v2, values="Percent", hole=0.45, template="plotly_dark")
    elif t2 == "Barres (V)":
        fig2 = px.bar(comp2, x=v2, y="Percent", template="plotly_dark", text_auto='.1f')
        fig2.update_traces(marker_line_width=0)
    else:  # Barres (H)
        fig2 = px.bar(comp2, y=v2, x="Percent", orientation="h", template="plotly_dark", text_auto='.1f')
        fig2.update_traces(marker_line_width=0)
    
    # Ajusta els marges
    fig1.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    
    return fig1, fig2


def create_kpi_dashboard(dff):
    """
    Crea el dashboard de KPIs amb mètriques clau.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades
    
    Retorna:
    --------
    dict
        Diccionari amb els valors dels KPIs
    """
    
    if dff.empty:
        return {}
    
    # Càlculs bàsics
    total = len(dff)
    n_morts_regs = (dff["Morts"] > 0).sum()
    n_ferits_regs = (dff["Ferits"] > 0).sum()
    
    # Percentatges
    p_morts = (n_morts_regs / total * 100) if total else 0
    p_ferits = (n_ferits_regs / total * 100) if total else 0
    
    # Totals
    total_morts = dff["Morts"].sum()
    total_ferits = dff["Ferits"].sum()
    total_arros = dff["Arrossegats"].sum()
    
    # Percentatges respecte arrossegats
    pm_morts = (total_morts / total_arros * 100) if total_arros > 0 else 0
    pm_ferits = (total_ferits / total_arros * 100) if total_arros > 0 else 0
    
    return {
        'total_accidents': total,
        'percent_morts': p_morts,
        'percent_ferits': p_ferits,
        'percent_morts_arrossegats': pm_morts,
        'percent_ferits_arrossegats': pm_ferits,
        'total_arrossegats': total_arros
    }


def render_kpi_boxes(kpi_data):
    """
    Renderitza les caixes de KPI a la interfície.
    
    Paràmetres:
    -----------
    kpi_data : dict
        Dades dels KPIs retornades per create_kpi_dashboard
    """
    
    if not kpi_data:
        return
    
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    
    with k1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Accidents filtrats</div>
            <div class="kpi-value">{kpi_data['total_accidents']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k2:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">% accidents amb morts</div>
            <div class="kpi-value">{kpi_data['percent_morts']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k3:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">% accidents amb ferits</div>
            <div class="kpi-value">{kpi_data['percent_ferits']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k4:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">% morts / arrossegats</div>
            <div class="kpi-value">{kpi_data['percent_morts_arrossegats']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k5:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">% ferits / arrossegats</div>
            <div class="kpi-value">{kpi_data['percent_ferits_arrossegats']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k6:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Arrossegats (total)</div>
            <div class="kpi-value">{kpi_data['total_arrossegats']}</div>
        </div>
        """, unsafe_allow_html=True)


def create_data_table(dff):
    """
    Crea la taula de dades amb opció de descàrrega.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades per mostrar
    """
    
    if dff.empty:
        return
    
    # Columnes a mostrar (en ordre lògic)
    cols = [
        "Data_str","Temporada","Lloc","Pais","Regio","Serralada","Orientacio",
        "Altitud","Grau de perill","Mida allau","Tipus activitat",
        "Origen","Desencadenant","Progressio",
        "Morts","Ferits","Arrossegats","Latitud","Longitud"
    ]
    
    # Filtra només les columnes existents
    cols = [c for c in cols if c in dff.columns]
    
    # Mostra la taula
    st.dataframe(dff[cols], use_container_width=True)
    
    # Opció de descàrrega
    csv = dff[cols].to_csv(index=False).encode("utf-8")
    st.download_button("💾 Descarrega CSV", csv, "accidents_filtrats.csv")
