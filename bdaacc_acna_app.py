import os  # per comprovar si existeix el fitxer local
import pandas as pd  
import streamlit as st  # framework web per a dashboards interactius
import pydeck as pdk  # visualitzacions de mapes amb pydeck / deck.gl
import plotly.express as px  

# --------------------------------------------------------
# CONFIGURACIÓ DE LA PÀGINA + ESTILS
# --------------------------------------------------------
st.set_page_config(page_title="Base de Dades d'Accidents per Allau ACNA", layout="wide")

# Estils personalitzats per a l'aplicació Streamlit: colors de tema, barra lateral i botons
st.markdown("""
<style>
.stApp[data-theme="dark"] { background-color: #0e1117 !important; }
.stApp[data-theme="light"] { background-color: #ffffff !important; }

.stApp[data-theme="dark"] h1, .stApp[data-theme="dark"] h2, .stApp[data-theme="dark"] h3, 
            .stApp[data-theme="dark"] h4, .stApp[data-theme="dark"] h5, .stApp[data-theme="dark"] p, 
            .stApp[data-theme="dark"] label { color: #ffffff !important; }
.stApp[data-theme="light"] h1, .stApp[data-theme="light"] h2, .stApp[data-theme="light"] h3, 
            .stApp[data-theme="light"] h4, .stApp[data-theme="light"] h5, .stApp[data-theme="light"] p, 
            .stApp[data-theme="light"] label { color: #000000 !important; }

.stApp[data-theme="dark"] [data-testid="stSidebar"] { background-color: #000000 !important; }
[data-testid="stSidebar"][data-theme="dark"] * { color: #ffffff !important; }
[data-testid="stSidebar"][data-theme="light"] { background-color: #f0f0f0 !important; }
[data-testid="stSidebar"][data-theme="light"] * { color: #000000 !important; }

.stApp[data-theme="dark"] div[data-baseweb="select"] > div,
.stApp[data-theme="dark"] div[data-baseweb="input"] > div,
.stApp[data-theme="dark"] div[data-baseweb="textarea"] > div {
    background-color: #1a1a1a !important; color: white !important;
}
.stApp[data-theme="light"] div[data-baseweb="select"] > div,
.stApp[data-theme="light"] div[data-baseweb="input"] > div,
.stApp[data-theme="light"] div[data-baseweb="textarea"] > div {
    background-color: #ffffff !important; color: black !important;
}

.stButton>button {
    width: 100%; border: 1px solid #40E0D0;
    background: transparent!important; color: #40E0D0 !important; font-weight: bold;
}
.stButton>button:hover { background: #40E0D0 !important; color: black !important; }

section.main > div { padding-top: 0rem !important; }

#heatmap-legend {
    position: fixed; right: 24px; bottom: 24px; z-index: 9999;
    background: rgba(20,20,20,0.85); border: 1px solid rgba(255,255,255,0.25);
    border-radius: 6px; padding: 10px 12px; font-size: 12px; color: #eee;
    backdrop-filter: blur(3px); box-shadow: 0 0 10px rgba(0,0,0,0.4);
}
#heatmap-legend .title { font-weight: 600; margin-bottom: 6px; color: #40E0D0; }
#heatmap-legend .bar {
    height: 10px; width: 240px; border-radius: 3px; margin: 6px 0 4px 0;
    background: linear-gradient(90deg,
        #000000 0%,
        #5e2b97 20%,
        #b02bff 40%,
        #ff5f3d 60%,
        #ffbd3d 80%,
        #fff26a 100%
    );
}
#heatmap-legend .ticks { display: flex; justify-content: space-between; color: #ccc; font-size: 11px; }
#heatmap-legend .note { color: #9bd7cf; font-size: 11px; margin-top: 4px; }

.kpi-box { background: #12151c; border: 1px solid #263042; border-radius: 8px; padding: 12px 14px; }
.kpi-title { color: #9bd7cf; font-size: 12px; margin-bottom: 6px; text-transform: uppercase; }
.kpi-value { color: #ffffff; font-size: 22px; font-weight: 700; margin-bottom: 4px; }
.kpi-sub { color: #d0d4da; font-size: 12px; }

/* Estil per al peu de pàgina fixat */
.footer-fixat {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: rgba(14, 17, 23, 0.85); /* Una mica de transparència per veure què hi ha sota */
    color: #888;
    text-align: center;
    padding: 5px 20px;
    font-size: 0.8rem;
    z-index: 999;
    border-top: 1px solid #263042;
    display: flex;
    justify-content: space-between;
}

/* Espai extra al final de la pàgina perquè l'últim element no quedi tapat pel peu */
.main .block-container {
    padding-bottom: 50px !important;
}
      
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------
# CÀRREGA I NETEJA DE DADES
# --------------------------------------------------------
@st.cache_data # Aquesta decoració fa que la funció es cachegi, 
               # millorant el rendiment en recarregar la pàgina

def load_data():
    # Carrega el fitxer Excel local amb les dades d'accidents per allau
    file_path = "data/bd_accidents_200726_net_c.xlsx"
    if not os.path.exists(file_path):
        st.error("❌ Fitxer no trobat.")
        st.stop()

    df = pd.read_excel(file_path, engine="openpyxl")
    df.columns = df.columns.str.strip()  # neteja espais en blancs dels noms de columnes

    # Converteix coordenades a numèric: canvia ',' per '.' i transforma a float
    for col in ["Latitud", "Longitud"]:
        df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Elimina files sense coordenades vàlides i fora de l'àrea peninsular
    df = df.dropna(subset=["Latitud","Longitud"])
    df = df[(df["Latitud"] > 30) & (df["Latitud"] < 50)]
    df = df[(df["Longitud"] > -10) & (df["Longitud"] < 10)]

    # Normalitza format de data intentant primer dia/mes/any i després mes/dia/any
    raw = df["Data"].astype(str)
    d1 = pd.to_datetime(raw, errors="coerce", dayfirst=True)
    mask = d1.isna()
    d2 = pd.to_datetime(raw[mask], errors="coerce", dayfirst=False)
    d1.loc[mask] = d2
    df["Data"] = d1

    # Columnes auxiliars per mostrar dates i analitzar per anys/mesos
    df["Data_str"] = df["Data"].dt.strftime("%d/%m/%Y").fillna("Desconegut")
    df["Any"] = df["Data"].dt.year

    mesos = {
        1:"Gener",2:"Febrer",3:"Març",4:"Abril",5:"Maig",6:"Juny",
        7:"Juliol",8:"Agost",9:"Setembre",10:"Octubre",11:"Novembre",12:"Desembre"
    }
    df["Mes"] = df["Data"].dt.month.map(mesos)
    df["Accidents"] = 1  # cada fila és un accident; es pot agrupar amb sum()

    # Assegura que les columnes de nombres siguin enters i sense NaN
    for col in ["Morts","Ferits","Arrossegats"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Normalitza categories que poden aparèixer com a NaN o cadenes buides
    cat_cols = [
        "Temporada","Tipus activitat","Pais","Regio","Serralada","Orientacio",
        "Origen","Progressio","Desencadenant","Material","Altitud",
        "Grau de perill","Mes","Mida allau"
    ]
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan":"Desconegut","None":"Desconegut","": "Desconegut"})

    return df

df = load_data()


# Llista global de variables categòriques per a l'anàlisi de composició
vars_percent = [
    "Grau de perill", "Desencadenant", "Origen", "Orientacio", 
    "Mida allau", "Tipus activitat", "Pais", "Regio", "Serralada", "Altitud"
]


def opts(col):
    # Retorna una llista d'opcions ordenades per una columna categòrica
    if col not in df.columns:
        return []
    s = df[col].dropna().astype(str).str.strip()
    s = s.replace({"nan":"Desconegut","None":"Desconegut","": "Desconegut"})
    return sorted(s.unique().tolist(), key=lambda x: (x=="Desconegut", x.lower()))


def map_center_zoom(d):
    # Retorna el centre i zoom inicial per al mapa pydeck
    # actualment es fixa sobre la Península Ibèrica
    center = {"lat": 40.0, "lon": -3.5}
    zoom = 4.9
    return center, zoom



# --------------------------------------------------------
# SIDEBAR FILTRES
# --------------------------------------------------------
# Controls que permeten filtrar les dades abans de mostrar-les.
st.sidebar.header("🔍 Filtres")

metrica = st.sidebar.selectbox(
    "Variable a representar (filtra files):",
    ["Accidents","Morts","Ferits","Arrossegats"],
    index=0
)

tipus_grafic_temporal = st.sidebar.radio(
    "Tipus de gràfic temporal",
    ["Línia","Barres"], horizontal=True
)

f_temp  = st.sidebar.multiselect("Temporada", opts("Temporada"))
f_mes   = st.sidebar.multiselect("Mes", opts("Mes"))
f_act   = st.sidebar.multiselect("Tipus activitat", opts("Tipus activitat"))
f_per   = st.sidebar.multiselect("Grau de perill", opts("Grau de perill"))
f_pais  = st.sidebar.multiselect("País", opts("Pais"))
f_reg   = st.sidebar.multiselect("Regió", opts("Regio"))
f_ser   = st.sidebar.multiselect("Serralada", opts("Serralada"))
f_ori   = st.sidebar.multiselect("Orientació", opts("Orientacio"))
f_org   = st.sidebar.multiselect("Origen allau", opts("Origen"))
f_prog  = st.sidebar.multiselect("Progressió", opts("Progressio"))
f_des   = st.sidebar.multiselect("Desencadenant", opts("Desencadenant"))
f_mat   = st.sidebar.multiselect("Material", opts("Material"))
f_alt   = st.sidebar.multiselect("Altitud", opts("Altitud"))
f_mida  = st.sidebar.multiselect("Mida d'allau", opts("Mida allau"))


# --------------------------------------------------------
# APLICACIÓ DE FILTRES
# --------------------------------------------------------
# Copia les dades originals i aplica els filtres seleccionats pel costat
# lateral. Això no modifica el DataFrame original `df`.
dff = df.copy()

if metrica != "Accidents":
    dff = dff[dff[metrica] > 0]

filters = {
    "Temporada":f_temp, "Mes":f_mes, "Tipus activitat":f_act, "Grau de perill":f_per,
    "Pais":f_pais, "Regio":f_reg, "Serralada":f_ser, "Orientacio":f_ori,
    "Origen":f_org, "Progressio":f_prog, "Desencadenant":f_des,
    "Material":f_mat, "Altitud":f_alt, "Mida allau":f_mida
}

for col, vals in filters.items():
    if vals:
        dff = dff[dff[col].isin(vals)]

dff = dff.dropna(subset=["Latitud","Longitud"])


# --------------------------------------------------------
# TÍTOL + MAPA
# --------------------------------------------------------
st.title("Base de Dades d'Accidents per Allau ACNA")

c1, c2 = st.columns([1,1])
with c1:
    mostra_punts = st.checkbox("Mostrar punts 📍", True)
with c2:
    mostra_heatmap = st.checkbox("Mostrar mapa de calor 🔥", False)

cpa, cpb, cpc, cpd = st.columns([1,1,1,1])
with cpa:
    radi = st.slider("Radi punt", 4, 80, 5)
with cpb:
    alpha_val = st.slider("Opacitat punts", 0.1, 1.0, 0.8)
with cpc:
    heat_radius = st.slider("Radi heatmap", 1, 40, 6)
with cpd:
    heat_intensity = st.slider("Intensitat", 0.2, 20.0, 10.0)

if dff.empty:
    st.warning("⚠️ Cap punt coincideix amb els filtres.")
else:
    center, zoom = map_center_zoom(dff)
    view = pdk.ViewState(latitude=center["lat"], longitude=center["lon"], zoom=zoom)

    layers = []

    if mostra_punts:
        alpha = int(alpha_val * 255)
        dff_tooltip = dff.copy()
        for c in ["Lloc","Data_str","Temporada","Grau de perill","Orientacio",
                  "Origen","Desencadenant","Mida allau","Tipus activitat",
                  "Morts","Ferits","Arrossegats"]:
            if c in dff_tooltip.columns:
                dff_tooltip[c] = dff_tooltip[c].astype(str).replace({"nan":"Desconegut"})

        layer_points = pdk.Layer(
            "ScatterplotLayer",
            data=dff_tooltip,
            get_position='[Longitud, Latitud]',
            get_radius=radi,
            get_fill_color=[64,224,208,alpha],
            radius_units="pixels",
            stroked=True,
            pickable=True
        )
        layers.append(layer_points)

    
    if mostra_heatmap:
        dff_h = dff.copy()
        dff_h["_weight"] = 1.0

        layer_heat = pdk.Layer(
            "HeatmapLayer",
            data=dff_h,
            get_position='[Longitud, Latitud]',
            get_weight="_weight",
            radiusPixels=int(heat_radius),
            intensity=float(heat_intensity),
            threshold=0,
            colorRange=[
                [30, 180, 200, 70],    # low density - aqua suau i semitransparent
                [0, 120, 160, 140],    # teal
                [80, 70, 200, 190],    # indigo / violeta
                [210, 80, 130, 230],   # magenta intens
                [255, 220, 60, 255],   # hot - groc/ambre

            ]
        )

        layers.append(layer_heat)


    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={
            "html": """
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
            """,
            "style": {"backgroundColor":"rgba(14,17,23,0.92)","color":"white"}
        }
    )

    st.pydeck_chart(deck, use_container_width=True)


# --------------------------------------------------------
# KPI (SOTA EL MAPA) — UNA FILA DE 6 COLUMNES
# --------------------------------------------------------
if not dff.empty:

    total = len(dff)
    n_morts_regs = (dff["Morts"] > 0).sum()
    n_ferits_regs = (dff["Ferits"] > 0).sum()

    p_morts = (n_morts_regs / total * 100) if total else 0
    p_ferits = (n_ferits_regs / total * 100) if total else 0

    total_morts = dff["Morts"].sum()
    total_ferits = dff["Ferits"].sum()
    total_arros = dff["Arrossegats"].sum()

    pm_morts = (total_morts / total_arros * 100) if total_arros > 0 else 0
    pm_ferits = (total_ferits / total_arros * 100) if total_arros > 0 else 0

    # ----------------------
    # FILA ÚNICA CON 6 COLUMNAS
    # ----------------------
    k1, k2, k3, k4, k5, k6 = st.columns(6)

    with k1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Accidents filtrats</div>
            <div class="kpi-value">{total}</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">% accidents amb morts</div>
            <div class="kpi-value">{p_morts:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">% accidents amb ferits</div>
            <div class="kpi-value">{p_ferits:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">% morts / arrossegats</div>
            <div class="kpi-value">{pm_morts:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with k5:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">% ferits / arrossegats</div>
            <div class="kpi-value">{pm_ferits:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with k6:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Arrossegats (total)</div>
            <div class="kpi-value">{total_arros}</div>
        </div>
        """, unsafe_allow_html=True)




