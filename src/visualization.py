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
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

from config.settings import COLORS, MAP_CONFIG

# --- FUNCIONS DE SUPORT ---

def ensure_pyarrow_compatibility(df):
    """Assegura que el DataFrame sigui compatible amb PyArrow forçant tipus correctos."""
    if df is None:
        return None
    df_safe = df.copy()
    string_columns = [
        'id', 'Codi', 'Temporada', 'Lloc', 'Tipus activitat', 'Pais',
        'Regio', 'Serralada', 'Orientacio', 'Altitud', 'Grup', 'Desenc',
        'Grau de perill', 'Mida allau', 'Origen', 'Progressio',
        'Desencadenant', 'Neu', 'Material', 'Observacions', 'Link', 'Fotos'
    ]
    for col in string_columns:
        if col in df_safe.columns:
            df_safe[col] = df_safe[col].astype(str).replace("nan", "")
    return df_safe


def get_map_center_zoom(dff):
    center = {
        "lat": MAP_CONFIG['default_center']['lat'],
        "lon": MAP_CONFIG['default_center']['lon']
    }
    zoom = MAP_CONFIG['default_zoom']
    return center, zoom


def get_simplified_tooltip_html():
    return """
    <b>{Lloc}</b><br/>
    Data: {Data}<br/>
    Perill: {Grau de perill}<br/>
    Origen: {Origen}<br/>
    Desencadenant: {Desencadenant}<br/>
    Morts: {Morts} | Ferits: {Ferits} | Arrossegats: {Arrossegats}
    """


# --- VISUALITZACIONS ---

def create_map_layer(dff, show_points=True, show_heatmap=False,
                     point_radius=5, point_opacity=0.8,
                     heat_radius=6, heat_intensity=10.0, map_style=None):

    if dff is None or dff.empty:
        return None

    center, zoom = get_map_center_zoom(dff)
    view_state = pdk.ViewState(
        latitude=center["lat"],
        longitude=center["lon"],
        zoom=zoom
    )

    if map_style is None:
        map_style_url = MAP_CONFIG['available_styles'][MAP_CONFIG['current_style']]
    else:
        map_style_url = MAP_CONFIG['available_styles'][map_style]

    layers = []

    if map_style in ["Topogràfic", "IGN Raster", "OSM Tiles"]:
        try:
            tile_key_map = {
                "Topogràfic": "stamen_terrain",
                "IGN Raster": "ign_raster",
                "OSM Tiles": "test_osm"
            }
            tile_url = MAP_CONFIG['tile_layer_urls'][tile_key_map[map_style]]
            layers.insert(0, pdk.Layer("TileLayer", data=tile_url, tile_size=256))
            map_style_url = None
        except Exception:
            map_style_url = MAP_CONFIG['available_styles']['Fosc']

    if show_points:
        dff_tooltip = dff.copy()
        alpha = int(point_opacity * 255)
        layer_points = pdk.Layer(
            "ScatterplotLayer",
            data=dff_tooltip,
            get_position='[Longitud, Latitud]',
            get_radius=point_radius,
            get_fill_color=[
                COLORS['turquoise_rgb'][0],
                COLORS['turquoise_rgb'][1],
                COLORS['turquoise_rgb'][2],
                alpha
            ],
            radius_units="pixels",
            pickable=True
        )
        layers.append(layer_points)

    if show_heatmap:
        dff_heat = dff.copy()
        dff_heat["_weight"] = 1.0
        layers.append(pdk.Layer(
            "HeatmapLayer",
            data=dff_heat,
            get_position='[Longitud, Latitud]',
            get_weight="_weight",
            radiusPixels=heat_radius,
            intensity=heat_intensity,
            colorRange=COLORS['heatmap_gradient']
        ))

    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=map_style_url,
        tooltip={
            "html": get_simplified_tooltip_html(),
            "style": {"backgroundColor": "rgba(14,17,23,0.92)", "color": "white"}
        }
    )


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

    fig.update_layout(height=480)
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
        return px.bar(comp, y=var, x="Percent", orientation="h", template="plotly_dark", text_auto='.1f')

    fig1, fig2 = get_fig(v1, t1), get_fig(v2, t2)
    fig1.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    return fig1, fig2


# --- KPI DASHBOARD ---

def create_kpi_dashboard(dff):
    if dff is None or dff.empty:
        return {}
    total = len(dff)
    total_arros = dff["Arrossegats"].sum()
    return {
        'total_accidents': total,
        'percent_morts': ((dff["Morts"] > 0).sum() / total * 100) if total else 0,
        'percent_ferits': ((dff["Ferits"] > 0).sum() / total * 100) if total else 0,
        'percent_morts_arrossegats': (dff["Morts"].sum() / total_arros * 100) if total_arros > 0 else 0,
        'percent_ferits_arrossegats': (dff["Ferits"].sum() / total_arros * 100) if total_arros > 0 else 0,
        'total_arrossegats': total_arros
    }


