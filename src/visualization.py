"""
Mòdul de Visualitzacions per a BDACC ACNA
===========================================

Funcionalitat:
- Creació de mapes interactius amb pydeck
- Gràfics temporals amb plotly
- Gràfics de composició (pastís, barres)
- KPI Dashboard amb mètriques clau

Autor: Òscar Alemán-Milán 
"""

import pandas as pd
import streamlit as st
import pydeck as pdk
import plotly.express as px
from config.settings import MAP_CONFIG, COLORS
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import io


def create_map_layer(dff, show_points=True, show_heatmap=False, 
                    point_radius=5, point_opacity=0.8, 
                    heat_radius=6, heat_intensity=10.0, map_style=None):
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
    map_style : str
        Estil de mapa a utilitzar
    
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
    
    # Determinar estil de mapa
    if map_style is None:
        map_style_url = MAP_CONFIG['available_styles'][MAP_CONFIG['current_style']]
    else:
        map_style_url = MAP_CONFIG['available_styles'][map_style]
    
    layers = []
    
    # Afegir capa de tiles per a mapes especials (Topogràfic, IGN Raster, OSM Tiles)
    if map_style in ["Topogràfic", "IGN Raster", "OSM Tiles"]:
        try:
            tile_key_map = {
                "Topogràfic": "stamen_terrain",
                "IGN Raster": "ign_raster", 
                "OSM Tiles": "test_osm"
            }
            tile_url = MAP_CONFIG['tile_layer_urls'][tile_key_map[map_style]]
            
            # Crear capa de tiles exactament com diu Gemini IA
            tile_layer = pdk.Layer(
                "TileLayer",
                data=tile_url,
                tile_size=256,
            )
            # Inserir al principi perquè estigui al fons
            layers.insert(0, tile_layer)
            
            # IMPORTANT: El Deck debe tener map_style=None
            map_style_url = None
        except Exception as e:
            st.error(f"❌ Error carregant {map_style}: {e}")
            map_style_url = MAP_CONFIG['available_styles']['Fosc']
    
    # Capa de punts
    if show_points:
        # Prepara les dades per als tooltips
        dff_tooltip = dff.copy()
        tooltip_cols = [
            "Lloc","Data","Temporada","Grau de perill","Orientacio",
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
        map_style=map_style_url,  # Pot ser None per TileLayers
        tooltip={
            "html": get_simplified_tooltip_html(),
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


def get_simplified_tooltip_html():
    """
    Genera l'HTML simplificat per als tooltips del mapa.
    
    Retorna:
    --------
    str
        Template HTML simplificat per als tooltips
    """
    return """
    <b>{Lloc}</b><br/>
    Data: {Data}<br/>
    Perill: {Grau de perill}<br/>
    Origen: {Origen}<br/>
    Desencadenant: {Desencadenant}<br/>
    Morts: {Morts} | Ferits: {Ferits} | Arrossegats: {Arrossegats}
    """


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
    Data: {Data}<br/>
    Temporada: {Temporada}<br/>
    Perill: {Grau de perill}<br/>
    Orientació: {Orientacio}<br/>
    Morts: {Morts} | Ferits: {Ferits} | Arrossegats: {Arrossegats}
    Desencadenant: {Desencadenant}<br/>
    Mida d'allau: {Mida allau}<br/>
    Activitat: {Tipus activitat}<br/><br/>
    Morts: {Morts} · Ferits: {Ferits} · Arrossegats: {Arrossegats}
    """


def handle_map_click(click_data, dff):
    """
    Processa els esdeveniments de clic al mapa.
    
    Paràmetres:
    -----------
    click_data : dict
        Dades del clic proporcionades per Pydeck
    dff : pandas.DataFrame
        Dades dels accidents mostrats al mapa
    
    Retorna:
    --------
    dict
        Informació sobre el resultat del clic
    """
    if click_data is None:
        return None
    
    # Inicialitzar session_state si no existeix
    if 'selected_accident' not in st.session_state:
        st.session_state.selected_accident = None
    if 'clicked_coords' not in st.session_state:
        st.session_state.clicked_coords = None
    
    # Comprovar si hi ha coordenades al clic
    if 'coordinates' in click_data:
        coords = click_data['coordinates']
        lat, lon = coords[1], coords[0]  # Pydeck retorna [lon, lat]
        
        # Buscar si hi ha un accident a prop (tolerància de 0.001 graus ~100m)
        nearby_accident = None
        if not dff.empty and 'Latitud' in dff.columns and 'Longitud' in dff.columns:
            for _, accident in dff.iterrows():
                accident_lat = accident['Latitud']
                accident_lon = accident['Longitud']
                
                # Calcular distància simple (per a coordenades properes)
                if (abs(lat - accident_lat) < 0.001 and 
                    abs(lon - accident_lon) < 0.001):
                    nearby_accident = accident
                    break
        
        if nearby_accident is not None:
            # Clic en un accident existent
            st.session_state.selected_accident = nearby_accident.to_dict()
            st.session_state.clicked_coords = None
            
            return {
                'type': 'accident_selected',
                'accident': nearby_accident.to_dict()
            }
        else:
            # Clic en espai buit
            st.session_state.selected_accident = None
            st.session_state.clicked_coords = (lat, lon)
            
            return {
                'type': 'empty_space',
                'coordinates': (lat, lon)
            }
    
    return None


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
    # Asegurar que Temporada se trata como texto correctamente sin decimales
    dff_temp = dff.copy()
    if 'Temporada' in dff_temp.columns:
        # Convertir a string, eliminando decimales y manejando valores nulos
        dff_temp['Temporada'] = dff_temp['Temporada'].fillna('Desconegut').astype(str).replace('\.0$', '', regex=True)
    
    serie = (
        dff_temp.dropna(subset=["Temporada"])
           .groupby("Temporada", as_index=False)
           .agg(Accidents=("id","count"),  # Contar registros por temporada
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
    # Para variables categóricas, incluir todos los valores (texto y números)
    if dff[v1].dtype == 'object':
        # Si es categórica (texto), usar value_counts directamente
        comp1 = dff[v1].value_counts(normalize=True).mul(100).reset_index()
        comp1.columns = [v1, 'Percent']
        
        # Ordenamiento especial para Mes (año hidrológico: septiembre a agosto)
        if v1 == "Mes":
            # Definir orden del año hidrológico
            orden_hidrologico = ["Setembre", "Octubre", "Novembre", "Desembre", 
                               "Gener", "Febrer", "Març", "Abril", 
                               "Maig", "Juny", "Juliol", "Agost"]
            
            # Crear una columna de ordenamiento
            comp1['orden'] = comp1[v1].map({mes: i for i, mes in enumerate(orden_hidrologico)})
            # Ordenar según el año hidrológico
            comp1 = comp1.sort_values('orden').drop('orden', axis=1)
    else:
        # Si es numérica, usar value_counts pero asegurar incluir todos
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
    # Para variables categóricas, incluir todos los valores (texto y números)
    if dff[v2].dtype == 'object':
        # Si es categórica (texto), usar value_counts directamente
        comp2 = dff[v2].value_counts(normalize=True).mul(100).reset_index()
        comp2.columns = [v2, 'Percent']
        
        # Ordenamiento especial para Mes (año hidrológico: septiembre a agosto)
        if v2 == "Mes":
            # Definir orden del año hidrológico
            orden_hidrologico = ["Setembre", "Octubre", "Novembre", "Desembre", 
                               "Gener", "Febrer", "Març", "Abril", 
                               "Maig", "Juny", "Juliol", "Agost"]
            
            # Crear una columna de ordenamiento
            comp2['orden'] = comp2[v2].map({mes: i for i, mes in enumerate(orden_hidrologico)})
            # Ordenar según el año hidrológico
            comp2 = comp2.sort_values('orden').drop('orden', axis=1)
    else:
        # Si es numérica, usar value_counts pero asegurar incluir todos
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


def create_data_table(dff, original_file_path=None):
    """
    Crea la taula de dades amb funcionalitat completa d'edició i guardat.
    Suporta Google Sheets com a base de dades principal.
    """
    if dff.empty:
        return

    # 1. Gestión de estado para persistencia
    # Siempre actualizar df_actualizado con los datos filtrados actuales
    st.session_state.df_actualizado = dff.copy()
    if 'editing_table' not in st.session_state:
        st.session_state.editing_table = False
    if 'mensaje_guardado' not in st.session_state:
        st.session_state.mensaje_guardado = ""

    # 2. Detectar origen de datos
    data_source = st.session_state.get('data_source', 'none')
    is_gsheets_editable = data_source == 'gsheets_editable'
    is_local_source = data_source in ['local', 'local_custom']

    # 3. Advertencia para edición local temporal
    if is_local_source and st.session_state.editing_table:
        st.warning("⚠️ L'edició de fitxers locals no es desa permanentment. Per desar canvis, utilitza la base de dades Google Sheets.")

    # 4. CSS Personalizado para botones
    st.markdown("""
    <style>
    div.stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
        color: white !important; border: none !important;
    }
    .edit-mode-container div.stButton > button:not([data-testid="stBaseButton-primary"]) {
        background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%) !important;
        color: white !important; border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
        
    # 5. Botones de acción (Editar, Guardar, Exportar) - Diseño moderno
    st.markdown("""
    <style>
    .action-buttons-container {
        display: flex;
        gap: 8px;
        margin: 16px 0;
        justify-content: flex-start;
        flex-wrap: wrap;
    }
    .action-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.1);
        min-width: 120px;
    }
    .action-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.2);
    }
    .action-btn.primary {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        box-shadow: 0 2px 4px rgba(17, 153, 142, 0.1);
    }
    .action-btn.primary:hover {
        box-shadow: 0 4px 8px rgba(17, 153, 142, 0.2);
    }
    .action-btn.secondary {
        background: linear-gradient(135deg, #6b7280 0%, #374151 100%);
        box-shadow: 0 2px 4px rgba(107, 114, 128, 0.1);
    }
    .action-btn.secondary:hover {
        box-shadow: 0 4px 8px rgba(107, 114, 128, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)
        
    if not st.session_state.editing_table:
        # Botones en modo lectura: Editar y Exportar
        col1, col2 = st.columns([1, 1], gap="small")
        with col1:
            if st.button("📝 Editar", key="trigger_edit", use_container_width=True):
                st.session_state.editing_table = True
                st.rerun()
        with col2:
            if st.button("📥 Exportar Excel", key="export_excel", use_container_width=True):
                export_to_excel(st.session_state.df_actualizado)
    else:
        # Botones en modo edición: Guardar, Guardar y salir, Cancelar
        col1, col2, col3 = st.columns(3, gap="small")
        with col1:
            if st.button("💾 Guardar", type="primary", key="save", use_container_width=True):
                # Guardar cambios
                st.session_state.df_actualizado = st.session_state.temp_editor
                
                # Persistencia a Google Sheets si es editable
                if is_gsheets_editable:
                    try:
                        conn = st.session_state.get('gsheets_conn')
                        if conn:
                            conn.update(st.session_state.df_actualizado)
                            st.cache_data.clear()
                            st.toast("✅ Cambios guardados a Google Sheets!")
                        else:
                            st.error("❌ Error: No hay conexión con Google Sheets")
                    except Exception as e:
                        st.error(f"❌ Error guardando en Google Sheets: {e}")
                else:
                    st.toast("✅ Cambios guardados localmente")
                
                st.rerun()
                    
        with col2:
            if st.button("💾 Guardar y salir", type="primary", key="save_and_exit", use_container_width=True):
                # Guardar cambios y salir
                st.session_state.df_actualizado = st.session_state.temp_editor
                
                # Persistencia a Google Sheets si es editable
                if is_gsheets_editable:
                    try:
                        conn = st.session_state.get('gsheets_conn')
                        if conn:
                            conn.update(st.session_state.df_actualizado)
                            st.cache_data.clear()
                            st.toast("✅ Cambios guardados a Google Sheets!")
                        else:
                            st.error("❌ Error: No hay conexión con Google Sheets")
                    except Exception as e:
                        st.error(f"❌ Error guardando en Google Sheets: {e}")
                
                st.session_state.editing_table = False
                st.rerun()
                    
        with col3:
            if st.button("✖ Cancelar", key="cancel", use_container_width=True):
                st.session_state.editing_table = False
                st.rerun()
    config_cols = {"Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY")}
    
    # Asegurar que columnas categóricas se mantengan como string para Arrow
    df_display = st.session_state.df_actualizado.copy()
    categorical_cols = ["Grau de perill", "Mida allau", "Origen", "Desencadenant", 
                     "Tipus activitat", "Pais", "Regio", "Serralada", "Orientacio", 
                     "Progressio", "Material"]
    
    for col in categorical_cols:
        if col in df_display.columns:
            df_display[col] = df_display[col].astype(str)
    
    if st.session_state.editing_table:
        st.info("Pots editar directament les cel·les de la taula.")
        st.session_state.temp_editor = st.data_editor(
            df_display,
            column_config=config_cols,
            num_rows="dynamic",
            key="editor_principal"
        )
    else:
        st.dataframe(df_display, column_config=config_cols, width='stretch')
    
    # Mostrar mensaje de éxito debajo de la tabla
    if st.session_state.mensaje_guardado:
        st.success(st.session_state.mensaje_guardado)
        # Limpiar mensaje después de mostrarlo
        st.session_state.mensaje_guardado = ""


def export_to_excel(df):
    """
    Exporta el DataFrame a Excel y lo descarga automáticamente.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame a exportar
    """
    if df.empty:
        st.warning("⚠️ No hay datos para exportar")
        return
    
    try:
        # Crear un buffer en memoria
        output = io.BytesIO()
        
        # Escribir el DataFrame a Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Accidents_Filtrats')
        
        # Descargar el archivo
        st.download_button(
            label="📥 Descargar Excel",
            data=output.getvalue(),
            file_name=f'accidents_filtrats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        st.success("✅ Datos preparados para exportación")
        
    except Exception as e:
        st.error(f"❌ Error al exportar a Excel: {e}")


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