# --------------------------------------------------------
# GRÀFIC TEMPORAL
# --------------------------------------------------------
st.markdown("<div style='margin-top:25px'></div>", unsafe_allow_html=True)

# Gràfic temporal: evolució d'accidents i morts per temporada
st.markdown("### Evolució temporal (Accidents i Morts)")

if not dff.empty:
    serie = (
        dff.dropna(subset=["Temporada"])
           .assign(Temp=lambda x: pd.to_numeric(x["Temporada"], errors="coerce"))
           .groupby("Temporada", as_index=False)
           .agg(Accidents=("Accidents","sum"),
                Morts=("Morts","sum"))
           .sort_values("Temporada")
    )

    if tipus_grafic_temporal == "Línia":
        fig_t = px.line(
            serie, x="Temporada", y=["Accidents","Morts"],
            markers=True, template="plotly",
            #title="Evolució per Temporada"
        )
    else:
        long_df = serie.melt(id_vars=["Temporada"], value_vars=["Accidents","Morts"])
        fig_t = px.bar(
            long_df, x="Temporada", y="value", color="variable",
            barmode="group", template="plotly",
            #title="Evolució per Temporada"
        )
        fig_t.update_traces(marker_line_width=0)

    fig_t.update_layout(height=480)
    st.plotly_chart(fig_t, use_container_width=True)



