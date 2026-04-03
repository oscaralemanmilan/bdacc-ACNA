# Project Guidelines

## Code Style
- Use Catalan for comments and UI strings
- Hardcoded column names in Catalan (Latitud, Longitud, Morts, etc.)
- Custom CSS for dark/light theme with turquoise accents (#40E0D0)

## Architecture
- Single-file Streamlit application (~700 lines) handling data loading, processing, filtering, and visualization
- Data pipeline: Load from Excel file or Google Sheets, normalize coordinates (comma-decimal), impute missing values with "Desconegut"
- Components: Sidebar filters (14 categories), map visualization (Pydeck with scatterplot/heatmap), charts (Plotly), export table
- Caching: Use `@st.cache_data` for performance on data operations

## Build and Test
- Environment: Use Conda with `allaus_env.yml` (Python 3.11, pinned dependencies)
- Install: `conda env create -f allaus_env.yml`
- Run: `streamlit run bdacc_acna_app.py`
- No automated tests or CI/CD present

## Conventions
- Data bounds: Filter to Iberian peninsula (30-50°N, -10-10°E)
- Missing values: Explicitly handled as "Desconegut" (Unknown)
- File structure: Data in `data/` folder, assets in `assets/` folder
- Performance: Expect slowdowns with datasets >10k rows due to heatmap rendering</content>
<parameter name="filePath">e:\OneDrive - UAB\APPs_dev\bdacc-ACNA\.github\copilot-instructions.md