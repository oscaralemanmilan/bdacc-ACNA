
"""
================================================================================
Base de Dades d'Accidents per Allaus - ACNA
================================================================================
Fitxer principal (main)
"""

import shutil
from datetime import date

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

from config.settings import HTML_TEMPLATES, MAP_CONFIG, PAGE_CONFIG
from src.data_processing import VARS_PERCENT, apply_filters, get_column_options, load_data
from src.map_folium import create_folium_map, get_folium_html
from src.ui_components import (
    create_composition_chart_controls,
    create_data_source_sidebar,
    create_filters_sidebar,
    create_footer,
    create_page_header,
    inject_custom_styles,
    show_empty_data_message,
)
from src.ui_folium import create_folium_controls
from src.visualization import (
    create_composition_charts,
    create_data_table,
    create_kpi_dashboard,
    create_temporal_chart,
    ensure_pyarrow_compatibility,
    render_kpi_boxes,
    render_tracklog_section
)





def main():
    """Funció principal de l'aplicació."""

    st.set_page_config(**PAGE_CONFIG)
    inject_custom_styles()

    # --- INICIALITZACIÓ DE SESSION STATE ---
    defaults = {
        'selected_accident': None,
        'clicked_coords': None,
        'edit_mode': False,
        'new_point_coords': None,
        'last_processed_click': None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


    # Inicialització del DataFrame oficial (comença buit per forçar selecció d'origen)
    if 'df_oficial' not in st.session_state:
        st.session_state.df_oficial = pd.DataFrame()

    create_page_header()

    # --- ORIGEN DE DADES I FILTRES ---
    df, has_data, origen = create_data_source_sidebar()

    if has_data and df is not None:
        st.session_state.df_oficial = df

    if has_data and not st.session_state.df_oficial.empty:
        filter_config = create_filters_sidebar(st.session_state.df_oficial)
        st.session_state.current_filters = filter_config
        st.session_state.temporal_chart_type = filter_config['tipus_grafic_temporal']

        dff = apply_filters(
            st.session_state.df_oficial,
            filter_config['filters'],
            filter_config['metrica']
        )
    else:
        dff = pd.DataFrame()
        filter_config = {'metrica': 'Accidents', 'tipus_grafic_temporal': 'Barres'}
        st.session_state.current_filters = filter_config
        st.session_state.temporal_chart_type = 'Barres'

    # --- RENDERITZAT PRINCIPAL ---
    if dff.empty:
        show_empty_data_message(has_data)
    else:
        render_folium_map_section(dff)
        render_charts_section(dff)
        render_data_table_section(dff)

    create_footer()


# ---------------------------------------------------------------------------
# SECCIONS DEL MAPA
# ---------------------------------------------------------------------------

@st.fragment
def render_map_zone(dff):
    from streamlit_folium import st_folium

    folium_config = create_folium_controls()

    folium_map = create_folium_map(
        dff,
        show_points=folium_config['show_points'],
        auto_fit=False,
        edit_mode=st.session_state.edit_mode,
        new_point=st.session_state.new_point_coords,
        allow_edit=(st.session_state.get('data_source') == 'gsheets_editable')
    )

    output = st_folium(
        folium_map,
        key="mapa_principal",
        width='stretch',
        height=500,
        returned_objects=["last_map_click", "map_edit_mode_active"]
    )

    if output:
        if "map_edit_mode_active" in output:
            new_val = output["map_edit_mode_active"]
            if new_val != st.session_state.edit_mode:
                if new_val and not st.session_state.edit_mode:
                    st.session_state.edit_mode = new_val
                    st.session_state.force_minimize_map = True
                    st.rerun()
                elif not new_val and st.session_state.edit_mode:
                    st.session_state.edit_mode = False
                    st.session_state.new_point_coords = None
                    st.session_state.last_processed_click = None
                    st.rerun()

        if output.get("last_map_click"):
            click_data = output["last_map_click"]
            click_id = (
                f"c_{click_data.get('lat')}"
                f"_{click_data.get('lng')}"
                f"_{click_data.get('t', 0)}"
            )
            if st.session_state.last_processed_click != click_id:
                st.session_state.new_point_coords = {
                    'lat': click_data['lat'],
                    'lng': click_data['lng']
                }
                st.session_state.last_processed_click = click_id
                st.rerun()

    if st.session_state.get('force_minimize_map'):
        st.markdown("""
        <script>
        setTimeout(function() {
            var btn = document.querySelector('.leaflet-control-fullscreen-button');
            if (btn && btn.classList.contains('leaflet-fullscreen-on')) { btn.click(); }
            if (document.fullscreenElement) { document.exitFullscreen(); }
        }, 100);
        </script>
        """, unsafe_allow_html=True)
        st.session_state.force_minimize_map = False

    if st.session_state.new_point_coords and st.session_state.edit_mode:
        render_accident_form(st.session_state.new_point_coords)


def render_folium_map_section(dff):
    render_map_zone(dff)


# ---------------------------------------------------------------------------
# FORMULARI D'ACCIDENT NOU
# ---------------------------------------------------------------------------

def render_accident_form(clicked_coords):
    with st.form("accident_form"):
        st.subheader("📝 Detalls del nou accident")
        st.info(f"📍 Coordenades: {clicked_coords['lat']:.6f}, {clicked_coords['lng']:.6f}")

        df_ref = st.session_state.get('df_oficial')
        nou_codi_suggerit = generate_next_codi(df_ref)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("###### 🆔 Identificadors")
            codi = st.number_input("Codi (Auto)", value=nou_codi_suggerit, step=1)
            id_accident = st.text_input("id web", value="")
            
            st.markdown("###### 📆 Dades temporals")
            temp_options = [""] + list(get_column_options(df_ref, "Temporada")) if df_ref is not None else [""]
            temporada = st.selectbox("Temporada", options=temp_options, index=(len(temp_options)-1))
            data_accident = st.date_input("Data", value=pd.Timestamp.now().date(), format="DD/MM/YYYY")

            st.markdown("###### 🌍 Dades geogràfiques")
            lloc = st.text_input("📍 Lloc", value=f"Nou accident ({clicked_coords['lat']:.4f}, {clicked_coords['lng']:.4f})")
            latitud = st.number_input("Latitud", value=clicked_coords['lat'], format="%.6f")
            longitud = st.number_input("Longitud", value=clicked_coords['lng'], format="%.6f")  
            
            pais_opts = [""] + list(get_column_options(df_ref, "Pais")) if df_ref is not None else [""]
            pais = st.selectbox("País", options=pais_opts, index=0)
            regio_opts = [""] + list(get_column_options(df_ref, "Regio")) if df_ref is not None else [""]
            regio = st.selectbox("Regió", options=regio_opts, index=0)
            serr_opts = [""] + list(get_column_options(df_ref, "Serralada")) if df_ref is not None else [""]
            serralada = st.selectbox("Serralada", options=serr_opts, index=0)
            orient_opts = [""] + list(get_column_options(df_ref, "Orientacio")) if df_ref is not None else [""]
            orientacio = st.selectbox("Orientació", options=orient_opts, index=0)
            alt_opts = [""] + list(get_column_options(df_ref, "Altitud")) if df_ref is not None else [""]
            altitud = st.selectbox("Altitud", options=alt_opts, index=0)

        with col2:
            st.markdown("###### 🎿 Activitat i danys")
            act_opts = [""] + list(get_column_options(df_ref, "Tipus activitat")) if df_ref is not None else [""]
            tipus_activitat = st.selectbox("Tipus activitat", options=act_opts, index=0)
            mat_opts = [""] + list(get_column_options(df_ref, "Material")) if df_ref is not None else [""]
            material = st.selectbox("Material", options=mat_opts, index=0)
            prog_opts = [""] + list(get_column_options(df_ref, "Progressio")) if df_ref is not None else [""]
            progressio = st.selectbox("Progressió", options=prog_opts, index=0)
            
            grup = st.number_input("Grup", min_value=0, value=0)            
            desenc = st.number_input("Desenc (Sobrecàrrega)", min_value=0, value=0)
            arrossegats = st.number_input("Arrossegats", min_value=0, value=0)
            ferits = st.number_input("Ferits", min_value=0, value=0)
            morts = st.number_input("Morts", min_value=0, value=0)

            st.markdown("###### ❄️ Perill, neu i allaus")
            perill_opts = [""] + list(get_column_options(df_ref, "Grau de perill")) if df_ref is not None else [""]
            grau_perill = st.selectbox("⚠ Grau de perill", options=perill_opts, index=0)
            orig_opts = [""] + list(get_column_options(df_ref, "Origen")) if df_ref is not None else [""]
            origen = st.selectbox("Origen", options=orig_opts, index=0)
            desenc_opts = [""] + list(get_column_options(df_ref, "Desencadenant")) if df_ref is not None else [""]
            desencadenant = st.selectbox("Desencadenant", options=desenc_opts, index=0)
            neu_opts = [""] + list(get_column_options(df_ref, "Neu")) if df_ref is not None else [""]
            neu = st.selectbox("Neu", options=neu_opts, index=0)
            mida_opts = [""] + list(get_column_options(df_ref, "Mida allau")) if df_ref is not None else [""]
            mida_allau = st.selectbox("Mida allau", options=mida_opts, index=0)
            
        with col3:    
            st.markdown("###### 📂 Altres")
            observacions = st.text_area("📝 Observacions", value="", height=100)
            link = st.text_input("🔗 Link", value="")
            fotos = st.text_input("📸 Fotos", value="")

        col_submit, col_cancel = st.columns(2)
        if col_cancel.form_submit_button("❌ Cancel·lar", use_container_width=True):
            st.session_state.new_point_coords = None
            st.session_state.edit_mode = False
            st.rerun()

        if col_submit.form_submit_button("✅ Confirmar i desar", use_container_width=True):
            guardar_accident(
                id_accident=id_accident, codi=codi, temporada=temporada,                
                data=data_accident, lloc=lloc, latitud=latitud, longitud=longitud,
                pais=pais, regio=regio, serralada=serralada, orientacio=orientacio, altitud=altitud,
                grup=grup, desenc=desenc, tipus_activitat=tipus_activitat,
                origen=origen, progressio=progressio, desencadenant=desencadenant,
                neu=neu, material=material, arrossegats=arrossegats,
                ferits=ferits, morts=morts, grau_perill=grau_perill,
                mida_allau=mida_allau, observacions=observacions,
                link=link, fotos=fotos
            )


# ---------------------------------------------------------------------------
# LÒGICA DE GUARDAT (CORREGIDA)
# ---------------------------------------------------------------------------

def generate_next_codi(df):
    if df is None or df.empty or 'Codi' not in df.columns:
        return 1
    codis_numerics = pd.to_numeric(df['Codi'], errors='coerce').dropna()
    return int(codis_numerics.max() + 1) if not codis_numerics.empty else 1


def guardar_accident(id_accident="", codi=None, temporada="", data=None,
                     lloc="", pais="", regio="", serralada="", orientacio="",
                     altitud="", grup=None, desenc=None, tipus_activitat=None, 
                     latitud=None, longitud=None, 
                     origen="", progressio="", desencadenant="", neu="", material="",
                     arrossegats=None, ferits=None, morts=None, grau_perill="",
                     mida_allau="", observacions="", link="", fotos=""):
    
    if codi is None:
        codi = generate_next_codi(st.session_state.df_oficial)

    data_source = st.session_state.get('data_source', 'none')
    is_gsheets = data_source == 'gsheets_editable'
    file_path = "data/bd_accidents_200726_net_c.xlsx"

    try:
        if not is_gsheets:
            st.error("❌ Només es permet desar canvis si estàs connectat a Google Sheets (Editable).")
            return
            
        conn = st.session_state.get('gsheets_conn')
        df_existing = conn.read()

        # Neteja de noms de columnes per evitar l'error 'Observacions '
        df_existing.columns = df_existing.columns.str.strip()

        # Format de data
        data_str = data.strftime('%d/%m/%Y') if isinstance(data, date) else pd.Timestamp.now().strftime('%d/%m/%Y')

        new_row = {
            'id': id_accident or None,
            'Codi': int(codi),
            'Temporada': temporada or "",
            'Data': data_str,
            'Lloc': lloc or "Accident sense nom",
            'Latitud': float(latitud), 
            'Longitud': float(longitud),
            'Tipus activitat': tipus_activitat or "",
            'Pais': pais or "",
            'Regio': regio or "",
            'Serralada': serralada or "",
            'Orientacio': orientacio or "",
            'Altitud': altitud or "",
            'Grup': int(grup) if grup else None,
            'Desenc': int(desenc) if desenc else None,
            'Arrossegats': int(arrossegats) if arrossegats else None,
            'Ferits': int(ferits) if ferits else None,
            'Morts': int(morts) if morts else None,
            'Grau de perill': grau_perill or "",
            'Mida allau': mida_allau or "",
            'Origen': origen or "",
            'Progressio': progressio or "",
            'Desencadenant': desencadenant or "",
            'Neu': neu or "",
            'Material': material or "",
            'Observacions': observacions or "",
            'Link': link or "",
            'Fotos': fotos or "",
        }

        new_df_row = pd.DataFrame([new_row])
        new_df_row.columns = new_df_row.columns.str.strip() # Neteja també la nova fila

        # ADAPTACIÓ DE TIPUS (Solució al FutureWarning i error de key)
        dtype_mapping = df_existing.dtypes.to_dict()
        valid_dtype_mapping = {k: v for k, v in dtype_mapping.items() if k in new_df_row.columns}
        new_df_row = new_df_row.astype(valid_dtype_mapping, errors='ignore')

        # Unió
        df_final = pd.concat([df_existing, new_df_row], ignore_index=True)

        # Post-processament de numèrics
        cols_numeriques = ['Codi', 'Grup', 'Desenc', 'Arrossegats', 'Ferits', 'Morts']
        for col in cols_numeriques:
            if col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').astype('Int64')

        df_to_save = ensure_pyarrow_compatibility(df_final)
        # Neteja final per GSheets
        string_cols = df_to_save.select_dtypes(include='object').columns
        df_to_save[string_cols] = df_to_save[string_cols].fillna("")
        conn.update(worksheet="Accidents", data=df_to_save)

        st.session_state.df_oficial = df_final
        st.session_state.new_point_coords = None
        st.cache_data.clear()
        st.success("✅ Accident desat correctament!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error en desar: {e}")


# ---------------------------------------------------------------------------
# ALTRES SECCIONS
# ---------------------------------------------------------------------------

def render_charts_section(dff):
    if dff is None or dff.empty: return
    render_kpi_boxes(create_kpi_dashboard(dff))
    st.markdown("### Evolució temporal")
    st.plotly_chart(create_temporal_chart(dff, st.session_state.get('temporal_chart_type', 'Barres')), width='stretch')
    
    st.markdown("### Anàlisi Categòrica")
    chart_config = create_composition_chart_controls(VARS_PERCENT)
    
    chart_types = ["Pastís", "Barres (V)", "Barres (H)"]
    t1_idx = chart_types.index(chart_config['type1'])
    t2_idx = chart_types.index(chart_config['type2'])
    
    fig1, fig2 = create_composition_charts(dff, VARS_PERCENT, VARS_PERCENT.index(chart_config['var1']), 
                                          VARS_PERCENT.index(chart_config['var2']), t1_idx, t2_idx)
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig1)
    c2.plotly_chart(fig2)

