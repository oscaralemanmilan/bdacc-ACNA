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
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

# Importacions dels mòduls modulars
from src.data_processing import VARS_PERCENT, apply_filters
from src.visualization import (
    create_map_layer, create_temporal_chart, create_composition_charts,
    create_kpi_dashboard, ensure_pyarrow_compatibility, render_kpi_boxes, create_data_table,
    get_simplified_tooltip_html
)
from src.ui_components import (
    inject_custom_styles, create_data_source_sidebar, create_filters_sidebar,
    create_map_controls, create_map_style_controls, create_map_controls_with_styles, create_page_header, 
    create_composition_chart_controls, sidebar_error, sidebar_success, 
    sidebar_info, create_footer, show_empty_data_message
)
# Importar nous mòduls Folium
from src.map_folium import create_folium_map, get_folium_html
from src.ui_folium import create_folium_controls
from config.settings import PAGE_CONFIG, HTML_TEMPLATES, MAP_CONFIG

# Importar streamlit_folium per interactivitat
import streamlit_folium


def main():
    """
    Funció principal de l'aplicació.
    """
    # Configuració de la pàgina
    st.set_page_config(**PAGE_CONFIG)
    
    # Injectar estils CSS personalitzats
    inject_custom_styles()
    
    # Inicialitzar session_state
    if 'selected_accident' not in st.session_state:
        st.session_state.selected_accident = None
    if 'clicked_coords' not in st.session_state:
        st.session_state.clicked_coords = None
    if 'map_system' not in st.session_state:
        st.session_state.map_system = 'Folium (Avançat)'  # Per defecte Folium
    
    # Capçalera de la pàgina
    create_page_header()
    
    # Barra lateral - Origen de dades
    df, has_data, origen = create_data_source_sidebar()
    
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
        # Secció del mapa (segons sistema seleccionat)
        if st.session_state.map_system == 'Folium (Avançat)':
            render_folium_map_section(dff)
        else:
            render_map_section(dff)
        
        # Secció de KPIs (just sota del mapa)
        render_kpi_section(dff)
        
        # Secció d'informació de selecció (sota dels KPIs)
        if st.session_state.map_system == 'Folium (Avançat)':
            # Función eliminada - ahora se usa streamlit_folium para interactividad
            # La lógica de edición de puntos se retomará más adelante con nuevo enfoque
            pass
        
        # Secció de gràfics temporals
        render_temporal_chart_section(dff, filter_config['tipus_grafic_temporal'])
        
        # Secció de gràfics de composició
        render_composition_charts_section(dff)
        
        # Secció de taula de dades
        render_data_table_section(dff)
    
    # Peu de pàgina
    create_footer()


