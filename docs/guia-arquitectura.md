# Guia d'Arquitectura per a Analistes de Dades
================================================

**Data creació:** 03/04/2026  
**Autor:** Òscar Alemán-Milán  
**Versió:** 1.0

## 🎯 Objectiu d'aquest Document

Aquesta guia està dissenyada específicament per a **analistes de dades i geoinformació** que treballen amb l'aplicació BDACC ACNA. No necessites ser expert en enginyeria de software per entendre i modificar el codi.

---

## 📁 Estructura del Projecte

```
bdacc-ACNA/
├── bdacc_acna_app.py          # Fitxer principal (200 línies)
├── src/                       # Lògica de l'aplicació
│   ├── data_processing.py     # Càrrega i neteja de dades
│   ├── visualization.py       # Mapes i gràfics
│   ├── ui_components.py       # Interfície d'usuari
│   └── utils.py              # Funcions auxiliars
├── config/
│   └── settings.py           # Configuració global
├── assets/                   # Imatges i logos
├── data/                     # Fitxers de dades
└── docs/                     # Documentació
```

---

## 🔧 Què Fa Cada Fitxer?

### 📄 `bdacc_acna_app.py` - **El Cervell de l'Aplicació**
**Per a tu és:** El punt d'entrada principal
- **Què fa:** Coordina totes les parts de l'aplicació
- **Què necessites saber:** Si vols afegir una nova secció completa (ex: pàgina d'estadístiques avançades)
- **Modificacions típiques:** Afegir noves seccions, canviar l'ordre dels components

---

### 📊 `src/data_processing.py` - **El Teu Laboratori de Dades**
**Per a tu és:** El mòdul més important per a la teva feina
- **Què fa:** 
  - Carrega dades des d'Excel, Google Sheets, o fitxers pujats
  - Neteja coordenades (coma → punt decimal)
  - Filtra dades geogràfiques (Península Ibèrica)
  - Normalitza dates (dd/mm/yyyy prioritari)
  - Converteix columnes numèriques (Morts, Ferits, Arrossegats)
  - Estandarditza categories buides → "Desconegut"

- **Funcions clau que usaràs:**
  - `load_data()` - Carrega fitxers Excel
  - `load_from_gsheet()` - Carrega Google Sheets
  - `process_data()` - Neteja les teves dades
  - `apply_filters()` - Aplica filtres complexos
  - `get_column_options()` - Obté valors únics per a filtres

- **Modificacions típiques:**
  - Afegir noves fonts de dades (APIs, bases de dades)
  - Modificar criteris de neteja
  - Afegir noves transformacions de dades
  - Canviar filtres geogràfics

---

### 🗺️ `src/visualization.py` - **El Teu Taller de Gràfics**
**Per a tu és:** On es creen totes les visualitzacions
- **Què fa:**
  - Crea mapes interactius amb pydeck
  - Genera gràfics temporals (barres/linies)
  - Crea gràfics de composició (pastís, barres)
  - Calcula i mostra KPIs
  - Prepara taules de dades exportables

- **Funcions clau que usaràs:**
  - `create_map_layer()` - Configura el mapa
  - `create_temporal_chart()` - Gràfics d'evolució
  - `create_composition_charts()` - Anàlisi categòrica
  - `create_kpi_dashboard()` - Mètriques clau

- **Modificacions típiques:**
  - Afegir nous tipus de gràfics
  - Canviar colors i estils
  - Modificar KPIs calculats
  - Afegir noves capes al mapa

---

### 🎨 `src/ui_components.py` - **La Teva Interfície**
**Per a tu és:** Components visuals de l'aplicació
- **Què fa:**
  - Defineix l'aparença (colors, fonts, estils)
  - Crea controls (botons, sliders, selectbox)
  - Gestiona missatges d'error/èxit
  - Organitza el layout de la pàgina

- **Funcions clau que usaràs:**
  - `create_data_source_sidebar()` - Selecció de dades
  - `create_filters_sidebar()` - Panell de filtres
  - `create_map_controls()` - Controls del mapa
  - `sidebar_error()`/`sidebar_success()` - Missatges

- **Modificacions típiques:**
  - Afegir nous filtres
  - Canviar colors i estils
  - Modificar textos i etiquetes
  - Afegir nous controls

---

### ⚙️ `src/utils.py` - **La Teva Caixa d'Eines**
**Per a tu és:** Funcions útils per a tasques comunes
- **Què fa:**
  - Validacions de dades
  - Conversions de format
  - Càlculs de percentatges
  - Utilitats de text

- **Funcions clau que usaràs:**
  - `validate_coordinates()` - Comprova coordenades
  - `calculate_percentage()` - Percentatges segurs
  - `get_data_summary()` - Estadístiques bàsiques

---

### 🎛️ `config/settings.py` - **El Teu Panell de Control**
**Per a tu és:** On es configura tot l'aplicació
- **Què fa:**
  - Defineix colors i estils
  - Configura paràmetres del mapa
  - Estableix textos per defecte
  - Gestiona rutes d'arxius

- **Modificacions típiques:**
  - Canviar colors de l'aplicació
  - Modificar texts i etiquetes
  - Ajustar configuració del mapa
  - Canviar rutes d'arxius

---

## 🚀 Com Afegir Nova Funcionalitat (Exemples Pràctics)

### 📈 Exemple 1: Afegir Nou Gràfic
**Objectiu:** Vols afegir un gràfic de dispersió Morts vs Ferits

1. **A `src/visualization.py`:**
```python
def create_scatter_morts_ferits(dff):
    """Crea gràfic de dispersió Morts vs Ferits"""
    fig = px.scatter(dff, x="Morts", y="Ferits", 
                    color="Grau de perill", 
                    template="plotly_dark")
    return fig
```

2. **A `bdacc_acna_app.py`:**
```python
def render_scatter_section(dff):
    st.markdown("### Relació Morts vs Ferits")
    fig = create_scatter_morts_ferits(dff)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

# Afegeix a main() després dels KPIs:
render_scatter_section(dff)
```

### 🗺️ Exemple 2: Afegir Nova Capa al Mapa
**Objectiu:** Vols mostrar accidents amb morts en vermell

1. **A `src/visualization.py`:**
```python
# Modifica create_map_layer():
if show_points:
    # Capa per a accidents sense morts
    layer_safe = pdk.Layer(...)
    
    # Capa per a accidents amb morts
    if "Morts" in dff.columns:
        dff_morts = dff[dff["Morts"] > 0]
        layer_morts = pdk.Layer(
            "ScatterplotLayer",
            data=dff_morts,
            get_position='[Longitud, Latitud]',
            get_radius=point_radius,
            get_fill_color=[255, 0, 0, alpha],  # Vermell
            radius_units="pixels"
        )
        layers.append(layer_morts)
```

### 🔍 Exemple 3: Afegir Nou Filtre
**Objectiu:** Vols filtrar per rang d'altitud

1. **A `src/ui_components.py`:**
```python
# Afegeix a create_filters_sidebar():
altitud_min = st.sidebar.slider("Altitud mínima (m)", 0, 3000, 0)
altitud_max = st.sidebar.slider("Altitud màxima (m)", 0, 3000, 3000)
filters['altitud_range'] = (altitud_min, altitud_max)
```

2. **A `src/data_processing.py`:**
```python
# Modifica apply_filters():
def apply_filters(df, filters_dict, metrica="Accidents"):
    dff = df.copy()
    
    # ... filtres existents ...
    
    # Nou filtre d'altitud
    if 'altitud_range' in filters_dict:
        alt_min, alt_max = filters_dict['altitud_range']
        if 'Altitud' in dff.columns:
            dff['Altitud'] = pd.to_numeric(dff['Altitud'], errors='coerce')
            dff = dff[(dff['Altitud'] >= alt_min) & (dff['Altitud'] <= alt_max)]
    
    return dff
```

---

## 🔧 Consells per a Analistes de Dades

### 📊 **Treballar amb Dades**
- **Sempre valida les dades:** Usa `validate_dataframe_structure()` abans de processar
- **Fes còpies:** `dff = df.copy()` per no modificar l'original
- **Gestiona valors buits:** Usa `normalize_categorical_values()` per estandarditzar

### 🗺️ **Treballar amb Mapes**
- **Coordenades:** Han de ser decimals (no graus/minuts/segons)
- **Límits geogràfics:** Configurats a `GEO_BOUNDS` a `settings.py`
- **Colors:** Modifica `COLORS` a `settings.py` per canviar l'aparença

### 📈 **Treballar amb Gràfics**
- **Templates:** Usa `plotly_dark` per consistència visual
- **Interactivitat:** Tots els gràfics són interactius per defecte
- **Exportació:** Les taules tenen botó de descàrrega CSV

### 🚨 **Gestió d'Errors**
- **Missatges clars:** Usa `sidebar_error()` amb missatges en català
- **Validacions:** Comprova sempre si les dades estan buides abans de visualitzar
- **Logs:** Usa `log_data_operation()` per debugging

---

## 🔄 Flux de Dades en l'Aplicació

```
1. Selecció d'origen de dades → 
2. Càrrega (Excel/Google Sheets) → 
3. Neteja i processament → 
4. Aplicació de filtres → 
5. Visualització (mapa + gràfics + KPIs) → 
6. Exportació (CSV)
```

---

## 📝 Glossari Tècnic Simplificat

| Terme Tècnic | Significat per a Tu | Exemple |
|--------------|-------------------|---------|
| **DataFrame** | Taula de dades com Excel però en Python | `df` és la teva taula principal |
| **Mòdul** | Fitxer Python amb funcions relacionades | `data_processing.py` gestiona dades |
| **Funció** | Bloc de codi que fa una tasca específica | `load_data()` carrega fitxers |
| **Cache** | Memòria temporal per accelerar | `@st.cache_data` guarda resultats |
| **Streamlit** | Framework per crear apps web | La tecnologia que fa funcionar tot |

---

## 🆘 Resolució de Problemes Comuns

### ❌ **Error: "Fitxer no trobat"**
- **Causa:** El fitxer Excel no existeix a `data/`
- **Solució:** Posa el fitxer a la carpeta correcta o usa Google Sheets

### ❌ **Error: "No hi ha dades"**
- **Causa:** Els filtres són massa restrictius
- **Solució:** Redueix filtres o comprova si les dades es carreguen bé

### ❌ **Mapa buit**
- **Causa:** No hi ha coordenades vàlides
- **Solució:** Comprova que Latitud/Longitud tinguin valors numèrics

### ❌ **Gràfic no es mostra**
- **Causa:** Dades buides després de filtrar
- **Solució:** Verifica que les columnes necessàries existeixin

---

## 📚 Recursos Addicionals

### 📖 **Documentació**
- **Streamlit:** https://docs.streamlit.io
- **Pandas:** https://pandas.pydata.org/docs/
- **Plotly:** https://plotly.com/python/

### 🎥 **Tutorials Recomanats**
- Streamlit per a Data Scientists
- Pandas per a Anàlisi de Dades
- Visualització amb Plotly Express

---

## 📞 Suport i Ajuda

Si tens dubtes tècnics:
1. Revisa aquesta guia
2. Consulta els comentaris al codi
3. Prova amb dades de mostra primer
4. Usa `print()` o `st.write()` per debugging

---

## 🔄 Futurs Millores Possibles

### 📊 **Anàlisi Avançada**
- Anàlisi de sèries temporals
- Models predictius de risc
- Clustering d'accidents

### 🗺️ **Funcionalitats Geogràfiques**
- Anàlisi per províncies
- Heatmaps per temporada
- Anàlisi de densitat espacial

### 📱 **Millora d'UI**
- Filtres per rang de dates
- Comparació entre períodes
- Exportació a PDF

---

**Recorda:** Aquesta arquitectura està dissenyada per ser **modificable**. No tinguis por a experimentar i adaptar-la a les teves necessitats d'anàlisi!
