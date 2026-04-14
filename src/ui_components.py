"""
Mòdul de Components d'Interfície d'Usuari per a BDACC ACNA
===========================================================

Funcionalitat:
- Estils CSS personalitzats
- Components de la barra lateral
- Missatges d'error/success/informació
- Layout i estructura de la pàgina

Autor: Òscar Alemán-Milán © 2026
"""

import streamlit as st
import os
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from src.data_processing import load_data, load_from_gsheet, get_column_options, process_data
from config.settings import COLORS, UI_CONFIG, HTML_TEMPLATES, MAP_CONFIG


def inject_custom_styles():
    """
    Injecta els estils CSS personalitzats a l'aplicació Streamlit.
    """
    st.markdown(f"""
<style>
/* Colors de fons per tema clar/fosc */
.stApp[data-theme="dark"] {{ background-color: {COLORS['dark_bg']} !important; }}
.stApp[data-theme="light"] {{ background-color: {COLORS['light_bg']} !important; }}

/* Colors de text per tema clar/fosc */
.stApp[data-theme="dark"] h1, .stApp[data-theme="dark"] h2, .stApp[data-theme="dark"] h3, 
            .stApp[data-theme="dark"] h4, .stApp[data-theme="dark"] h5, .stApp[data-theme="dark"] p, 
            .stApp[data-theme="dark"] label {{ color: #ffffff !important; }}
.stApp[data-theme="light"] h1, .stApp[data-theme="light"] h2, .stApp[data-theme="light"] h3, 
            .stApp[data-theme="light"] h4, .stApp[data-theme="light"] h5, .stApp[data-theme="light"] p, 
            .stApp[data-theme="light"] label {{ color: #000000 !important; }}

/* Barra lateral */
.stApp[data-theme="dark"] [data-testid="stSidebar"] {{ background-color: {COLORS['sidebar_dark']} !important; }}
[data-testid="stSidebar"][data-theme="dark"] * {{ color: #ffffff !important; }}
[data-testid="stSidebar"][data-theme="light"] {{ background-color: {COLORS['sidebar_light']} !important; }}
[data-testid="stSidebar"][data-theme="light"] * {{ color: #000000 !important; }}
/* Reduir padding del sidebar al mínim */
[data-testid="stSidebar"] > div {{ padding: 0rem 0.5rem !important; }}
[data-testid="stSidebar"] > section {{ padding: 0 0.5rem !important; }}

/* Eliminar marges dels títols del sidebar per pujar el contingut */
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {{
    margin-top: 0px !important;
    padding-top: 0px !important;
}}

/* Control visual del logo del sidebar (més robust) */
[data-testid="stSidebarUserContent"] div[data-testid="stImage"] img {{
    margin-top: 30px !important;      
    margin-bottom: 20px !important;   
    margin-left: auto !important;
    margin-right: auto !important;
    display: block !important;
    width: {UI_CONFIG['sidebar_logo_width']}px !important;
}}

/* Camps d'entrada */
.stApp[data-theme="dark"] div[data-baseweb="select"] > div,
.stApp[data-theme="dark"] div[data-baseweb="input"] > div,
.stApp[data-theme="dark"] div[data-baseweb="textarea"] > div {{
    background-color: #1a1a1a !important; color: white !important;
}}
.stApp[data-theme="light"] div[data-baseweb="select"] > div,
.stApp[data-theme="light"] div[data-baseweb="input"] > div,
.stApp[data-theme="light"] div[data-baseweb="textarea"] > div {{
    background-color: #ffffff !important; color: black !important;
}}

/* Botons */
.stButton>button {{
    width: 100%; border: 1px solid {COLORS['turquoise']};
    background: transparent!important; color: {COLORS['turquoise']} !important; font-weight: bold;
}}
.stButton>button:hover {{ background: {COLORS['turquoise']} !important; color: black !important; }}

/* Espaiat principal */
section.main > div {{ padding-top: 0rem !important; }}
[data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}

/* Control de padding superior de títols */
/* Control d'espais superiors (Netejat) */
h1 {{ 
    margin-top: -40px !important; 
    margin-bottom: 0px !important; 
    padding-top: 0px !important;
    padding-bottom: 0px !important;
}}
.main .block-container {{ padding-top: 0px !important; }}
/* Alinear logo amb el títol */
[data-testid="stImage"] {{
    margin-top: -65px !important;
    margin-bottom: 0px !important; 
    padding-top: 0px !important;
    padding-bottom: 0px !important;
}}
h3 {{ 
    margin-top: 15px !important; 
    margin-bottom: 15px !important;
    padding-top: 0px !important;
    padding-bottom: 0px !important;
}}

/* Llegenda del mapa de calor */
#heatmap-legend {{
    position: fixed; right: 24px; bottom: 24px; z-index: 9999;
    background: rgba(20,20,20,0.85); border: 1px solid rgba(255,255,255,0.25);
    border-radius: 6px; padding: 10px 12px; font-size: 12px; color: #eee;
    backdrop-filter: blur(3px); box-shadow: 0 0 10px rgba(0,0,0,0.4);
}}
#heatmap-legend .title {{ font-weight: 600; margin-bottom: 6px; color: {COLORS['turquoise']}; }}
#heatmap-legend .bar {{
    height: 10px; width: 240px; border-radius: 3px; margin: 6px 0 4px 0;
    background: linear-gradient(90deg,
        #000000 0%,
        #5e2b97 20%,
        #b02bff 40%,
        #ff5f3d 60%,
        #ffbd3d 80%,
        #fff26a 100%
    );
}}
#heatmap-legend .ticks {{ display: flex; justify-content: space-between; color: #ccc; font-size: 11px; }}
#heatmap-legend .note {{ color: #9bd7cf; font-size: 11px; margin-top: 4px; }}

/* Caixes de KPI */
.kpi-box {{ background: #12151c; border: 1px solid #263042; border-radius: 0px; padding: 12px 14px; margin-top: 0px !important; margin-bottom: 15px !important; }}
.kpi-title {{ color: #9bd7cf; font-size: 12px; margin-bottom: 6px; text-transform: uppercase; }}
.kpi-value {{ color: #ffffff; font-size: 22px; font-weight: 700; margin-bottom: 4px; }}
.kpi-sub {{ color: #d0d4da; font-size: 12px; }}
      
/* Control d'espaiat per a gràfics Plotly */
[data-testid="stPlotlyChart"] {{
    margin-top: 0 !important;
    margin-bottom: 10px !important;
}}
/* Peu de pàgina fixat */
.footer-fixat {{
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: rgba(14, 17, 23, 0.85);
    color: #888;
    text-align: center;
    padding: 5px 20px;
    font-size: 0.8rem;
    z-index: 999;
    border-top: 1px solid #263042;
    display: flex;
    justify-content: space-between;
}}

/* Espai extra al final */
.main .block-container {{
    padding-bottom: 50px !important;
}}
      
</style>
""", unsafe_allow_html=True)