def render_folium_map_section(dff):
    """
    Renderitza la secció del mapa interactiu amb Folium sincronitzat al primer clic.
    """
    # 1. Inicializar estados
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'new_point_coords' not in st.session_state:
        st.session_state.new_point_coords = None
    if 'last_processed_click' not in st.session_state:
        st.session_state.last_processed_click = None

    # 2. Crear los controles
    folium_config = create_folium_controls()
    
    # 3. Preparar el mapa
    folium_map = create_folium_map(
        dff,
        show_points=folium_config['show_points'],
        auto_fit=False, 
        edit_mode=st.session_state.edit_mode,
        new_point=st.session_state.new_point_coords 
    )

    # 4. RENDERIZAR EL MAPA
    from streamlit_folium import st_folium
    output = st_folium(
        folium_map,
        key="mapa_principal",
        width='stretch',
        height=500,
        returned_objects=["last_map_click", "map_edit_mode_active"]
    )

    # 5. LÓGICA DE CAPTURA INMEDIATA
    if output:
        # Sincronizar Modo Edición
        if "map_edit_mode_active" in output:
            new_val = output["map_edit_mode_active"]
            if new_val != st.session_state.edit_mode:
                # Si se está activando el modo edición, minimizar mapa si está en pantalla completa
                if new_val and not st.session_state.edit_mode:
                    # Activar modo edición - minimizar mapa si está en pantalla completa
                    st.session_state.edit_mode = new_val
                    st.session_state.force_minimize_map = True
                    st.rerun()
                elif not new_val and st.session_state.edit_mode:
                    # Si se está intentando desactivar el modo edición y hay un formulario abierto
                    if st.session_state.new_point_coords is not None:
                        # Cancelar directamente el formulario sin aviso
                        st.session_state.edit_mode = False
                        st.session_state.new_point_coords = None
                        st.session_state.last_processed_click = None
                        st.rerun()
                    else:
                        # Cambio normal de modo edición
                        st.session_state.edit_mode = new_val
                        st.rerun()

        # Sincronizar Clic
        if "last_map_click" in output and output["last_map_click"]:
            click_data = output["last_map_click"]
            # Usamos el timestamp 't' de JS para asegurar que es un clic nuevo
            click_id = f"c_{click_data.get('lat')}_{click_data.get('lng')}_{click_data.get('t', 0)}"
            
            if st.session_state.last_processed_click != click_id:
                st.session_state.new_point_coords = {'lat': click_data['lat'], 'lng': click_data['lng']}
                st.session_state.last_processed_click = click_id
                st.rerun() # Recarga instantánea para mostrar el formulario

    
    # 5.6. MINIMIZAR MAPA AUTOMÁTICAMENTE (si se activó edición)
    if 'force_minimize_map' in st.session_state and st.session_state.force_minimize_map:
        # JavaScript para salir del modo pantalla completa del mapa
        st.markdown("""
        <script>
        // Salir del modo pantalla completa del mapa
        setTimeout(function() {
            // Buscar botón de fullscreen y hacer clic si está activo
            var fullscreenBtn = document.querySelector('.leaflet-control-fullscreen-button');
            if (fullscreenBtn && fullscreenBtn.classList.contains('leaflet-fullscreen-on')) {
                fullscreenBtn.click();
            }
            // También intentar salir de fullscreen del documento
            if (document.fullscreenElement) {
                document.exitFullscreen();
            }
        }, 100);
        </script>
        """, unsafe_allow_html=True)
        
        # Limpiar el estado después de ejecutar
        st.session_state.force_minimize_map = False
    
    # 6. FORMULARIO (siempre debajo del mapa)
    if st.session_state.new_point_coords and st.session_state.edit_mode:
        render_accident_form(st.session_state.new_point_coords)