# --------------------------------------------------------
# GRÀFICS DE COMPOSICIÓ COMPARATIUS (%) - VERSIÓ FINAL
# --------------------------------------------------------
# Cada gràfic mostra la distribució percentual d'una variable categòrica
st.markdown("---")
st.markdown(f"### Anàlisi de Variables Categòriques")

col_esquerra, col_dreta = st.columns(2)

# --- COLUMNA ESQUERRA (Grau de perill / Barres H) ---
with col_esquerra:
    # Index 0 = "Grau de perill" | Index 2 = "Barres (H)"
    v1 = st.selectbox("Variable (Gràfic 1):", vars_percent, index=0, key="v_esq")
    t1 = st.radio("Tipus (Gràfic 1):", ["Pastís", "Barres (V)", "Barres (H)"], index=2, key="t_esq", horizontal=True)

    if not dff.empty:
        comp1 = dff[v1].value_counts(normalize=True).mul(100).reset_index()
        comp1.columns = [v1, 'Percent']
        
        if t1 == "Pastís":
            fig1 = px.pie(comp1, names=v1, values="Percent", hole=0.45, template="plotly_dark")
        elif t1 == "Barres (V)":
            fig1 = px.bar(comp1, x=v1, y="Percent", template="plotly_dark", text_auto='.1f')
            fig1.update_traces(marker_line_width=0) # TREU LES VORES
        else:
            fig1 = px.bar(comp1, y=v1, x="Percent", orientation="h", template="plotly_dark", text_auto='.1f')
            fig1.update_traces(marker_line_width=0) # TREU LES VORES
        
        fig1.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig1, use_container_width=True)

