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
    serie = (
        dff.dropna(subset=["Temporada"])
           .assign(Temp=lambda x: x["Temporada"].astype(str))  # Mantener como string
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


def create_data_table(dff, original_file_path=None):
    """
    Crea la taula de dades mantent el tipus de dada 'datetime' per a un ordenament correcte.
    """
    if dff.empty:
        return

    # 1. Neteja de columnes duplicades (mètode eficient)
    df_visualizacion = dff.loc[:, ~dff.columns.duplicated()].copy()

    # 2. Selecció de columnes segons l'Excel original
    columnas_excel = [
        'id', 'Codi', 'Temporada', 'Data', 'Lloc', 'Latitud', 'Longitud', 
        'Tipus activitat', 'Pais', 'Regio', 'Serralada', 'Orientacio', 'Altitud', 
        'Grup', 'Desenc', 'Arrossegats', 'Ferits', 'Morts', 'Grau de perill', 
        'Mida allau', 'Origen', 'Progressio', 'Desencadenant', 'Neu', 'Material', 
        'Observacions', 'Link', 'Fotos'
    ]
    columnas_mostrar = [col for col in columnas_excel if col in df_visualizacion.columns]
    df_visualizacion = df_visualizacion[columnas_mostrar].copy()

    # --- TRACTAMENT DE DATES (FORMATO AÑO-MES-DIA HH:MM:SS) ---
    if 'Data' in df_visualizacion.columns:
        
        # 1. Conversión para formato estándar año-mes-dia hh:mm:ss
        df_visualizacion['Data'] = pd.to_datetime(
            df_visualizacion['Data'], 
            errors='coerce'
        )

        # 2. Eliminar espais invisibles i valors estranys
        df_visualizacion['Data'] = df_visualizacion['Data'].astype('datetime64[ns]')

        # 3. Ordenar per data (més recents primer)
        df_visualizacion = df_visualizacion.sort_values(
            by='Data',
            ascending=False,
            na_position='last'
        )
    
    # --- CORRECCIÓN GENERAL PARA ARROW: Convertir columnas object con números a strings ---
    # Identificar columnas de tipo object que puedan contener números
    for col in df_visualizacion.columns:
        if df_visualizacion[col].dtype == 'object':
            # Verificar si la columna contiene valores numéricos mezclados
            sample_values = df_visualizacion[col].dropna().head(10)
            if any(isinstance(val, (int, float)) for val in sample_values):
                df_visualizacion[col] = df_visualizacion[col].astype(str)

    # --- REORDENACIÓ VISUAL DE COLUMNES ---
    columnas_importantes = ["id", "Codi", "Data", "Temporada", "Lloc", "Pais", "Regio", "Morts", "Ferits"]
    cols_existentes = [c for c in columnas_importantes if c in df_visualizacion.columns]
    resto_cols = [c for c in df_visualizacion.columns if c not in cols_existentes]
    df_visualizacion = df_visualizacion[cols_existentes + resto_cols]

    # --- GESTIÓ D'ESTAT (SESSION STATE) ---
    if 'editing_table' not in st.session_state:
        st.session_state.editing_table = False
    
    # Per evitar que les dades editades quedin "congelades" si canvien els filtres,
    # actualitzem el session_state si no estem en mode edició activa.
    if not st.session_state.editing_table:
        st.session_state.edited_data = df_visualizacion.copy()

    # --- INTERFÍCIA DE BOTONS AMB ESTILS PERSONALITZATS I FUNCIONALITAT ---
    # CSS personalitzat per controlar padding, mida i color - Selectors més específics
    # Hi ha estils que no reaccionen
    # Estils que funcionen són box-shadow, border-radius i padding
    st.markdown("""
    <style>
    /* Selectores més específics per botons de la taula */
    [data-testid="stVerticalBlock"] div.stButton > button[data-testid="stBaseButton-secondary"],
    [data-testid="stVerticalBlock"] div.stButton > button[data-testid="stBaseButton-primary"],
    div.stButton > button[data-testid="stBaseButton-secondary"],
    div.stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        padding: 12px 12px !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 10px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.4) !important;
        min-height: 24px !important;
        line-height: 8px !important;
    }
    
    /* Botón Guardar (primary) */
    [data-testid="stVerticalBlock"] div.stButton > button[data-testid="stBaseButton-primary"],
    div.stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
        box-shadow: 0 2px 4px rgba(17, 153, 142, 0.4) !important;
    }
    
    /* Botón Cancelar (último secondary) */
    [data-testid="stVerticalBlock"] div.stButton > button[data-testid="stBaseButton-secondary"]:last-child,
    div.stButton > button[data-testid="stBaseButton-secondary"]:last-child {
        background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%) !important;
        box-shadow: 0 2px 4px rgba(238, 9, 121, 0.4) !important;
    }
    
    /* Hover effects */
    [data-testid="stVerticalBlock"] div.stButton > button:hover,
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 2px 6px rgba(102, 126, 234, 0.6) !important;
    }
    
    [data-testid="stVerticalBlock"] div.stButton > button[data-testid="stBaseButton-primary"]:hover,
    div.stButton > button[data-testid="stBaseButton-primary"]:hover {
        box-shadow: 0 2px 6px rgba(17, 153, 142, 0.6) !important;
    }
    
    [data-testid="stVerticalBlock"] div.stButton > button[data-testid="stBaseButton-secondary"]:last-child:hover,
    div.stButton > button[data-testid="stBaseButton-secondary"]:last-child:hover {
        box-shadow: 0 2px 6px rgba(238, 9, 121, 0.6) !important;
    }
    
    </style>
    """, unsafe_allow_html=True)
    
    # Variable para mostrar mensaje de éxito (usando session_state para persistencia)
    if 'mensaje_guardado' not in st.session_state:
        st.session_state.mensaje_guardado = ""
    
    col_btn, _ = st.columns([1, 2])  # Botons de la taula de dades
    with col_btn:
        if not st.session_state.editing_table:
            if st.button("Editar"):
                st.session_state.editing_table = True
                st.session_state.mensaje_guardado = ""  # Limpiar mensaje al entrar en edición
                st.rerun()
        else:
            c1, c2, c3 = st.columns(3)  # Tres botones en modo edición
            with c1:
                if st.button("Guardar", type="primary"):
                    # Lógica de guardar los cambios editados (sin salir de edición)
                    # 1. Capturar los datos editados del data_editor
                    datos_editados = st.session_state.edited_data.copy()
                    
                    # 2. Actualizar el DataFrame original con los cambios
                    df_visualizacion.update(datos_editados)
                    
                    # 3. Guardar en session_state para persistencia
                    st.session_state.df_actualizado = df_visualizacion.copy()
                    
                    # 4. Mensaje de éxito
                    st.session_state.mensaje_guardado = "Canvis desats correctament"
                    
                    # 5. MANTENER en modo edición (no salir)
                    st.rerun()
            with c2:
                if st.button("Guardar i sortir", type="primary"):
                    # Lógica de guardar y salir
                    # 1. Capturar los datos editados del data_editor
                    datos_editados = st.session_state.edited_data.copy()
                    
                    # 2. Actualizar el DataFrame original con los cambios
                    df_visualizacion.update(datos_editados)
                    
                    # 3. Guardar en session_state para persistencia
                    st.session_state.df_actualizado = df_visualizacion.copy()
                    
                    # 4. Mensaje de éxito
                    st.session_state.mensaje_guardado = "Canvis desats i sortit correctament"
                    
                    # 5. Salir del modo edición
                    st.session_state.editing_table = False
                    st.rerun()
            with c3:
                if st.button("Cancel·lar"):
                    # Lógica de cancelar (salir sin guardar cambios)
                    st.session_state.editing_table = False
                    st.session_state.mensaje_guardado = "Edició cancelada sense guardar canvis"
                    st.rerun()

    # --- RENDERITZAT AMB CONFIGURACIÓ DE COLUMNA ---
    # Definim com volem que Streamlit mostri la data (format DD/MM/YYYY)
    config_columnes = {
        "Data": st.column_config.DateColumn(
            "Data",
            format="DD/MM/YYYY",  # Mostrar en formato día/mes/año
            help="Data de l'accident"
        )
    }

    if st.session_state.editing_table:
        st.subheader("📝 Dades Filtrades (Mode d'edició)")
        # El data_editor respectarà el format i permetrà triar dates amb un calendari
        st.session_state.edited_data = st.data_editor(
            st.session_state.edited_data,
            column_config=config_columnes,
            num_rows="dynamic",
            width='stretch'
        )
    else:
        st.subheader(" Dades filtrades")
        # El dataframe mostrarà la data correctament però l'ordenarà pel valor temporal real
        st.dataframe(
            df_visualizacion, 
            column_config=config_columnes,
            width='stretch'
        )
    
    # Mostrar mensaje de éxito debajo de la tabla
    if st.session_state.mensaje_guardado:
        st.success(st.session_state.mensaje_guardado)
        # Limpiar mensaje después de mostrarlo
        st.session_state.mensaje_guardado = ""


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
