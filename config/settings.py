"""
Mòdul de Configuració per a BDACC ACNA
========================================

Conté constants i paràmetres de configuració global de l'aplicació.

Autor: Òscar Alemán-Milán © 2026
"""

# --------------------------------------------------------
# CONFIGURACIÓ GENERAL DE L'APLIACIÓ
# --------------------------------------------------------
PAGE_CONFIG = {
    "page_title": "Base de Dades d'Accidents per Allaus ACNA",
    "layout": "wide"
}

DEFAULT_DATA_FILE = "data/bd_accidents_200726_net_c.xlsx"  # Pot tenir problemes de permisos

# --------------------------------------------------------
# COLORS I ESTILS
# --------------------------------------------------------
COLORS = {
    # Colors principals
    "turquoise": "#40E0D0",
    "turquoise_rgb": (64, 224, 208),  # RGB per pydeck
    
    # Colors de fons
    "dark_bg": "#0e1117",
    "light_bg": "#ffffff",
    "sidebar_dark": "#000000",
    "sidebar_light": "#f0f0f0",
    
    # Colors per mapa de calor
    "heatmap_gradient": [
        [30, 180, 200, 70],    # baixa densitat - aqua suau
        [0, 120, 160, 140],    # teal
        [80, 70, 200, 190],    # indigo / violeta
        [210, 80, 130, 230],   # magenta intens
        [255, 220, 60, 255],   # alt - groc/ambre
    ],
    
    # Colors per avisos
    "error_bg": "#ffdddd",
    "error_text": "#a80000",
    "error_border": "#ff8080",
    "success_bg": "#ddffdd",
    "success_text": "#1f7a1f",
    "success_border": "#80ff80",
    "info_bg": "#e7f4ff",
    "info_text": "#155a8a",
    "info_border": "#8ec8ff"
}

# --------------------------------------------------------
# CONFIGURACIÓ DEL MAPA
# --------------------------------------------------------
MAP_CONFIG = {
    # Centre i zoom per defecte (Península Ibèrica)
    "default_center": {"lat": 40.0, "lon": -3.5},
    "default_zoom": 4.9,
    
    # Estils de mapa disponibles (sense API)
    "available_styles": {
        "Fosc": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        "Clar": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        "Voyager": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
        "Topogràfic": "stamen_terrain"  # Especial per TileLayer
    },
    
    # URLs per TileLayer (mapes que necessiten capes addicionals)
    "tile_layer_urls": {
        "stamen_terrain": "https://tile.opentopomap.org/{z}/{x}/{y}.png",
        "satelite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "ign_raster": "https://tms-mapa-raster.ign.es/1.0.0/mapa-raster/{z}/{x}/{y}.jpeg",
        "test_osm": "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    },
    
    # Estil actual per defecte
    "current_style": "Fosc",
    
    # Configuració per defecte del mapa
    "default_point_radius": 5,
    "default_point_opacity": 0.8,
    "default_heat_radius": 6,
    "default_heat_intensity": 10.0
}

# --------------------------------------------------------
# CONFIGURACIÓ DE GRÀFICS
# --------------------------------------------------------
CHART_CONFIG = {
    # Alçada per defecte dels gràfics
    "default_height": 480,
    
    # Template per defecte
    "default_template": "plotly",
    "dark_template": "plotly_dark",
    
    # Marges per defecte
    "default_margins": {"l": 20, "r": 20, "t": 20, "b": 20}
}

# --------------------------------------------------------
# CONFIGURACIÓ DE DADES
# --------------------------------------------------------
DATA_CONFIG = {
    # Columnes obligatòries
    "required_columns": ["Data", "Latitud", "Longitud"],
    
    # Columnes numèriques
    "numeric_columns": ["Morts", "Ferits", "Arrossegats"],
    
    # Columnes categòriques
    "categorical_columns": [
        "Temporada","Tipus activitat","Pais","Regio","Serralada","Orientacio",
        "Origen","Progressio","Desencadenant","Material","Altitud",
        "Grau de perill","Mes","Mida allau"
    ],
    
    # Valors per defecte per a dades buides
    "unknown_value": "Desconegut",
    
    # Límits geogràfics (Península Ibèrica)
    "geo_bounds": {
        "lat_min": 30, "lat_max": 50,
        "lon_min": -10, "lon_max": 10
    }
}

# --------------------------------------------------------
# CONFIGURACIÓ DE LA INTERFÍCIE
# --------------------------------------------------------
UI_CONFIG = {
    # Títols i textos
    "app_title": "BASE DE DADES D'ACCIDENTS PER ALLAUS - ACNA",
    
    # Opcions de mètriques
    "metric_options": ["Accidents","Morts","Ferits","Arrossegats"],
    
    # Opcions de tipus de gràfic temporal
    "temporal_chart_types": ["Barres","Línia"],
    
    # Opcions de tipus de gràfic de composició
    "composition_chart_types": ["Pastís", "Barres (V)", "Barres (H)"],
    
    # Opcions d'origen de dades
    "data_sources": ["Local", "Local personalitzat", "Google Sheet"],
    
    # Rutes d'assets
    "logo_path": "assets/brand-acna-02.jpg",
    "logo_width": 200
}

# --------------------------------------------------------
# CONFIGURACIÓ DE FILTRES
# --------------------------------------------------------
FILTER_CONFIG = {
    # Filtres temporals
    "temporal_filters": ["Temporada", "Mes"],
    
    # Filtres d'activitat
    "activity_filters": ["Tipus activitat"],
    
    # Filtres de risc
    "risk_filters": ["Grau de perill"],
    
    # Filtres geogràfics
    "geographic_filters": ["Pais", "Regio", "Serralada", "Orientacio"],
    
    # Filtres d'allau
    "avalanche_filters": ["Origen", "Progressio", "Desencadenant", "Material", "Altitud", "Mida allau"]
}

# --------------------------------------------------------
# CONFIGURACIÓ DE KPIs
# --------------------------------------------------------
KPI_CONFIG = {
    # Títols dels KPI
    "titles": [
        "Accidents filtrats",
        "% accidents amb morts",
        "% accidents amb ferits", 
        "% morts / arrossegats",
        "% ferits / arrossegats",
        "Arrossegats (total)"
    ],
    
    # Format dels números
    "decimal_places": 1
}

# --------------------------------------------------------
# CONFIGURACIÓ DE TEMPLATES HTML
# --------------------------------------------------------
HTML_TEMPLATES = {
    # Template per peu de pàgina
    "footer": """
    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #888; opacity: 1;">
        <div><b>Desenvolupament:</b> Òscar Alemán-Milán © 2026 |   |<b> Base de dades:</b>   Associació per al Coneixement de la Neu i les Allaus (ACNA), ICGC, Centre de Lauegi d'Aran i ARI.</div>
    </div>
    """,
    
    # Espai extra sota el contingut principal
    "main_padding": """
    <div style='margin-top:25px'></div>
    """
}