def render_kpi_boxes(kpi_data):
    if not kpi_data:
        return
    cols = st.columns(6)
    metrics = [
        ("Accidents filtrats",    f"{kpi_data['total_accidents']}"),
        ("% accidents morts",     f"{kpi_data['percent_morts']:.1f}%"),
        ("% accidents ferits",    f"{kpi_data['percent_ferits']:.1f}%"),
        ("% morts / arros.",      f"{kpi_data['percent_morts_arrossegats']:.1f}%"),
        ("% ferits / arros.",     f"{kpi_data['percent_ferits_arrossegats']:.1f}%"),
        ("Arrossegats (total)",   f"{kpi_data['total_arrossegats']}")
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

def create_data_table(dff, original_file_path=None):
    if dff is None or dff.empty:
        st.info("No hi ha dades per mostrar.")
        return

    # --- INICIALITZACIÓ D'ESTAT ---
    # Actualitza df_editable només si no existeix o si han canviat les dades font
    # (shape com a proxy de canvi), i mai durant el mode edició.
    dff_shape = dff.shape
    if (
        'df_editable' not in st.session_state or
        (st.session_state.get('_df_editable_shape') != dff_shape and
         not st.session_state.get('editing_table', False))
    ):
        st.session_state.df_editable = ensure_pyarrow_compatibility(dff)
        st.session_state._df_editable_shape = dff_shape

    if 'editing_table' not in st.session_state:
        st.session_state.editing_table = False

    if '_staged_edits' not in st.session_state:
        st.session_state._staged_edits = None

    data_source = st.session_state.get('data_source', 'none')
    is_gsheets = data_source == "gsheets_editable"

    # --- BOTONS D'ACCIÓ ---
    col1, col2 = st.columns([1, 1])

    if not st.session_state.editing_table:
        with col1:
            if st.button("📝 Editar Taula", use_container_width=True):
                st.session_state._staged_edits = st.session_state.df_editable.copy()
                st.session_state.editing_table = True
                # Sense st.rerun(): Streamlit ja fa rerun automàtic en prémer un botó
        with col2:
            if st.button("📥 Exportar Excel", use_container_width=True):
                export_to_excel(st.session_state.df_editable)
    else:
        with col1:
            if st.button("💾 Guardar Canvis", type="primary", use_container_width=True):
                # Consolida els staged edits com a df_editable definitiu
                if st.session_state._staged_edits is not None:
                    st.session_state.df_editable = st.session_state._staged_edits.copy()

                if is_gsheets:
                    with st.spinner("Desant al Google Sheets..."):
                        try:
                            conn = st.session_state.get('gsheets_conn')
                            if conn is None:
                                st.error("No s'ha trobat la connexió a Google Sheets.")
                                return

                            df_to_save = st.session_state.df_editable.copy()

                            if df_to_save is None or df_to_save.empty:
                                st.error("No hi ha dades per desar.")
                                return

                            # Coordenades: forcem float
                            for col in ['Latitud', 'Longitud']:
                                if col in df_to_save.columns:
                                    df_to_save[col] = pd.to_numeric(
                                        df_to_save[col], errors='coerce'
                                    )

                            # Dates: datetime64 -> string (GSheets no accepta datetime64)
                            for col in df_to_save.select_dtypes(
                                include=['datetime64[ns]', 'datetime64']
                            ).columns:
                                df_to_save[col] = (
                                    df_to_save[col].dt.strftime('%d/%m/%Y').fillna('')
                                )

                            # Numèrics: NaN -> 0
                            for col in ['Arrossegats', 'Ferits', 'Morts']:
                                if col in df_to_save.columns:
                                    df_to_save[col] = (
                                        pd.to_numeric(df_to_save[col], errors='coerce')
                                        .fillna(0)
                                        .astype(int)
                                    )

                            # Text: NaN -> string buit
                            string_cols = df_to_save.select_dtypes(include='object').columns
                            df_to_save[string_cols] = df_to_save[string_cols].fillna("")

                            conn.update(worksheet="Accidents", data=df_to_save)
                            st.cache_data.clear()
                            st.success("✅ Guardat correctament a Google Sheets!")

                        except Exception as e:
                            st.error(f"Error al guardar: {e}")
                            return
                else:
                    st.success("✅ Canvis aplicats a la sessió local.")

                st.session_state._staged_edits = None
                st.session_state.editing_table = False
                # st.rerun() necessari aquí per refrescar la taula en mode lectura
                st.rerun()

        with col2:
            if st.button("✖ Cancel·lar", use_container_width=True):
                # Descarta els staged edits sense tocar df_editable
                st.session_state._staged_edits = None
                st.session_state.editing_table = False
                # Sense st.rerun(): Streamlit ja renderitza de nou automàticament

    # --- RENDERITZAT DE LA TAULA ---
    config_cols = {"Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY")}

    if st.session_state.editing_table:
        # El data_editor escriu als staged edits, NO directament a df_editable
        edited = st.data_editor(
            st.session_state._staged_edits,
            column_config=config_cols,
            num_rows="dynamic",
            use_container_width=True,
            key="main_data_editor"
        )
        st.session_state._staged_edits = edited
    else:
        st.dataframe(
            st.session_state.df_editable,
            column_config=config_cols,
            use_container_width=True
        )


def export_to_excel(df):
    if df is None or df.empty:
        return
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Dades_Exportades')
        st.download_button(
            label="Descarregar Excel",
            data=output.getvalue(),
            file_name=f'export_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        st.error(f"Error a l'exportar: {e}")


def handle_map_click(click_data, dff):
    if click_data is None or 'coordinates' not in click_data:
        return None

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