def render_accident_form(clicked_coords):
    """
    Renderiza el formulario completo de accidente con todas las columnas originales.
    """
    # Aviso nativo del navegador para prevenir salida accidental
    st.markdown("""
    <script>
    // Prevenir salida accidental cuando hay formulario abierto
    window.addEventListener('beforeunload', function(e) {
        // Verificar si hay un formulario activo y si estamos en modo edición
        var formElements = document.querySelectorAll('form[data-testid="stForm"]');
        var editModeActive = false;
        
        // Verificar si el modo edición está activo (buscando coordenadas en el estado)
        try {
            var coordsText = document.body.textContent.includes('Coordenades:');
            if (coordsText) {
                editModeActive = true;
            }
        } catch(e) {
            // Ignorar errores
        }
        
        if (formElements.length > 0 && editModeActive) {
            e.preventDefault();
            e.returnValue = 'Desa el formulari o cancel·la\'l abans de sortir del mode edició.';
            return e.returnValue;
        }
    });
    </script>
    """, unsafe_allow_html=True)
    
    with st.form("accident_form"):
        st.subheader("📝 Detalls del nou accident")
        st.info(f"📍 Coordenades: {clicked_coords['lat']:.6f}, {clicked_coords['lng']:.6f}")
        
        # Cargar datos existentes para obtener opciones
        try:
            df = load_data()
        except:
            df = None
        
        # Campos del formulario organizados en columnas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Datos básicos
            id_accident = st.text_input("🆔 ID", value="", help="Identificador únic de l'accident")
            codi = st.text_input("🔢 Codi", value="", help="Codi de referència")
            
            # Temporal y geográfico
            temporada = st.selectbox("�️ Temporada", 
                                   options=get_column_options(df, "Temporada") if df is not None else ["Desconegut"],
                                   help="Temporada de l'accident")
            data_accident = st.date_input("📅 Data", value=pd.Timestamp.now().date(), help="Data de l'accident")
            lloc = st.text_input("📍 Lloc", value=f"Accident en {clicked_coords['lat']:.4f}", help="Descripció del lloc")
            
            # Ubicación
            pais = st.selectbox("🏳️ País", 
                              options=get_column_options(df, "Pais") if df is not None else ["Desconegut"],
                              help="País on va ocórrer l'accident")
            regio = st.selectbox("🗺️ Regió", 
                                options=get_column_options(df, "Regio") if df is not None else ["Desconegut"],
                                help="Regió geogràfica")
            serralada = st.selectbox("⛰️ Serralada", 
                                    options=get_column_options(df, "Serralada") if df is not None else ["Desconegut"],
                                    help="Serralada on va ocórrer")
            orientacio = st.selectbox("🧭 Orientació", 
                                    options=get_column_options(df, "Orientacio") if df is not None else ["Desconegut"],
                                    help="Orientació de la pendent")
            altitud = st.selectbox("📏 Altitud", 
                                  options=get_column_options(df, "Altitud") if df is not None else ["Desconegut"],
                                  help="Rang d'altitud")
            grup = st.text_input("👥 Grup", value="", help="Grup o equip afectat")
        
        with col2:
            # Actividad y accidente
            tipus_activitat = st.selectbox("🎿 Tipus activitat", 
                                         options=get_column_options(df, "Tipus activitat") if df is not None else ["Desconegut"],
                                         help="Tipus d'activitat que es practicava")
            desenc = st.text_input("⚡ Desenc", value="", help="Desencadenant principal")
            origen = st.selectbox("🌊 Origen", 
                                options=get_column_options(df, "Origen") if df is not None else ["Desconegut"],
                                help="Origen de l'allau")
            progressio = st.selectbox("📈 Progressió", 
                                     options=get_column_options(df, "Progressio") if df is not None else ["Desconegut"],
                                     help="Progressió de l'allau")
            desencadenant = st.selectbox("🎯 Desencadenant", 
                                        options=get_column_options(df, "Desencadenant") if df is not None else ["Desconegut"],
                                        help="Factor desencadenant")
            neu = st.text_input("❄️ Neu", value="", help="Condicions de neu")
            material = st.selectbox("🔧 Material", 
                                   options=get_column_options(df, "Material") if df is not None else ["Desconegut"],
                                   help="Material implicat")
        
        with col3:
            # Víctimas y peligrosidad
            arrossegats = st.number_input("🏃 Arrossegats", min_value=0, value=0, step=1, help="Nombre de persones arrossegades")
            ferits = st.number_input("� Ferits", min_value=0, value=0, step=1, help="Nombre de persones ferides")
            morts = st.number_input("💀 Morts", min_value=0, value=0, step=1, help="Nombre de persones mortes")
            grau_perill = st.selectbox("⚠️ Grau de perill", 
                                      options=get_column_options(df, "Grau de perill") if df is not None else ["Desconegut"],
                                      help="Nivell de perill de l'accident")
            mida_allau = st.selectbox("📏 Mida allau", 
                                     options=get_column_options(df, "Mida allau") if df is not None else ["Desconegut"],
                                     help="Mida de l'allau")
            
            # Información adicional
            observacions = st.text_area("📝 Observacions", value="", help="Observacions addicionals", height=100)
            link = st.text_input("🔗 Link", value="", help="Enllaç a informació addicional")
            fotos = st.text_input("📸 Fotos", value="", help="Referència a fotos o arxiu")
        
        # Botón de envío del formulario
        col_submit, col_cancel = st.columns([1, 1])
        
        with col_submit:
            submitted = st.form_submit_button("📝 Confirmar i desar")
        
        with col_cancel:
            cancelled = st.form_submit_button("🚫 Cancel·lar")
        
        if cancelled:
            # Limpiar coordenadas seleccionadas
            st.session_state.new_point_coords = None
            st.session_state.edit_mode = False
            st.rerun()
            
        if submitted:
            try:
                # Validar coordenadas
                coords_valid = (
                    clicked_coords['lat'] is not None and 
                    clicked_coords['lng'] is not None and
                    clicked_coords['lat'] != 0 and
                    clicked_coords['lng'] != 0
                )
                
                if not coords_valid:
                    st.error("❌ Les coordenades no són vàlides")
                    return
                
                # Guardar en Excel con todos los campos
                guardar_accident_excel(
                    coords=clicked_coords,
                    id_accident=id_accident,
                    codi=codi,
                    temporada=temporada,
                    data=data_accident,
                    lloc=lloc,
                    pais=pais,
                    regio=regio,
                    serralada=serralada,
                    orientacio=orientacio,
                    altitud=altitud,
                    grup=grup,
                    desenc=desenc,
                    tipus_activitat=tipus_activitat,
                    origen=origen,
                    progressio=progressio,
                    desencadenant=desencadenant,
                    neu=neu,
                    material=material,
                    arrossegats=arrossegats,
                    ferits=ferits,
                    morts=morts,
                    grau_perill=grau_perill,
                    mida_allau=mida_allau,
                    observacions=observacions,
                    link=link,
                    fotos=fotos
                )
                
                # Limpiar estado del formulario pero mantener modo edición activo
                st.session_state.new_point_coords = None
                st.session_state.last_processed_click = None
                # NOTA: No desactivar edit_mode para permitir crear más puntos
                
                st.success("✅ Accident guardat correctament!")
                st.cache_data.clear()
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error en desar a l'Excel: {str(e)}")


