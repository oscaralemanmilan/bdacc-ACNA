# BDACC ACNA Codebase Knowledge Base (Creation date: 03/04/2026)

## Project Overview
- **Name**: Base de Dades d'Accidents per Allaus - ACNA (Avalanche Accident Database)
- **Type**: Streamlit web application for analyzing avalanche accident data
- **Language**: Catalan (comments and UI), Python code
- **License**: MIT (© 2026 Òscar Alemán-Milán)
- **Purpose**: Interactive visualization and statistical analysis of ACNA avalanche database

---

## Build & Deployment

### Environment Setup (Conda)
- **Environment file**: `allaus_env.yml` (Conda YAML format)
- **Environment name**: `allaus_env`
- **Python version**: 3.11.15
- **Conda channels**: conda-forge, repo.anaconda.com (main, r, msys2)
- **Prefix**: `C:\Users\oscar\anaconda3\envs\allaus_env`

### Core Dependencies
- **streamlit** (1.55.0) — web framework for dashboards
- **pandas** (2.3.3) — data processing
- **plotly** (6.6.0) — interactive charts
- **pydeck** (0.9.1) — map visualization (deck.gl)
- **openpyxl** (3.1.5) — Excel file handling

### Run Command
```bash
streamlit run bdacc_acna_app.py
```

### Data File Location
- Default: `data/bd_accidents_200726_net_c.xlsx` (Excel file)
- Alternative sources: Google Sheets or custom local uploads

---

## Architecture & Component Boundaries

### Main Components (in `bdacc_acna_app.py`)

#### 1. **Data Processing Pipeline**
- `load_data(file_path)` — Loads Excel or uploaded files
- `process_data(df)` — Core data cleaning:
  - Strips whitespace from column names
  - Converts coordinates (comma→dot decimal): Latitud, Longitud
  - Filters geographic bounds (Iberian Peninsula: 30-50°N, -10-10°E)
  - Normalizes date formats (tries day/month/year first, then month/day/year)
  - Creates helper columns: Data_str, Any, Mes, Accidents count
  - Converts numeric columns to int: Morts, Ferits, Arrossegats
  - Normalizes categorical missing values (NaN/"None"/"" → "Desconegut")
- `load_from_gsheet(url)` — Loads data from public Google Sheets