def create_data_source_sidebar():
    """
    Crea la secció de selecció d'origen de dades a la barra lateral.
    
    Retorna:
    --------
    tuple
        (df, has_data, data_source) - DataFrame carregat, booleà si hi ha dades, i font de dades
    """
    # Logo del sidebar configurat (primera posició)
    st.sidebar.image(
        UI_CONFIG['sidebar_logo_path'], 
        width=UI_CONFIG['sidebar_logo_width']
    )

    st.sidebar.header("📊 Origen de dades")
    
    origen = st.sidebar.radio(
        "Selecciona l'origen de les dades:", 
        UI_CONFIG['data_sources'], 
        key="origen"
    )
    
    df = None
    
    # Inicializar variables para Google Sheets
    conn = None
    worksheet = None
    
    if origen == "Google Sheets (Editable)":
        
        # --- SISTEMA DE PROTECCIÓ PER CONTRASENYA ---
        if "is_authenticated" not in st.session_state:
            st.session_state.is_authenticated = False
            
        # Llegeix directament del fitxer secrets.toml.
        correct_pwd = st.secrets["ADMIN_PASSWORD"]
        
        if not st.session_state.is_authenticated:
            st.sidebar.markdown("**📝 Versió d'anàlisi i edició**")
            st.sidebar.info("☁ Els canvis es desaran al núvol")
            pwd = st.sidebar.text_input("🔑 Contrasenya d'accés:", type="password")
            
            if pwd == correct_pwd:
                st.session_state.is_authenticated = True
                st.rerun() # Reinicia per amagar el camp
            else:
                if pwd:
                    st.sidebar.error("❌ Contrasenya incorrecta.")
                else:
                    st.sidebar.warning("🔒 Cal contrasenya per accedir a l'edició.")
                st.session_state.data_source = "none"
                return pd.DataFrame(), False, origen
        # ----------------------------------------------

        try:
            # Conexión a Google Sheets usando el spreadsheet del secrets.toml
            conn = st.connection("gsheets", type=GSheetsConnection)
            worksheet = conn.read(ttl=0)  # Usará el spreadsheet configurado en secrets.toml
            
            if worksheet is not None and not worksheet.empty:
                # Això elimina files que no tenen absolutament cap dada (comunes a GSheets)
                worksheet = worksheet.dropna(how='all')

                # Processament global de dades (unificat per a tots els orígens)
                df = process_data(worksheet)
                st.session_state.data_source = "gsheets_editable"
                st.session_state.gsheets_conn = conn
                
                # Descarregar també el document Tracklog
                try:
                    df_tracklog = conn.read(worksheet="Tracklog", ttl=0)
                    df_tracklog = df_tracklog.dropna(how='all')
                    st.session_state.df_tracklog = df_tracklog
                except Exception as e_track:
                    st.sidebar.warning(f"No s'ha trobat un full anomenat 'Tracklog'. {e_track}")
                    st.session_state.df_tracklog = pd.DataFrame(columns=["Id edicio", "Data edicio", "Autor", "Codi accident", "Lloc accident", "Canvis introduits", "Actualitzat a la web"])

                sidebar_success("✅ Connexió a Google Sheets")
            else:
                sidebar_error("No s'han pogut carregar les dades de Google Sheets")
        except Exception as e:
            sidebar_error(f"Error connexió Google Sheets: {e}")
    
    elif origen == "Google Sheets (Lectura)":
        if "gs_readonly_connected" not in st.session_state:
            st.session_state.gs_readonly_connected = False

        if not st.session_state.gs_readonly_connected:
            st.sidebar.markdown("**📖 Versió exclusivament d'anàlisi**")
            st.sidebar.info("🔒 Mode només lectura (cal que el document sigui públic)")
            
        # El camp d'enllaç sempre visible
        spreadsheet_url = st.sidebar.text_input(
            "Enllaç del Google Sheets",
            value="",
            help="Enganxa l'enllaç complet del Google Sheets compartit públicament. Ex: https://docs.google.com/spreadsheets/d/ID_AQUI/edit",
            key="spreadsheet_url_readonly"
        )
        
        if not spreadsheet_url:
            st.sidebar.warning("⚠️ Cal introduir l'enllaç del spreadsheet per connectar")
            df = pd.DataFrame()
            st.session_state.data_source = "none"
            return df, False, origen
        
        try:
            df = load_from_gsheet(spreadsheet_url)
            if df is not None and not df.empty:
                st.session_state.data_source = "gsheets_readonly"
                if not st.session_state.gs_readonly_connected:
                    st.session_state.gs_readonly_connected = True
                    st.rerun()
                sidebar_success("✅ Connexió a Google Sheets")
            else:
                sidebar_error("No s'han pogut carregar les dades de Google Sheets")
        except Exception as e:
            sidebar_error(f"Error connexió Google Sheets: {e}")
            df = pd.DataFrame()
    
    if df is None:
        df = pd.DataFrame()  # DataFrame buit per permetre que el codi continuï
        st.session_state.data_source = "none"
    
    has_data = not df.empty
    return df, has_data, origen