def generate_unique_id(df):
    """
    Genera un ID únic per a un nou accident seguint la seqüència existent.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame existent amb accidents
        
    Retorna:
    --------
    str
        ID únic generat
    """
    if df.empty:
        return f"ACC_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Buscar la columna de ID (puede ser 'id', 'ID', o 'Codi')
    id_column = None
    for col in ['id', 'ID', 'Codi']:
        if col in df.columns:
            id_column = col
            break
    
    if id_column is None:
        return f"ACC_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Buscar IDs numèrics existents
    max_id = 0
    for id_val in df[id_column]:
        if isinstance(id_val, str):
            # Buscar prefijos ACC_ o numéricos
            if id_val.startswith('ACC_'):
                try:
                    num_part = id_val.replace('ACC_', '')
                    if num_part.isdigit():
                        num_id = int(num_part)
                        if num_id > max_id:
                            max_id = num_id
                except:
                    continue
            elif id_val.isdigit():
                try:
                    num_id = int(id_val)
                    if num_id > max_id:
                        max_id = num_id
                except:
                    continue
    
    # Generar nou ID
    new_id = max_id + 1
    return f"ACC_{new_id}"


def guardar_accident_excel(coords, id_accident="", codi="", temporada="", data="", lloc="", 
                          pais="", regio="", serralada="", orientacio="", altitud="", grup="",
                          desenc="", tipus_activitat="", origen="", progressio="", desencadenant="",
                          neu="", material="", arrossegats=0, ferits=0, morts=0, grau_perill="",
                          mida_allau="", observacions="", link="", fotos=""):
    """
    Funció per guardar un nou accident a l'Excel o Google Sheets amb tots els camps.
    Paràmetres:
    -----------
    coords : dict
        Coordenades {'lat': valor, 'lng': valor}
    Los demás parámetros corresponden a todas las columnas del Excel
    """
    try:
        # Detectar fuente de datos actual
        data_source = st.session_state.get('data_source', 'none')
        is_gsheets_editable = data_source == 'gsheets_editable'
        
        # Debug: mostrar fuente de datos
        st.write(f"🔍 Fuente de datos detectada: {data_source}")
        st.write(f"🔍 Es Google Sheets editable: {is_gsheets_editable}")
        
        # Obtener DataFrame actual según la fuente
        if is_gsheets_editable:
            # Obtener datos de Google Sheets usando conexión directa
            try:
                conn = st.connection("gsheets", type=GSheetsConnection)
                with st.spinner("Carregant dades de Google Sheets..."):
                    df_existing = conn.read()
            except Exception as e:
                st.error(f"❌ Error connectant a Google Sheets: {str(e)}")
                return
        else:
            # Leer el Excel existente
            file_path = "data/bd_accidents_200726_net_c.xlsx"
            
            # Crear backup de seguridad
            import shutil
            backup_path = f"data/backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}_bd_accidents.xlsx"
            shutil.copy2(file_path, backup_path)
            
            # Leer datos existentes
            df_existing = pd.read_excel(file_path, engine="openpyxl")
        
        # Generar ID único si no se proporciona
        if not id_accident:
            id_accident = generate_unique_id(df_existing)
        
        # Crear nueva fila con todos los campos
        new_row = {
            'id': id_accident,
            'Codi': codi if codi else "AUTO",
            'Temporada': temporada if temporada else "Desconegut",
            'Data': pd.to_datetime(data) if data else pd.Timestamp.now(),
            'Lloc': lloc if lloc else f"Accident ({coords['lat']:.6f}, {coords['lng']:.6f})",
            'Latitud': float(coords['lat']),
            'Longitud': float(coords['lng']),
            'Tipus activitat': tipus_activitat if tipus_activitat else "Desconegut",
            'Pais': pais if pais else "Desconegut",
            'Regio': regio if regio else "Desconegut",
            'Serralada': serralada if serralada else "Desconegut",
            'Orientacio': orientacio if orientacio else "Desconegut",
            'Altitud': altitud if altitud else "Desconegut",
            'Grup': grup if grup else "Desconegut",
            'Desenc': desenc if desenc else "Desconegut",
            'Arrossegats': int(arrossegats),
            'Ferits': int(ferits),
            'Morts': int(morts),
            'Grau de perill': grau_perill if grau_perill else "Desconegut",
            'Mida allau': mida_allau if mida_allau else "Desconegut",
            'Origen': origen if origen else "Desconegut",
            'Progressio': progressio if progressio else "Desconegut",
            'Desencadenant': desencadenant if desencadenant else "Desconegut",
            'Neu': neu if neu else "Desconegut",
            'Material': material if material else "Desconegut",
            'Observacions': observacions if observacions else "",
            'Link': link if link else "",
            'Fotos': fotos if fotos else ""
        }
        
        # Añadir nueva fila
        df_new = pd.DataFrame([new_row])
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        
        # Guardar según la fuente de datos
        if is_gsheets_editable:
            # Sincronizar con Google Sheets
            with st.spinner("Desant dades al Google Sheets..."):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    
                    # Asegurar compatibilidad completa con PyArrow
                    df_final = ensure_pyarrow_compatibility(df_final)
                    
                    # Verificar y forzar formato de columnas numéricas y de fecha
                    df_final['Latitud'] = pd.to_numeric(df_final['Latitud'], errors='coerce')
                    df_final['Longitud'] = pd.to_numeric(df_final['Longitud'], errors='coerce')
                    df_final['Data'] = pd.to_datetime(df_final['Data'], errors='coerce', dayfirst=True)
                    df_final['Morts'] = pd.to_numeric(df_final['Morts'], errors='coerce').fillna(0).astype(int)
                    df_final['Ferits'] = pd.to_numeric(df_final['Ferits'], errors='coerce').fillna(0).astype(int)
                    df_final['Arrossegats'] = pd.to_numeric(df_final['Arrossegats'], errors='coerce').fillna(0).astype(int)
                    
                    # Actualizar Google Sheets
                    conn.update(worksheet="Accidents", data=df_final)
                    st.cache_data.clear()
                    st.success("✅ Dades desades correctament al núvol!")
                    
                except Exception as e:
                    st.error(f"❌ Error guardant a Google Sheets: {str(e)}")
                    return
        else:
            # Guardar con engine openpyxl
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Accidents')
            
            st.success(f"✅ Accident guardat correctament! Backup creat a: {backup_path}")
        
        # Limpiar caché
        st.cache_data.clear()
        
    except FileNotFoundError:
        st.error("❌ No s'ha trobat el fitxer Excel. Assegura't que 'data/bd_accidents_200726_net_c.xlsx' existeix.")
    except PermissionError:
        st.error("❌ No es pot escriure al fitxer. Pot estar obert en un altre programa.")
    except Exception as e:
        if is_gsheets_editable:
            st.error(f"❌ Error guardant a Google Sheets: {str(e)}")
        else:
            st.error(f"❌ Error en desar a l'Excel: {str(e)}")
            # Intentar restaurar del backup si existe
            try:
                if 'backup_path' in locals():
                    shutil.copy2(backup_path, file_path)
                    st.info("🔄 S'ha restaurat el fitxer original des del backup.")
            except:
                pass 

