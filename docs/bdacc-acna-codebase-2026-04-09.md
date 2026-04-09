# BDACC ACNA Codebase Knowledge Base (Creation date: 09/04/2026)

## Project Overview
- **Name**: Base de Dades d'Accidents per Allaus - ACNA (Avalanche Accident Database)
- **Type**: Streamlit web application for analyzing avalanche accident data
- **Language**: Catalan (comments and UI), Python code
- **License**: MIT (© 2026 Òscar Alemán-Milán)
- **Purpose**: Interactive visualization and statistical analysis of ACNA avalanche database
- **Architecture**: Modular design with separated concerns

---

## Build & Deployment

### Environment Setup (Conda)
- **Environment file**: `allaus_env.yml` (Conda YAML format)
- **Environment name**: `allaus_env`
- **Python version**: 3.11.15
- **Conda channels**: conda-forge, repo.anaconda.com (main, r, msys2)
- **Prefix**: `C:\Users\oscar\anaconda3\envs\allaus_env`

### Core Dependencies
- **streamlit** (1.55.0) - web framework for dashboards
- **pandas** (2.3.3) - data processing
- **plotly** (6.6.0) - interactive charts
- **pydeck** (0.9.1) - map visualization (deck.gl)
- **openpyxl** (3.1.5) - Excel file handling
- **streamlit_gsheets** - Google Sheets integration
- **streamlit_folium** - Folium map integration
- **folium** - Interactive maps
- **numpy** - Numerical operations

### Run Command
```bash
streamlit run bdacc_acna_app.py
```

### Data File Location
- Default: `data/bd_accidents_200726_net_c.xlsx` (Excel file)
- Alternative sources: Google Sheets or custom local uploads

---

## Architecture & Component Boundaries

### Main Application (`bdacc_acna_app.py`)
- **Entry point**: 717 lines, orchestrates all modules
- **Session state management**: Handles editing modes and data persistence
- **Component coordination**: Manages UI layout and data flow

### Modular Structure (`src/`)

#### 1. **`src/data_processing.py`** - Data Pipeline
- **Functions**:
  - `load_data(file_path)` - Loads Excel or uploaded files
  - `load_from_gsheet(url)` - Loads data from Google Sheets
  - `process_data(df)` - Core data cleaning and standardization
  - `apply_filters(df, filters_dict, metrica)` - Apply complex filters
  - `get_column_options(df, col)` - Get unique values for dropdowns
- **Data cleaning**:
  - Strips whitespace from column names
  - Converts coordinates (comma->dot decimal): Latitud, Longitud
  - Filters geographic bounds (Iberian Peninsula: 30-50°N, -10-10°E)
  - Normalizes date formats (dd/mm/yyyy primary, mm/dd/yyyy fallback)
  - Creates helper columns: Data_str, Any, Mes, Accidents count
  - Converts numeric columns to int: Morts, Ferits, Arrossegats
  - Normalizes categorical missing values (NaN/"None"/"" -> "Desconegut")

#### 2. **`src/visualization.py`** - Visualizations Engine
- **Core Functions**:
  - `create_map_layer(dff, show_points, show_heatmap, ...)` - Interactive pydeck maps
  - `create_temporal_chart(dff, chart_type)` - Temporal evolution charts
  - `create_composition_charts(dff, vars_percent, ...)` - Composition analysis
  - `create_kpi_dashboard(dff)` - KPI calculations
  - `create_data_table(dff, original_file_path)` - Data table with editing
  - `render_kpi_boxes(kpi_data)` - KPI UI rendering
  - `export_to_excel(df)` - Excel export functionality
  - `handle_map_click(click_data, dff)` - Map interaction handling
- **Support Functions**:
  - `ensure_pyarrow_compatibility(df)` - PyArrow compatibility
  - `get_map_center_zoom(dff)` - Map center calculation
  - `get_simplified_tooltip_html()` - Tooltip HTML template

#### 3. **`src/ui_components.py`** - UI Components
- **Styling Functions**:
  - `inject_custom_styles()` - Custom CSS injection
  - `create_page_header()` - Header component
  - `create_footer()` - Footer component