def create_filters_sidebar(df):
    """
    Crea la secció de filtres a la barra lateral.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        Dades filtrades per mostrar
    
    Retorna:
    --------
    dict
        Diccionari amb tots els filtres seleccionats
    """
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtres per a l'anàlisi")
    
    # Selector de mètrica
    metrica = st.sidebar.selectbox(
        "Variable a representar (filtra files):",
        UI_CONFIG['metric_options'],
        index=0
    )
    
    # Tipus de gràfic temporal
    tipus_grafic_temporal = st.sidebar.radio(
        "Tipus de gràfic temporal",
        UI_CONFIG['temporal_chart_types'], 
        horizontal=True
    )
    
    # Filtres categòrics
    filters = {}
    
    # Filtres temporals
    filters["Temporada"] = st.sidebar.multiselect("Temporada", get_column_options(df, "Temporada"))
    filters["Mes"] = st.sidebar.multiselect("Mes", get_column_options(df, "Mes"))
    
    # Filtres d'activitat
    filters["Tipus activitat"] = st.sidebar.multiselect("Tipus activitat", get_column_options(df, "Tipus activitat"))
    
    # Filtres de risc
    filters["Grau de perill"] = st.sidebar.multiselect("Grau de perill", get_column_options(df, "Grau de perill"))
    
    # Filtres geogràfics
    filters["Pais"] = st.sidebar.multiselect("País", get_column_options(df, "Pais"))
    filters["Regio"] = st.sidebar.multiselect("Regió", get_column_options(df, "Regio"))
    filters["Serralada"] = st.sidebar.multiselect("Serralada", get_column_options(df, "Serralada"))
    filters["Orientacio"] = st.sidebar.multiselect("Orientació", get_column_options(df, "Orientacio"))
    
    # Filtres d'allau
    filters["Origen"] = st.sidebar.multiselect("Origen allau", get_column_options(df, "Origen"))
    filters["Progressio"] = st.sidebar.multiselect("Progressió", get_column_options(df, "Progressio"))
    filters["Desencadenant"] = st.sidebar.multiselect("Desencadenant", get_column_options(df, "Desencadenant"))
    filters["Material"] = st.sidebar.multiselect("Material", get_column_options(df, "Material"))
    filters["Altitud"] = st.sidebar.multiselect("Altitud", get_column_options(df, "Altitud"))
    filters["Mida allau"] = st.sidebar.multiselect("Mida d'allau", get_column_options(df, "Mida allau"))
    
    return {
        'filters': filters,
        'metrica': metrica,
        'tipus_grafic_temporal': tipus_grafic_temporal
    }


