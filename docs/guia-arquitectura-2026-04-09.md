# Guia d'Arquitectura per a Analistes de Dades - BDACC ACNA
============================================================

**Data creació:** 09/04/2026  
**Autor:** Òscar Alemán-Milán  
**Versió:** 2.0 (Actualitzada amb sistema d'edició)

## 1.0 Introducció

Aquesta guia està dissenyada específicament per a **analistes de dades i geoinformació** que treballen amb l'aplicació BDACC ACNA. El projecte ha evolucionat a una arquitectura modular completa amb capacitat d'edició de dades en temps real i sincronització amb Google Sheets.

---

## 2.0 Flux de Dades Actualitzat

### 2.1 Arquitectura de Dades
```
Google Sheets (Editable) 
        ||
        || (streamlit_gsheets)
        ||
        ||
    Streamlit App
        ||
        || (process_data)
        ||
        ||
    DataFrame (df_editable)
        ||
        || (apply_filters)
        ||
        ||
    DataFrame Filtrat (dff)
        ||
        || (visualizations)
        ||
        ||
    Mapes + Gràfics + KPIs
        ||
        || (edición usuario)
        ||
        ||
    Google Sheets (sync)
```

### 2.2 Pipeline de Processament
1. **Selecció d'origen de dades**
   - **Local Excel**: `data/bd_accidents_200726_net_c.xlsx`
   - **Google Sheets**: URL pública o privada
   - **Fitxer pujat**: Upload dinàmic

2. **Càrrega i Processament**
   - `load_data()` o `load_from_gsheet()`
   - `process_data()` - Neteja i estandardització
   - `ensure_pyarrow_compatibility()` - Compatibilitat Streamlit

3. **Filtratge Dinàmic**
   - `apply_filters()` - Aplicació de filtres complexos
   - Validació geogràfica (Península Ibèrica)
   - Filtratge temporal i categòric

4. **Visualització Interactiva**
   - Mapes (pydeck + Folium)
   - Gràfics temporals i de composició
   - KPI Dashboard
   - Taula de dades editable

5. **Edició i Sincronització**
   - `st.data_editor()` - Edició directa
   - `conn.update()` - Sincronització Google Sheets
   - Persistència d'estat d'edició

---

## 3.0 Sistema d'Edició de Dades

### 3.1 Arquitectura d'Edició
El sistema d'edició implementa la solució de Gemini per a la persistència de dades:

```python
# Inicialització única
if 'df_editable' not in st.session_state:
    st.session_state.df_editable = ensure_pyarrow_compatibility(dff)

# Mode edició
if st.session_state.editing_table:
    st.session_state.df_editable = st.data_editor(
        st.session_state.df_editable,
        column_config=config_cols,
        num_rows="dynamic",
        key="main_data_editor"
    )
```

### 3.2 Característiques d'Edició
- **Persistència**: Els canvis es guarden automàticament a `st.session_state.df_editable`
- **Validació**: Compatibilitat PyArrow per a Streamlit
- **Sincronització**: Guardat manual a Google Sheets
- **Error Handling**: Maneig robust d'errors de DataFrame

### 3.3 Flux d'Edició
1. **Entrar en Mode Edició**: Botó "Editar Taula"
2. **Edició Directa**: `st.data_editor` amb cel·les editables
3. **Guardat Local**: Canvis persisteixen a la sessió
4. **Sincronització**: Botó "Guardar Canvis" per a Google Sheets
5. **Sortida**: Botó "Cancel·lar" per sortir del mode edició

---

## 4.0 Estructura Modular Actualitzada

### 4.1 `src/data_processing.py` - Pipeline de Dades
**Funcions clau:**
- `load_data(file_path)` - Càrrega Excel
- `load_from_gsheet(url)` - Càrrega Google Sheets
- `process_data(df)` - Neteja i estandardització
- `apply_filters(df, filters_dict, metrica)` - Filtratge complex
- `get_column_options(df, col)` - Opcions per a filtres

**Canvis recents:**
- Millor maneig de dates i coordenades
- Validació geogràfica més robusta
- Optimització de memòria per a grans datasets

### 4.2 `src/visualization.py` - Motor de Visualitzacions
**Funcions clau:**
- `create_map_layer()` - Mapes pydeck interactius
- `create_data_table()` - Taula amb edició
- `create_temporal_chart()` - Gràfics temporals
- `create_composition_charts()` - Anàlisi categòrica
- `create_kpi_dashboard()` - Mètriques clau
- `handle_map_click()` - Interaccions amb mapa

**Característiques noves:**
- Sistema complet d'edició de dades
- Sincronització amb Google Sheets
- Compatibilitat PyArrow
- Maneig d'errors robust

### 4.3 `src/ui_components.py` - Components d'Interfície
**Funcions clau:**
- `create_data_source_sidebar()` - Selecció de dades
- `create_filters_sidebar()` - Panell de filtres
- `create_map_controls()` - Controls del mapa
- `inject_custom_styles()` - Estils CSS
- `create_page_header()` - Capçalera
- `create_footer()` - Peu de pàgina

**Millora UX:**
- Disseny responsiu
- Missatges d'error clars
- Navegació millorada
- Accessibilitat millorada

### 4.4 `src/map_folium.py` - Mapes Folium
**Funcions clau:**
- `create_folium_map()` - Creació de mapa
- `get_folium_html()` - Conversió HTML
- `handle_folium_click()` - Interaccions

**Característiques:**
- Múltiples capes base
- Controls interactius
- Mode edició per a punts
- Marcadors personalitzats

### 4.5 `config/settings.py` - Configuració Global
**Constants clau:**
- `PAGE_CONFIG` - Configuració Streamlit
- `COLORS` - Esquema de colors
- `MAP_CONFIG` - Configuració de mapes
- `HTML_TEMPLATES` - Plantilles HTML

---

## 5.0 Sistema de Google Sheets

### 5.1 Integració
```python
# Connexió
conn = st.connection("gsheets")

# Actualització
conn.update(worksheet=df_to_save)
```

### 5.2 Característiques
- **Edició en temps real**: Canvis immediats a Google Sheets
- **Validació de dades**: Comprovació de tipus abans de pujar
- **Maneig d'errors**: Errors específics per a Google Sheets
- **Cache automàtic**: `st.cache_data.clear()` després d'actualitzar

### 5.3 Flux de Sincronització
1. **Edició local**: Canvis a `st.session_state.df_editable`
2. **Validació**: Comprovació de tipus de dades
3. **Preparació**: `ensure_pyarrow_compatibility()`
4. **Actualització**: `conn.update(worksheet=df_to_save)`
5. **Confirmació**: Missatge d'èxit i refresc

---

## 6.0 Millora de Rendiment i UX

### 6.1 Optimitzacions de Rendiment
- **Caching**: `@st.cache_data` en funcions costoses
- **Lazy Loading**: Càrrega de dades només quan cal
- **Memòria**: Optimització de DataFrames
- **Renderitzat**: Mapes optimitzats per a grans datasets

### 6.2 Millora d'Experiència d'Usuari
- **Disseny responsiu**: Adaptació a mòbil i escriptori
- **Feedback visual**: Indicadors de càrrega i progrés
- **Missatges d'error**: Clars i en català
- **Accessibilitat**: Navegació per teclat i lector de pantalla

### 6.3 Maneig d'Errors
- **Validació de dades**: Comprovacions abans de processar
- **Errors específics**: Missatges detallats per a cada error
- **Recuperació**: Opcions per a recuperar-se d'errors
- **Logging**: Informació per a debugging

---

## 7.0 Guia Pràctica per a Analistes

### 7.1 Afegir Nous Filtres
```python
# 1. A ui_components.py - Afegir control
def create_filters_sidebar(filters_dict):
    # Nou filtre
    nou_filtre = st.sidebar.selectbox("Nou Filtre", options)
    filters_dict['nou_filtre'] = nou_filtre

# 2. A data_processing.py - Aplicar filtre
def apply_filters(df, filters_dict, metrica="Accidents"):
    dff = df.copy()
    if 'nou_filtre' in filters_dict:
        dff = dff[dff['columna'] == filters_dict['nou_filtre']]
    return dff
```

### 7.2 Afegir Nova Visualització
```python
# 1. A visualization.py - Crear funció
def create_nova_visualitzacio(dff):
    if dff.empty:
        return None
    fig = px.scatter(dff, x='x', y='y')
    return fig

# 2. A bdacc_acna_app.py - Integrar
def render_nova_seccio(dff):
    st.markdown("## Nova Visualització")
    fig = create_nova_visualitzacio(dff)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
```

### 7.3 Modificar Sistema d'Edició
```python
# A visualization.py - Modificar create_data_table
def create_data_table(dff, original_file_path=None):
    # Afegir nova validació
    if 'nou_camp' in df_to_save.columns:
        df_to_save['nou_camp'] = df_to_save['nou_camp'].astype(str)
    
    # Afegir nova lògica de guardat
    if st.button("Nova Acció"):
        # Nova funcionalitat
        pass
```

---

## 8.0 Resolució de Problemes Comuns

### 8.1 Errors de Google Sheets
- **Error**: `GSheetsConnection.update() argument mismatch`
  - **Solució**: Usar `worksheet=df_to_save` com a argument amb nom
- **Error**: `The truth value of a DataFrame is ambiguous`
  - **Solució**: Usar `if df is not None` en lloc de `if df`

### 8.2 Errors de PyArrow
- **Error**: PyArrow compatibility issues
  - **Solució**: Usar `ensure_pyarrow_compatibility()`
- **Error**: String conversion issues
  - **Solució**: Forçar tipus string a columnes categòriques

### 8.3 Problemes de Rendiment
- **Error**: Mapa lent amb molts punts
  - **Solució**: Limitar densitat de punts o usar clustering
- **Error**: Càrrega lenta de dades
  - **Solució**: Optimitzar `process_data()` o usar caching

---

## 9.0 Bones Pràctiques

### 9.1 Desenvolupament
- **Modularitat**: Mantenir funcions separades per responsabilitat
- **Documentació**: Afegir docstrings a funcions noves
- **Testing**: Provar amb diferents tipus de dades
- **Version Control**: Fer commits freqüents amb missatges clars

### 9.2 Dades
- **Validació**: Sempre validar dades d'entrada
- **Neteja**: Mantenir consistència en noms de columnes
- **Seguretat**: No emmagatzemar credencials al codi
- **Backup**: Mantenir còpies de seguretat de dades

### 9.3 UI/UX
- **Consistència**: Mantenir estil consistent
- **Accessibilitat**: Assegurar-se que és accessible
- **Feedback**: Proporcionar feedback clar a l'usuari
- **Errors**: Manejar errors amb gràcia

---

## 10.0 Futur de l'Aplicació

### 10.1 Millores Planificades
- **Anàlisi Avançada**: Models predictius de risc
- **Exportació**: PDF i altres formats
- **Col·laboració**: Edició multiusuari
- **Mòbil**: Aplicació mòbil nativa

### 10.2 Integracions Futures
- **APIs externes**: Dades meteorològiques
- **Bases de dades**: PostgreSQL o MongoDB
- **Cloud**: AWS o Google Cloud
- **Monitoring**: Sistema de monitoratge

### 10.3 Escalabilitat
- **Microserveis**: Arquitectura de microserveis
- **Docker**: Contenització
- **CI/CD**: Pipeline de desplegament
- **Testing**: Suite de tests automatitzats

---

## 11.0 Recursos i Documentació

### 11.1 Documentació Tècnica
- **Streamlit**: https://docs.streamlit.io
- **Pandas**: https://pandas.pydata.org/docs/
- **Plotly**: https://plotly.com/python/
- **Folium**: https://python-visualization.github.io/folium/

### 11.2 APIs i Serveis
- **Google Sheets API**: https://developers.google.com/sheets/api
- **Pydeck**: https://pydeck.gl
- **OpenStreetMap**: https://www.openstreetmap.org/

### 11.3 Comunitat
- **GitHub**: Repositori del projecte
- **Streamlit Community**: Fòrum i exemples
- **Python Data Science**: Recursos i tutorials

---

**Recorda**: Aquesta arquitectura està dissenyada per ser **modificable i escalable**. No tinguis por a experimentar i adaptar-la a les teves necessitats d'anàlisi de dades!

---

## 12.0 Contacte i Suport

Si necessites ajuda o tens preguntes:
1. Revisa aquesta guia
2. Consulta la documentació tècnica
3. Prova amb dades de mostra
4. Usa `st.write()` per debugging
5. Contacta amb l'equip de desenvolupament

**Última actualització**: 09/04/2026
**Versió**: 2.0 - Sistema d'Edició Complet