- **Sidebar Components**:
  - `create_data_source_sidebar()` - Data source selection
  - `create_filters_sidebar()` - Filter controls
  - `create_map_controls()` - Map control buttons
  - `create_map_style_controls()` - Map style selection
  - `create_composition_chart_controls()` - Chart configuration
- **Message Functions**:
  - `sidebar_error(message)` - Error messages
  - `sidebar_success(message)` - Success messages
  - `sidebar_info(message)` - Info messages
  - `show_empty_data_message()` - Empty state handling

#### 4. **`src/map_folium.py`** - Folium Maps
- **Core Functions**:
  - `create_folium_map(dff, show_points, auto_fit, edit_mode, new_point)` - Folium map creation
  - `get_folium_html(map_object)` - HTML conversion
  - `handle_folium_click()` - Map click handling
- **Features**:
  - Multiple tile layers (OpenStreetMap, CartoDB, Topographic)
  - Interactive controls (fullscreen, locate, edit)
  - Custom markers and popups
  - Edit mode for point addition

#### 5. **`src/ui_folium.py`** - Folium UI Controls
- **Functions**:
  - `create_folium_controls()` - Folium-specific UI controls
- **Purpose**: Lightweight Folium-specific UI components

#### 6. **`src/utils.py`** - Utility Functions
- **Data validation and processing utilities**
- **Format conversion functions**
- **Percentage calculations**
- **Text processing utilities**

#### 7. **`config/settings.py`** - Configuration
- **Constants**:
  - `PAGE_CONFIG` - Streamlit page configuration
  - `COLORS` - Color scheme definitions
  - `MAP_CONFIG` - Map configuration and styles
  - `HTML_TEMPLATES` - HTML templates for UI
  - `DEFAULT_DATA_FILE` - Default data file path
  - `UI_CONFIG` - UI configuration parameters

---

## Data Flow & State Management

### Session State Architecture
- **`df`**: Original loaded dataset
- **`dff`**: Filtered dataset for current view
- **`df_editable`**: Editable DataFrame for data table
- **`editing_table`**: Boolean flag for edit mode
- **`data_source`**: Current data source (local/gsheets)
- **`gsheets_conn`**: Google Sheets connection object

### Data Processing Pipeline
```
1. Data Source Selection (Local Excel/Google Sheets) ->
2. Data Loading (load_data/load_from_gsheet) ->
3. Data Processing (process_data) ->
4. Filter Application (apply_filters) ->
5. Visualization (maps/charts/KPIs) ->
6. Optional Editing (create_data_table) ->
7. Export (Excel/Google Sheets)
```

### Google Sheets Integration
- **Connection**: `st.connection("gsheets")` via streamlit_gsheets
- **Update Method**: `conn.update(worksheet=df_to_save)`
- **Edit Mode**: Direct table editing with persistence
- **Sync**: Real-time synchronization with Google Sheets

---

## Recent Changes & Improvements

### Data Editing System (April 2026)
- **Implemented**: Complete data table editing functionality
- **Features**:
  - Direct cell editing with `st.data_editor`
  - Persistent state management with `df_editable`
  - Google Sheets synchronization
  - PyArrow compatibility for Streamlit
  - Error handling for ambiguous DataFrame truth values
- **Architecture**: Gemini's solution for persistent editing

### Map System Enhancements
- **Dual Map System**: pydeck + Folium integration
- **Interactive Features**:
  - Point addition/editing
  - Multiple tile layers
  - Fullscreen and locate controls
  - Custom markers and popups
- **Performance**: Optimized rendering and caching

### UI/UX Improvements
- **Responsive Design**: Better mobile and desktop layouts
- **Error Handling**: Comprehensive error messages and validation
- **Performance**: Caching optimizations and faster data loading
- **Accessibility**: Improved keyboard navigation and screen reader support

---

## Project Conventions

### Naming & Structure
- **Modular Architecture**: Separated concerns in src/ modules
- **Catalan UI**: All user-facing text in Catalan
- **Catalan column names**: Expected in data (Lloc, Temporada, Grau de perill, etc.)
- **Snake_case**: Python variables and functions
- **Asset naming**: `brand-acna-*.{jpg,png}` in assets/