def create_map_style_controls():
    """
    Crea els controls d'estil de mapa i recentrat.
    
    Retorna:
    --------
    dict
        Configuració d'estil seleccionada
    """
    st.sidebar.markdown("---")
    st.sidebar.header("🗺️ Estils de Mapa")
    
    # Selector d'estil de mapa
    map_style = st.sidebar.selectbox(
        "Estil del mapa:",
        list(MAP_CONFIG['available_styles'].keys()),
        index=list(MAP_CONFIG['available_styles'].keys()).index(MAP_CONFIG['current_style'])
    )
    
    # Botó per recentrar el mapa
    center_map = st.sidebar.button("🎯 Centrar mapa")
    
    return {
        'style': map_style,
        'center_map': center_map
    }


def create_page_header():
    """
    Crea la capçalera de la pàgina amb títol i logo.
    """
    col_titol, col_logo = st.columns([4, 1])
    with col_titol:
        st.title(UI_CONFIG['app_title'])
    with col_logo:
        st.image(UI_CONFIG['logo_path'], width=UI_CONFIG['logo_width'])
    
    # Espai extra després de la capçalera (controlable)
    st.markdown("<div style='margin-bottom: -50px;'></div>", unsafe_allow_html=True)


def create_composition_chart_controls(vars_percent):
    """
    Crea els controls per als gràfics de composició.
    
    Paràmetres:
    -----------
    vars_percent : list
        Llista de variables categòriques disponibles
    
    Retorna:
    --------
    dict
        Configuració dels gràfics seleccionada
    """
    col_esquerra, col_dreta = st.columns(2)
    
    with col_esquerra:
        v1 = st.selectbox("Variable (Gràfic 1):", vars_percent, index=0, key="v_esq")
        t1 = st.radio("Tipus (Gràfic 1):", UI_CONFIG['composition_chart_types'], index=2, key="t_esq", horizontal=True)
    
    with col_dreta:
        v2 = st.selectbox("Variable (Gràfic 2):", vars_percent, index=2, key="v_dret")
        t2 = st.radio("Tipus (Gràfic 2):", UI_CONFIG['composition_chart_types'], index=0, key="t_dret", horizontal=True)
    
    return {
        'var1': v1,
        'var2': v2,
        'type1': t1,
        'type2': t2
    }


def sidebar_error(msg):
    """
    Mostra un missatge d'error a la barra lateral.
    
    Paràmetres:
    -----------
    msg : str
        Missatge d'error a mostrar
    """
    st.sidebar.markdown(
        f"<div style='background:{COLORS['error_bg']}; color:{COLORS['error_text']}; padding:10px; border-radius:6px; border:1px solid {COLORS['error_border']};'>{msg}</div>",
        unsafe_allow_html=True
    )