#### 2. **UI & Styling**
- Custom Streamlit CSS for dark/light theme support
- Color scheme: Turquoise accent (#40E0D0)
- Responsive sidebar with three data source options:
  - Local (default): pre-indexed file
  - Local personalitzat: user upload
  - Google Sheet: URL-based
- Custom footer positioning and KPI boxes

#### 3. **Data Filtering (Sidebar)**
- Metric selector: Accidents, Morts, Ferits, Arrossegats
- Chart type toggle: Barres (bar) / Línia (line)
- Multi-select filters (14 categories):
  - Temporal: Temporada, Mes
  - Activity: Tipus activitat
  - Risk: Grau de perill
  - Geography: Pais, Regio, Serralada, Orientacio
  - Avalanche: Origen, Progressio, Desencadenant, Material, Altitud, Mida allau

#### 4. **Visualizations**
- **Map (pydeck)**: Interactive deck.gl rendering with:
  - ScatterplotLayer (points, turquoise, configurable radius/opacity)
  - HeatmapLayer (density visualization, gradient: aqua→purple→magenta→yellow)
  - Custom tooltips showing full record details
  - CartoDB dark-matter base map
- **Temporal chart (plotly)**: Line or bar chart (Accidents vs Morts by Temporada)
- **Composition charts (plotly)**: 2-column layout with switchable:
  - Variables (from vars_percent list)
  - Chart types: Pastís (pie), Barres (V/H) bars
- **Data table**: Expandable section with 19 columns + CSV export

#### 5. **KPI Dashboard**
6-column metrics row showing:
- Accidents filtrats (total records)
- % accidents amb morts / ferits
- % morts/ferits per arrossegats
- Total arrossegats

#### 6. **Global Variables**
- `vars_percent`: 10 categorical analysis variables (standardized analysis targets)
- `opts(col)`: Returns sorted unique values for dropdowns
- `map_center_zoom(d)`: Fixed to Iberian Peninsula (40.0°N, -3.5°E, zoom 4.9)

---

## Project Conventions

### Naming & Structure
- **Single-file app**: All logic in `bdacc_acna_app.py` (no modules yet)
- **Catalan UI**: All user-facing text in Catalan (titles, labels, help text)
- **Catalan column names**: Expected in data (Lloc, Temporada, Grau de perill, Mida allau, etc.)
- **Snake_case**: Python variables and functions
- **Asset naming**: `brand-acna-*.{jpg,png}` and `Allau_ACNA.jpg` in assets/

### Data Conventions
- **Coordinates**: String format with comma decimals ("42,345") → converted to float
- **Dates**: Mixed formats (dd/mm/yyyy primary, mm/dd/yyyy fallback)
- **Missing values**: Explicit "Desconegut" (Catalan for "Unknown")
- **Numeric columns**: Integers (deaths, injured, carried away)
- **Units**: Coordinates in decimal degrees, altitude implied in Altitud column

### Styling Patterns
- Custom HTML/CSS injected via `st.markdown(..., unsafe_allow_html=True)`
- Flexbox for layout alignment
- Dark theme default with light theme fallback
- Inline color variables: turquoise (#40E0D0), dark bg (#0e1117/#ffffff)

### Caching Strategy
- `@st.cache_data` on `load_data()` and `process_data()` for performance
- Global `df` variable shared across session
- Filtered copy `dff` created per view to preserve original

---

## Potential Pitfalls & Common Issues

### 1. **Data Dependencies**
- ❌ **Error**: `FileNotFoundError: Fitxer no trobat: data/bd_accidents_200726_net_c.xlsx`
  - **Fix**: Ensure Excel file exists in `data/` folder or use Google Sheets mode
- ❌ **Error**: Coordinates outside bounding box (e.g., world-wide data)
  - **Fix**: Geographic filter expects 30-50°N, -10-10°E; non-matches show warning
- ❌ **Error**: Date parsing failures
  - **Fix**: App tries two formats; dates outside valid range become NaT

### 2. **Environment Setup**
- **Conda-specific**: Must use Conda environment (not pip) due to `openpyxl`, `pydeck` binary deps
- **Python 3.11**: Pinned version; newer main Python may have compatibility issues
- **Windows path**: Env location hardcoded in YAML; may need adjustment on new machine
- **Live reload**: Streamlit auto-reruns on code changes; can be slow with large datasets

### 3. **Data Processing Edge Cases**
- Empty/NaN categorical fields become "Desconegut" — may skew filtering
- Numeric cols (Morts, Ferits) default to 0 if missing — affects sum aggregations
- Multiple date formats may cause inconsistent parsing — validate with Data_str column
- Google Sheets export as CSV (some formatting lost vs. Excel)

### 4. **Performance Issues**
- Large datasets slow map rendering; consider client-side filtering
- Heatmap layer is CPU-intensive; disable if <5000 points
- Cache keys don't detect file changes automatically (user must clear cache)

### 5. **Catalan-Specific**
- All UI labels assume Catalan; no i18n (internationalization) support
- Column names must match exactly (case-sensitive)
- Month names hardcoded in Spanish/Catalan map; no auto-translation

---

## Key Files & Patterns

| File/Dir | Purpose | Patterns |
|----------|---------|----------|
| `bdacc_acna_app.py` | Main application (700+ lines) | Streamlit patterns: caching, custom CSS, multi-view |
| `data/bd_accidents_200726_net_c.xlsx` | Default dataset | Excel with specific column schema |
| `assets/brand-acna-*.{jpg,png}` | Logo/branding images | Sized for sidebar (290px, 200px) |
| `allaus_env.yml` | Conda environment | Full dependency tree with versions |
| `README.md` | Project description | Minimal (2 lines); needs expansion |
| `LICENSE` | MIT License | Standard MIT boilerplate |

---

## Suggested Documentation Links
- **Streamlit docs**: https://docs.streamlit.io
- **Pydeck API**: https://pydeck.gl
- **Plotly Express**: https://plotly.com/python/plotly-express/
- **Pandas data cleaning**: https://pandas.pydata.org/docs/reference/frame.html
- **Conda cheat sheet**: https://conda.io/projects/conda/en/latest/user-guide/cheatsheet.html

---

## Development Ready Notes
- No test suite (pytest/unittest not in dependencies)
- No module structure (monolithic file)
- Git repo present (`.git/` directory, `.gitignore` exists)
- No CI/CD config (no GitHub Actions, etc.)
- No docstrings (rely on inline Catalan comments)
- Single developer (Òscar Alemán-Milán)
