"""
Mòdul de Visualitzacions per a BDACC ACNA
===========================================
Funcionalitat:
- Creació de mapes interactius amb pydeck
- Gràfics temporals amb plotly
- Gràfics de composició (pastís, barres)
- KPI Dashboard amb mètriques clau
"""

import io
from datetime import date, datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config.settings import COLORS, MAP_CONFIG
import gspread


# --- FUNCIONS DE SUPORT ---

def ensure_pyarrow_compatibility(df):
    if df is None: return None
    df_safe = df.copy()

    # A. ENTERS PURS
    int_columns = ['id', 'Grup', 'Desenc', 'Codi', 'Morts', 'Ferits', 'Arrossegats']
    for col in int_columns:
        if col in df_safe.columns:
            df_safe[col] = pd.to_numeric(df_safe[col], errors='coerce').fillna(0).astype('Int64')

    # B. CATEGÒRIQUES
    text_fake_numbers = ['Temporada', 'Altitud', 'Mida allau'] 
    for col in text_fake_numbers:
        if col in df_safe.columns:
            temp_num = pd.to_numeric(df_safe[col], errors='coerce')
            df_safe[col] = temp_num.fillna(df_safe[col]).astype(str).replace(r'\.0$', '', regex=True)
            df_safe[col] = df_safe[col].replace(["nan", "None", "<NA>"], "")

    # C. RESTA DE TEXT
    string_columns = ['Tipus activitat', 'Pais', 'Regio', 'Serralada', 'Orientacio', 'Grau de perill', 'Lloc']
    for col in string_columns:
        if col in df_safe.columns:
            df_safe[col] = df_safe[col].astype(str).replace(["nan", "None"], "")
            
    return df_safe


def get_map_center_zoom(dff):
    center = {
        "lat": MAP_CONFIG['default_center']['lat'],
        "lon": MAP_CONFIG['default_center']['lon']
    }
    zoom = MAP_CONFIG['default_zoom']
    return center, zoom


# --- VISUALITZACIONS ---