def render_map_section(dff):
    """
    Renderitza la secció del mapa interactiu (Pydeck - original).
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades per mostrar
    """
    # Controls del mapa integrats amb la vista
    map_config = create_map_controls_with_styles()
    
    # Crea el mapa amb l'estil seleccionat
    deck = create_map_layer(
        dff,
        show_points=map_config['show_points'],
        show_heatmap=map_config['show_heatmap'],
        point_radius=map_config['point_radius'],
        point_opacity=map_config['point_opacity'],
        heat_radius=map_config['heat_radius'],
        heat_intensity=map_config['heat_intensity'],
        map_style=map_config['style']
    )
    
    if deck:
        st.pydeck_chart(deck, width='stretch')


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
        st.plotly_chart(fig, width='stretch')


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
            st.plotly_chart(fig1, width='stretch')
        
        with col_dreta:
            st.plotly_chart(fig2, width='stretch')


def render_data_table_section(dff):
    """
    Renderitza la secció de la taula de dades.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades
    """
    # Obtenir la ruta del fitxer original
    original_file_path = st.session_state.get('current_file_path', 'data/bd_accidents_200726_net_c.xlsx')
    
    with st.expander("📄 Dades filtrades", expanded=True):  # expanded=True per mantenir-la sempre visible
        create_data_table(dff, original_file_path)


if __name__ == "__main__":
    main()