def render_data_table_section(dff):
    with st.expander("📋 Dades filtrades", expanded=True):
        create_data_table(dff, "data/bd_accidents_200726_net_c.xlsx")
    
    # --- BOTÓ PER FORÇAR LA SINCRONITZACIÓ ---
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔄 Sincronització de Dades")
        if st.button("Forçar refresc (Google Sheets)", use_container_width=True, type="secondary"):
            st.cache_data.clear() 
            if 'df_oficial' in st.session_state:
                del st.session_state['df_oficial'] 
            if 'gs_readonly_connected' in st.session_state:
                del st.session_state['gs_readonly_connected']
            st.rerun()

    # --- GENERACIÓ D'INFORMES PDF ---
    data_source_current = st.session_state.get('data_source', 'none')
    if data_source_current == 'gsheets_editable':
        st.markdown("---")
        st.markdown("### 📄 Generació d'Informes PDF")
        
        df_src = st.session_state.df_oficial if 'df_oficial' in st.session_state else dff
        if df_src is not None and not df_src.empty:
            import io
            import zipfile
            import base64
            from src.pdf_generator import generate_accident_pdf
            
            if 'pdf_excluded' not in st.session_state:
                st.session_state.pdf_excluded = set()
                
            df_src_cerca = df_src.copy()
            df_src_cerca['Data_obj'] = pd.to_datetime(df_src_cerca['Data'], errors='coerce')
            
            def format_data(dt, orig):
                if pd.isna(dt): return str(orig)
                return dt.strftime('%d/%m/%Y')
                
            def format_codi_int(x):
                try:
                    return str(int(float(x)))
                except:
                    return str(x)
                
            df_src_cerca['Data_str'] = df_src_cerca.apply(lambda r: format_data(r['Data_obj'], r['Data']), axis=1)
            df_src_cerca['Codi_str'] = df_src_cerca['Codi'].apply(format_codi_int)
            
            nom_cerca = df_src_cerca['Codi_str'] + " | " + df_src_cerca['Lloc'].astype(str).fillna('Desconegut') + " | " + df_src_cerca['Data_str']
            df_src_cerca['nom_accident_cerca'] = nom_cerca
            
            llista_accidents = df_src_cerca['nom_accident_cerca'].tolist()
            
            col_cerca, col_data = st.columns(2)
            with col_cerca:
                st.markdown("**Cerca manual:**")
                accidents_manuals = st.multiselect("🔍 Seleccionar per Codi, Lloc o Data:", options=llista_accidents)
                
            with col_data:
                st.markdown("**Selecció per rang de dates:**")
                dates = st.date_input("Dates de l'accident:", value=(), key="dates_pdf")
                
            accidents_per_data = []
            if len(dates) == 2:
                start_date, end_date = dates
                mask = df_src_cerca['Data_obj'].notna() & (df_src_cerca['Data_obj'].dt.date >= start_date) & (df_src_cerca['Data_obj'].dt.date <= end_date)
                accidents_per_data = df_src_cerca[mask]['nom_accident_cerca'].tolist()
                if not accidents_per_data:
                    st.info("No hi ha accidents en aquest rang de dates.")
                else:
                    st.success(f"✓ S'han inclòs {len(accidents_per_data)} accidents pel rang de dates.")
                    
            # Obtenim tots i descartem els exclosos explícitament
            candidats_set = list(dict.fromkeys(accidents_manuals + accidents_per_data))
            all_selected_set = [acc for acc in candidats_set if acc not in st.session_state.pdf_excluded]
            
            if st.session_state.pdf_excluded and len(all_selected_set) < len(candidats_set):
                if st.button("♻️ Restaurar llista original"):
                    st.session_state.pdf_excluded.clear()
                    st.rerun()
            
            if all_selected_set:
                st.markdown("#### Llistat a Descarregar")
                pdf_files = {}
                for acc in all_selected_set:
                    row = df_src_cerca[df_src_cerca['nom_accident_cerca'] == acc].iloc[0]
                    pdf_bytes = generate_accident_pdf(row.to_dict())
                    
                    # Generar nom del fitxer
                    codi_int_str = str(row['Codi_str'])
                    lloc_safe = str(row['Lloc']).replace(' ', '_').replace('/', '_') if pd.notna(row['Lloc']) else 'NOL'
                    data_dt = row['Data_obj']
                    data_estr = data_dt.strftime('%Y%m%d') if pd.notna(data_dt) else 'NODATA'
                    file_name = f"{data_estr}_Informe_Acc_{codi_int_str}_{lloc_safe}.pdf"
                    
                    pdf_files[file_name] = pdf_bytes
                    
                    col_n, col_p, col_b, col_rm = st.columns([4, 1, 1, 0.5])
                    val_vertical = f"<div style='padding-top: 10px; font-weight: 500;'>📄 {acc}</div>"
                    col_n.markdown(val_vertical, unsafe_allow_html=True)
                    
                    with col_p:
                        if st.button("👁️ Veure", key=f"prev_pdf_{row['Codi']}", use_container_width=True):
                            st.session_state.pdf_preview_bytes = pdf_bytes
                            st.session_state.pdf_preview_name = file_name
                    
                    with col_b:
                        st.download_button(
                            label="📥 Descarregar",
                            data=pdf_bytes,
                            file_name=file_name,
                            mime="application/pdf",
                            key=f"btn_pdf_{row['Codi']}",
                            use_container_width=True
                        )
                        
                    with col_rm:
                        if st.button("x", key=f"rm_pdf_{row['Codi']}", help="Eliminar de la llista"):
                            st.session_state.pdf_excluded.add(acc)
                            st.rerun()
                
                # Previsualitzador en línia
                if 'pdf_preview_bytes' in st.session_state and st.session_state.pdf_preview_bytes:
                    st.markdown("---")
                    col_t, col_cx = st.columns([4,1])
                    col_t.markdown(f"**Previsualitzant: {st.session_state.pdf_preview_name}**")
                    if col_cx.button("Tancar Previsualització", use_container_width=True):
                        del st.session_state['pdf_preview_bytes']
                        st.rerun()
                    else:
                        base64_pdf = base64.b64encode(st.session_state.pdf_preview_bytes).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                
                if len(all_selected_set) > 1:
                    st.markdown("---")
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for fname, fbytes in pdf_files.items():
                            zip_file.writestr(fname, fbytes)
                    
                    c_buida, c_zip, c_buida2 = st.columns([1,2,1])
                    with c_zip:
                        st.download_button(
                            label=f"📦 Descarregar Tots ({len(all_selected_set)} PDFs)",
                            data=zip_buffer.getvalue(),
                            file_name="Informes_Accidents_ACNA.zip",
                            mime="application/zip",
                            type="primary",
                            use_container_width=True
                        )
            
    # CRIDA A LA SECCIÓ DEL TRACKLOG
    render_tracklog_section()

if __name__ == "__main__":
    main()