def sidebar_success(msg):
    """
    Mostra un missatge d'èxit a la barra lateral.
    
    Paràmetres:
    -----------
    msg : str
        Missatge d'èxit a mostrar
    """
    st.sidebar.markdown(
        f"<div style='background:{COLORS['success_bg']}; color:{COLORS['success_text']}; padding:10px; border-radius:6px; border:1px solid {COLORS['success_border']};'>{msg}</div>",
        unsafe_allow_html=True
    )


def sidebar_info(msg):
    """
    Mostra un missatge d'informació a la barra lateral.
    
    Paràmetres:
    -----------
    msg : str
        Missatge d'informació a mostrar
    """
    st.sidebar.markdown(
        f"<div style='background:{COLORS['info_bg']}; color:{COLORS['info_text']}; padding:10px; border-radius:6px; border:1px solid {COLORS['info_border']};'>{msg}</div>",
        unsafe_allow_html=True
    )


def create_map_interaction_panel():
    """
    Panel simplificado para no interferir con el modo edición.
    Solo muestra información de accidentes seleccionados, no gestiona clics.
    """
    # Solo mostramos información si hay un accidente SELECCIONADO (punto existente)
    # pero NO si es un clic en el vacío, para dejar paso al modo edición.
    if 'selected_accident' in st.session_state and st.session_state.selected_accident is not None:
        accident = st.session_state.selected_accident
        st.markdown("### 📍 Detalls de l'Accident")
        
        # Organitzar informació en columnes
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📍 Localització**")
            if 'Lloc' in accident:
                st.write(accident['Lloc'])
            if 'Pais' in accident:
                st.write(f"País: {accident['Pais']}")
            if 'Regio' in accident:
                st.write(f"Regió: {accident['Regio']}")
            if 'Serralada' in accident:
                st.write(f"Serralada: {accident['Serralada']}")
        
        with col2:
            st.markdown("**📅 Data i Risc**")
            if 'Data' in accident:
                # Formatear fecha directamente desde la columna Data
                data_format = pd.to_datetime(accident['Data']).strftime('%d/%m/%Y')
                st.write(f"Data: {data_format}")
            if 'Temporada' in accident:
                st.write(f"Temporada: {accident['Temporada']}")
            if 'Grau de perill' in accident:
                st.write(f"Perill: {accident['Grau de perill']}")
            if 'Altitud' in accident:
                st.write(f"Altitud: {accident['Altitud']}")
        
        with col3:
            st.markdown("**⚠️ Allau i Víctimes**")
            if 'Mida allau' in accident:
                st.write(f"Mida: {accident['Mida allau']}")
            if 'Morts' in accident:
                st.write(f"Morts: {accident['Morts']}")
            if 'Ferits' in accident:
                st.write(f"Ferits: {accident['Ferits']}")
            if 'Arrossegats' in accident:
                st.write(f"Arrossegats: {accident['Arrossegats']}")
        
        # Detalls addicionals
        with st.expander("📋 Veure tots els detalls"):
            # Mostrar totes las columnas disponibles
            for key, value in accident.items():
                if key not in ['Lloc', 'Pais', 'Regio', 'Serralada', 'Data', 
                               'Temporada', 'Grau de perill', 'Altitud', 'Mida allau',
                               'Morts', 'Ferits', 'Arrossegats']:
                    st.write(f"**{key}:** {value}")
        
        # Botó d'edició
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            st.button("📝 Editar accident", key="edit_accident", width='stretch')
    else:
        # Si no hay accidente seleccionado, no mostramos nada aquí para no ensuciar la UI
        # El formulario de "Nuevo accidente" ya aparecerá desde el archivo principal
        pass


def create_footer():
    """
    Crea el peu de pàgina.
    """
    st.markdown("---")
    st.markdown(HTML_TEMPLATES['footer'], unsafe_allow_html=True)


def show_empty_data_message(has_data):
    """
    Mostra missatges apropiats quan no hi ha dades.
    
    Paràmetres:
    -----------
    has_data : bool
        Indica si hi ha dades carregades
    """
    if not has_data:
        # No hi ha dades carregades
        pass
    else:
        # Hi ha dades però cap coincidència amb filtres
        st.warning("⚠️ Cap punt coincideix amb els filtres.")