# --- COLUMNA DRETA (Origen / Pastís) ---
with col_dreta:
    # Ajusta l'index de v2 segons la posició de "Origen" a la teva llista vars_percent (normalment és el 2)
    v2 = st.selectbox("Variable (Gràfic 2):", vars_percent, index=2, key="v_dret")
    t2 = st.radio("Tipus (Gràfic 2):", ["Pastís", "Barres (V)", "Barres (H)"], index=0, key="t_dret", horizontal=True)

    if not dff.empty:
        comp2 = dff[v2].value_counts(normalize=True).mul(100).reset_index()
        comp2.columns = [v2, 'Percent']
        
        if t2 == "Pastís":
            fig2 = px.pie(comp2, names=v2, values="Percent", hole=0.45, template="plotly_dark")
        elif t2 == "Barres (V)":
            fig2 = px.bar(comp2, x=v2, y="Percent", template="plotly_dark", text_auto='.1f')
            fig2.update_traces(marker_line_width=0) # TREU LES VORES
        else:
            fig2 = px.bar(comp2, y=v2, x="Percent", orientation="h", template="plotly_dark", text_auto='.1f')
            fig2.update_traces(marker_line_width=0) # TREU LES VORES
        
        fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)



# --------------------------------------------------------
# TAULA
# --------------------------------------------------------
with st.expander("📄 Dades filtrades"):
    cols = [
        "Data_str","Temporada","Lloc","Pais","Regio","Serralada","Orientacio",
        "Altitud","Grau de perill","Mida allau","Tipus activitat",
        "Origen","Desencadenant","Progressio",
        "Morts","Ferits","Arrossegats","Latitud","Longitud"
    ]
    cols = [c for c in cols if c in dff.columns]

    st.dataframe(dff[cols], use_container_width=True)

    csv = dff[cols].to_csv(index=False).encode("utf-8")
    st.download_button("💾 Descarrega CSV", csv, "accidents_filtrats.csv")


# --------------------------------------------------------
# CRÈDITS (PEU DE PÀGINA EN UNA SOLA LÍNIA)
# --------------------------------------------------------
st.markdown("---")

# Utilitzem un sol bloc HTML amb Flexbox per alinear-ho tot en una fila
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #888; opacity: 1;">
        <div><b>Desenvolupament:</b> Òscar Alemán-Milán © 2026 |   |<b> Base de dades:</b>   Associació per al Coneixement de la Neu i les Allaus (ACNA), ICGC, Centre de Lauegi d'Aran i ARI.</div>
        
    
    </div>
    """, 
    unsafe_allow_html=True
)