def create_temporal_chart(dff, chart_type="Barres"):
    if dff is None or dff.empty:
        return None

    dff_temp = dff.copy()
    if 'Temporada' in dff_temp.columns:
        dff_temp['Temporada'] = (
            dff_temp['Temporada']
            .fillna('Desconegut')
            .astype(str)
            .replace(r'\.0$', '', regex=True)
        )

    serie = (
        dff_temp
        .dropna(subset=["Temporada"])
        .groupby("Temporada", as_index=False)
        .agg(Accidents=("id", "count"), Morts=("Morts", "sum"))
        .sort_values("Temporada")
    )

    if chart_type == "Línia":
        fig = px.line(
            serie, x="Temporada", y=["Accidents", "Morts"],
            markers=True, template="plotly", title="Evolució per Temporada"
        )
    else:
        fig = px.bar(
            serie.melt(id_vars=["Temporada"], value_vars=["Accidents", "Morts"]),
            x="Temporada", y="value", color="variable",
            barmode="group", template="plotly", title="Evolució per Temporada"
        )

    fig.update_layout(
        height=480,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


def create_composition_charts(dff, vars_percent, var1_index=0, var2_index=2,
                               type1_index=2, type2_index=0):
    if dff is None or dff.empty:
        return None, None

    v1, v2 = vars_percent[var1_index], vars_percent[var2_index]
    chart_types = ["Pastís", "Barres (V)", "Barres (H)"]
    t1, t2 = chart_types[type1_index], chart_types[type2_index]

    def get_fig(var, t):
        comp = dff[var].value_counts(normalize=True).mul(100).reset_index()
        comp.columns = [var, 'Percent']
        if var == "Mes":
            orden = [
                "Setembre", "Octubre", "Novembre", "Desembre",
                "Gener", "Febrer", "Març", "Abril",
                "Maig", "Juny", "Juliol", "Agost"
            ]
            comp['orden'] = comp[var].map({m: i for i, m in enumerate(orden)})
            comp = comp.sort_values('orden').drop('orden', axis=1)

        if t == "Pastís":
            return px.pie(comp, names=var, values="Percent", hole=0.45, template="plotly_dark")
        if t == "Barres (V)":
            return px.bar(comp, x=var, y="Percent", template="plotly_dark", text_auto='.1f')
        return px.bar(
            comp, y=var, x="Percent", orientation="h",
            template="plotly_dark", text_auto='.1f'
        )

    fig1, fig2 = get_fig(v1, t1), get_fig(v2, t2)
    fig1.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    return fig1, fig2


# --- KPI DASHBOARD ---

def create_kpi_dashboard(dff):
    if dff is None or dff.empty:
        return {}
    total = len(dff)
    total_arros = int(pd.to_numeric(dff["Arrossegats"], errors='coerce').fillna(0).sum())
    total_morts = int(pd.to_numeric(dff["Morts"], errors='coerce').fillna(0).sum())
    total_ferits = int(pd.to_numeric(dff["Ferits"], errors='coerce').fillna(0).sum())
    return {
        'total_accidents':           total,
        'percent_morts':               ((dff["Morts"] > 0).sum() / total * 100) if total else 0,
        'percent_ferits':               ((dff["Ferits"] > 0).sum() / total * 100) if total else 0,
        'percent_morts_arrossegats':  (total_morts / total_arros * 100) if total_arros > 0 else 0,
        'percent_ferits_arrossegats': (total_ferits / total_arros * 100) if total_arros > 0 else 0,
        'total_arrossegats':           total_arros,
        'total_morts':                total_morts,
        'total_ferits':               total_ferits,
    }


def render_kpi_boxes(kpi_data):
    if not kpi_data:
        return
    cols = st.columns(6)
    metrics = [
        ("Accidents filtrats",     f"{kpi_data['total_accidents']}"),
        ("% accidents amb morts",  f"{kpi_data['percent_morts']:.1f}%"),
        ("% accidents amb ferits", f"{kpi_data['percent_ferits']:.1f}%"),
        ("% morts / arros.",       f"{kpi_data['percent_morts_arrossegats']:.1f}%"),
        ("% ferits / arros.",      f"{kpi_data['percent_ferits_arrossegats']:.1f}%"),
        ("Arrossegats (total)",    f"{kpi_data['total_arrossegats']}"),
    ]
    for i, (label, value) in enumerate(metrics):
        with cols[i]:
            st.markdown(
                f'<div class="kpi-box">'
                f'<div class="kpi-title">{label}</div>'
                f'<div class="kpi-value">{value}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


# --- TAULA DE DADES I EDICIÓ ---

def _parse_date_safe(value) -> date:
    fallback = datetime.now().date()
    if value is None or pd.isna(value):
        return fallback
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, str):
        value = value.strip()
        if not value or value.lower() in ('nat', 'none', 'nan', ''):
            return fallback
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    try:
        parsed = pd.to_datetime(value, dayfirst=True)
        return parsed.date() if not pd.isna(parsed) else fallback
    except:
        return fallback

def create_data_table(dff, original_file_path=None):
    if dff is None or dff.empty:
        st.info("No hi ha dades per mostrar.")
        return

    if 'Data' in dff.columns:
        dff = dff.sort_values(by='Data', ascending=False)

    dff_shape = dff.shape
    if 'df_editable' not in st.session_state or (st.session_state.get('_df_editable_shape') != dff_shape and not st.session_state.get('editing_table', False)):
        st.session_state.df_editable = ensure_pyarrow_compatibility(dff)
        st.session_state._df_editable_shape = dff_shape

    if 'editing_table' not in st.session_state: st.session_state.editing_table = False
    if '_staged_edits' not in st.session_state: st.session_state._staged_edits = None
    if '_edit_row_index' not in st.session_state: st.session_state._edit_row_index = None

    is_gsheets = st.session_state.get('data_source') == "gsheets_editable"

    # --- CONFIGURACIÓ DE TIPUS DE DADES ACORDATS ---
    config_columnes = {
        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
        # Fem servir format="%d" per assegurar que NO surtin decimals (.0)
        "id": st.column_config.NumberColumn("id", format="%d"),
        "Codi": st.column_config.NumberColumn("Codi", format="%d"),
        "Grup": st.column_config.NumberColumn("Grup", format="%d"),
        "Desenc": st.column_config.NumberColumn("Desenc", format="%d"),
        "Arrossegats": st.column_config.NumberColumn("Arrossegats", format="%d"),
        "Ferits": st.column_config.NumberColumn("Ferits", format="%d"),
        "Morts": st.column_config.NumberColumn("Morts", format="%d"),
        "Latitud": st.column_config.NumberColumn("Latitud", format="%.6f"),
        "Longitud": st.column_config.NumberColumn("Longitud", format="%.6f"),
    }

    if not st.session_state.editing_table:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Editar Taula", use_container_width=True, type="primary"):
                if not is_gsheets:
                    st.info("No tens permisos d'edició, però pots seguir explorant la casuística d'accidentalitat.")
                else:
                    st.session_state._staged_edits = st.session_state.df_editable.copy()
                    st.session_state.editing_table = True
                    st.session_state._edit_row_index = None
                    st.rerun()
        with col2:
            st.download_button("📥 Exportar Excel", data=_prepare_excel(st.session_state.df_editable), 
                               file_name=f'export_{datetime.now().strftime("%Y%m%d")}.xlsx', use_container_width=True)

        # REVISIÓ: Afegit hide_index=True per al mode lectura
        st.dataframe(
            st.session_state.df_editable, 
            column_config=config_columnes, 
            width="stretch",
            hide_index=True
        )

    else:
        # --- LÒGICA DE SINCRONITZACIÓ I NETEJA ---
        df_edit = st.session_state._staged_edits
        # Evitem errors si 'Lloc' té nuls en generar les opcions del cercador
        opcions_lloc = [""] + sorted(df_edit['Lloc'].dropna().unique().tolist())

        def on_selection_change():
            if "taula_edicio" in st.session_state:
                seleccionats = st.session_state.taula_edicio.get("selection", {}).get("rows", [])
                if seleccionats:
                    st.session_state._edit_row_index = seleccionats[0]
                    st.session_state.input_codi_selector = None
                    st.session_state.input_lloc_selector = ""

        def update_from_codi():
            nou_codi = st.session_state.input_codi_selector
            if nou_codi and nou_codi > 0:
                mask = df_edit['Codi'] == nou_codi
                indices = df_edit.index[mask].tolist()
                if indices:
                    st.session_state._edit_row_index = df_edit.index.get_loc(indices[0])
                    st.session_state.input_lloc_selector = ""
                    if "taula_edicio" in st.session_state:
                        st.session_state.taula_edicio["selection"]["rows"] = []

        def update_from_lloc():
            nou_lloc = st.session_state.input_lloc_selector
            if nou_lloc != "":
                idx_llista = df_edit[df_edit['Lloc'] == nou_lloc].index.tolist()
                if idx_llista:
                    st.session_state._edit_row_index = df_edit.index.get_loc(idx_llista[0])
                    st.session_state.input_codi_selector = None
                    if "taula_edicio" in st.session_state:
                        st.session_state.taula_edicio["selection"]["rows"] = []

        # --- BOTONS DE CONTROL ---
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Desar i sortir", type="primary", use_container_width=True):
                _desar_canvis(is_gsheets)
        with col2:
            if st.button("❌ Cancel·lar", use_container_width=True):
                st.session_state._staged_edits = None
                st.session_state.editing_table = False
                st.session_state._edit_row_index = None
                st.rerun()

        # --- TAULA D'EDICIÓ ---
        st.dataframe(
            st.session_state._staged_edits,
            column_config=config_columnes,
            width="stretch",
            height=280,
            hide_index=True, # Ja el tenies aquí, correcte
            on_select=on_selection_change,
            selection_mode="single-row",
            key="taula_edicio"
        )

        # --- SELECTORS DE CERCA ---
        st.write("### Selecciona el registre a modificar")
        c1, c2 = st.columns([1, 3])
        
        with c1:
            st.number_input("Codi de l'accident:", min_value=0, step=1, value=None,
                            key="input_codi_selector", on_change=update_from_codi)
        with c2:
            st.selectbox("Cerca per Lloc:", options=opcions_lloc,
                         key="input_lloc_selector", on_change=update_from_lloc)

        st.divider()

        # --- MOSTRAR FORMULARI ---
        if st.session_state._edit_row_index is not None:
            _render_edit_form(st.session_state._edit_row_index)
        else:
            st.info("💡 Tria una fila a la taula o utilitza els cercadors superiors per començar a editar.")


def _render_edit_form(row_index):
    selected_row = st.session_state._staged_edits.iloc[row_index]
    accident_id_key = selected_row['Codi']
    nom_lloc = selected_row['Lloc']
    st.markdown(f"##### ✏️ Editant: **{nom_lloc}** <span style='color:gray'>(Codi {accident_id_key})</span>", unsafe_allow_html=True)

    with st.form(key=f"edit_form_{accident_id_key}"):
        cols = st.columns(3)
        edited_row_dict = {}

        for i, (col_name, value) in enumerate(selected_row.items()):
            widget_key = f"acc_{accident_id_key}_{col_name}_{i}"
            
            with cols[i % 3]:
                if col_name == 'Data':
                    edited_row_dict[col_name] = st.date_input(col_name, value=_parse_date_safe(value), key=widget_key)
                elif col_name in ['Morts', 'Ferits', 'Arrossegats', 'id', 'Grup', 'Desenc', 'Codi']:
                    val = int(float(value)) if pd.notnull(value) and str(value) != "" else 0
                    edited_row_dict[col_name] = st.number_input(col_name, value=val, min_value=0, key=widget_key)
                elif col_name in ['Latitud', 'Longitud']:
                    val = float(value) if pd.notnull(value) and str(value) != "" else 0.0
                    edited_row_dict[col_name] = st.number_input(col_name, value=val, format="%.6f", step=0.0001, key=widget_key)
                else:
                    val = str(value) if pd.notnull(value) and str(value) != "nan" else ""
                    edited_row_dict[col_name] = st.text_input(col_name, value=val, key=widget_key)

        st.divider()
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.form_submit_button("✅ Aplicar canvis", type="primary", use_container_width=True):
                for k, v in edited_row_dict.items():
                    if isinstance(v, date): edited_row_dict[k] = pd.Timestamp(v)
                st.session_state._staged_edits.iloc[row_index] = pd.Series(edited_row_dict)
                st.success("Canvis aplicats a la llista temporal.")
                st.rerun()
        with c_btn2:
            if st.form_submit_button("🗑️ Eliminar registre", use_container_width=True):
                st.session_state._staged_edits = st.session_state._staged_edits.drop(st.session_state._staged_edits.index[row_index]).reset_index(drop=True)
                st.session_state._edit_row_index = None
                st.rerun()

def _desar_canvis(is_gsheets):
    if st.session_state._staged_edits is not None:
        st.session_state.df_editable = st.session_state._staged_edits.copy()
        
        if is_gsheets:
            with st.spinner("Sincronitzant amb Google Sheets..."):
                try:
                    conn = st.session_state.get('gsheets_conn')
                    df_to_save = st.session_state.df_editable.copy()
                    
                    # 1. Preparació de dades (Formatat de dates i números)
                    for col in df_to_save.columns:
                        if col == 'Data':
                            df_to_save[col] = df_to_save[col].apply(
                                lambda v: _parse_date_safe(v).strftime('%d/%m/%Y')
                            )
                        elif col in ['Arrossegats', 'Ferits', 'Morts', 'Codi', 'id', 'Grup', 'Desenc']:
                            df_to_save[col] = pd.to_numeric(df_to_save[col], errors='coerce').fillna(0).astype(int)
                    
                    # 2. Actualització completa (Sobreescriure)
                    # El mètode .update de la connexió de Streamlit és la via més directa i segura
                    # per reflectir canvis, altes i baixes d'un sol cop.
                    conn.update(worksheet="Accidents", data=df_to_save)
                    
                    st.cache_data.clear()
                    st.success("Google Sheets actualitzat correctament!")
                    
                except Exception as e:
                    st.error(f"Error de sincronització: {e}")
                    return
    
    st.session_state.df_oficial = st.session_state.df_editable.copy()
    st.session_state.editing_table = False
    st.session_state._edit_row_index = None # Netegem l'índex seleccionat
    st.rerun()

def _prepare_excel(df):
    if df is None or df.empty: return b""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dades')
    return output.getvalue()

def handle_map_click(click_data, dff):
    if click_data is None or 'coordinates' not in click_data: return None
    lat, lon = click_data['coordinates'][1], click_data['coordinates'][0]
    nearby = None
    if dff is not None and not dff.empty:
        for _, row in dff.iterrows():
            if abs(lat - row['Latitud']) < 0.001 and abs(lon - row['Longitud']) < 0.001:
                nearby = row.to_dict()
                break
    if nearby:
        st.session_state.selected_accident = nearby
        return {'type': 'accident_selected', 'accident': nearby}
    return None