### Data Conventions
- **Coordinates**: String format with comma decimals ("42,345") -> converted to float
- **Dates**: Mixed formats (dd/mm/yyyy primary, mm/dd/yyyy fallback)
- **Missing values**: Explicit "Desconegut" (Catalan for "Unknown")
- **Numeric columns**: Integers (deaths, injured, carried away)
- **Units**: Coordinates in decimal degrees, altitude in Altitud column

### Styling Patterns
- **Custom HTML/CSS**: Injected via `st.markdown(..., unsafe_allow_html=True)`
- **Flexbox Layout**: Responsive design patterns
- **Dark/Light Theme**: Theme-aware styling
- **Color Scheme**: Turquoise accent (#40E0D0), dark bg (#0e1117/#ffffff)

### Caching Strategy
- **`@st.cache_data`**: On data loading and processing functions
- **Session State**: For UI state and editing modes
- **Cache Invalidation**: Automatic cache clearing on data updates

---

## Potential Pitfalls & Common Issues

### 1. **Data Dependencies**
- **Error**: `FileNotFoundError: Fitxer no trobat`
  - **Fix**: Ensure Excel file exists or use Google Sheets mode
- **Error**: Coordinates outside geographic bounds
  - **Fix**: Check data format and geographic filters
- **Error**: Date parsing failures
  - **Fix**: Validate date formats and handle edge cases

### 2. **Google Sheets Integration**
- **Error**: `GSheetsConnection.update() argument mismatch`
  - **Fix**: Use named argument `worksheet=df_to_save`
- **Error**: DataFrame ambiguous truth value
  - **Fix**: Use `if df is not None` instead of `if df`
- **Error**: PyArrow compatibility issues
  - **Fix**: Use `ensure_pyarrow_compatibility()` function

### 3. **Performance Issues**
- **Large datasets**: Consider pagination or filtering
- **Map rendering**: Optimize point density and layer complexity
- **Cache issues**: Clear cache manually if needed

### 4. **Environment Setup**
- **Conda dependencies**: Use provided environment file
- **Python version**: Stick to 3.11.15 for compatibility
- **Windows paths**: Adjust environment paths if needed

---

## Key Files & Patterns

| File/Dir | Purpose | Key Functions |
|----------|---------|---------------|
| `bdacc_acna_app.py` | Main application | `main()`, session state management |
| `src/data_processing.py` | Data pipeline | `load_data()`, `process_data()`, `apply_filters()` |
| `src/visualization.py` | Visualizations | `create_map_layer()`, `create_data_table()` |
| `src/ui_components.py` | UI components | `create_*_sidebar()`, `inject_custom_styles()` |
| `src/map_folium.py` | Folium maps | `create_folium_map()`, `get_folium_html()` |
| `config/settings.py` | Configuration | Global constants and settings |
| `data/bd_accidents_200726_net_c.xlsx` | Default dataset | Excel with specific schema |
| `allaus_env.yml` | Environment | Conda environment specification |

---

## Development Guidelines

### Adding New Features
1. **Data Processing**: Add to `src/data_processing.py`
2. **Visualizations**: Add to `src/visualization.py`
3. **UI Components**: Add to `src/ui_components.py`
4. **Configuration**: Update `config/settings.py`
5. **Main App**: Update `bdacc_acna_app.py` for integration

### Testing & Debugging
- **Use `st.write()`**: For debugging data structures
- **Check session state**: Verify state management
- **Test with different data sources**: Local Excel, Google Sheets
- **Validate edge cases**: Empty data, invalid coordinates

### Performance Optimization
- **Cache expensive operations**: Use `@st.cache_data`
- **Optimize data loading**: Load only necessary columns
- **Map performance**: Limit point density for large datasets
- **UI responsiveness**: Use proper layout patterns

---

## Suggested Documentation Links
- **Streamlit docs**: https://docs.streamlit.io
- **Pydeck API**: https://pydeck.gl
- **Plotly Express**: https://plotly.com/python/plotly-express/
- **Pandas data cleaning**: https://pandas.pydata.org/docs/
- **Folium maps**: https://python-visualization.github.io/folium/
- **Google Sheets API**: https://developers.google.com/sheets/api

---

## Development Status
- **Architecture**: Fully modularized
- **Testing**: No formal test suite
- **CI/CD**: No automated deployment
- **Documentation**: Comprehensive technical and user guides
- **Version Control**: Git with proper branching
- **Dependencies**: Managed via Conda environment
