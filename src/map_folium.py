"""
Mòdul de visualització de mapes amb Folium simplificat.
Proporciona mapes interactivus amb controls natius i punts d'accidents.

Autor: Òscar Alemán-Milán © 2026
"""

import folium
import streamlit as st
import pandas as pd
from config.settings import MAP_CONFIG
from branca.element import Template, MacroElement


def create_folium_map(dff, show_points=True, auto_fit=True, edit_mode=False, new_point=None, selected_map="Fosc"):
    """
    Crea un mapa interactiu amb Folium i múltiples capes base.
    
    Paràmetres:
    -----------
    dff : pandas.DataFrame
        Dades filtrades per mostrar
    show_points : bool
        Si es mostren els punts d'accidents
    auto_fit : bool
        Si el mapa s'ha d'ajustar automàticament als punts
    edit_mode : bool
        Si el mode d'edició està actiu (per mostrar cursor crosshair)
    new_point : dict
        Coordenades del nou punt per mostrar marcador de borrador
    selected_map : str
        Mapa seleccionado per defecte ("Fosc", "Clar", "Standard", "Topogràfic", "Satèl·lit")
    
    Retorna:
    --------
    folium.Map
        Mapa interactiu amb tots els elements configurats
    """
    
    # Centre i zoom per defecte (sempre iguals)
    center = MAP_CONFIG['default_center']
    
    # Crear mapa base sin tiles por defecto
    m = folium.Map(
        location=[center["lat"], center["lon"]], 
        zoom_start=5.5,  # Zoom original
        tiles=None,  # No especificar tiles per defecte
        control_scale=True,  # Reactivar escala gràfica
        control_zoom=True
    )
    
    # Definir configuración de capas según el mapa seleccionado
    capes_config = {
        "Satèl·lit": {
            "tiles": 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            "attr": 'Tiles &copy; Esri | OpenStreetMap contributors',
            "default": False
        },
        "Topogràfic": {
            "tiles": 'https://tile.opentopomap.org/{z}/{x}/{y}.png',
            "attr": 'OpenTopoMap | OpenStreetMap contributors',
            "default": False
        },
        "Standard": {
            "tiles": 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            "attr": 'OpenStreetMap contributors',
            "default": False
        },
        "Clar": {
            "tiles": 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            "attr": 'CARTO | OpenStreetMap contributors',
            "default": False
        },
        "Fosc": {
            "tiles": 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
            "attr": 'CARTO | OpenStreetMap contributors',
            "default": True  # Por defecto
        }
    }
    
    # Afegim les capes en ordre. La ÚLTIMA que s'afegeix és la que queda activa.
    # Primer les que NO volem per defecte
    altres_capes = ["Satèl·lit", "Topogràfic", "Standard", "Clar"]
    for nom in altres_capes:
        config = capes_config[nom]
        folium.TileLayer(
            tiles=config["tiles"],
            attr=config["attr"],
            name=nom,
            overlay=False,
            control=True,
            show=False  # Això fa que estiguin al selector però no es carreguin d'inici
        ).add_to(m)

    # Finalment afegim la capa per defecte (Fosc)
    config_fosc = capes_config["Fosc"]
    folium.TileLayer(
        tiles=config_fosc["tiles"],
        attr=config_fosc["attr"],
        name="Fosc",
        overlay=False,
        control=True,
        show=True  # Aquesta és la que es veurà només obrir
    ).add_to(m)

    # Ara el LayerControl sí que trobarà capes per mostrar
    folium.LayerControl(position='topright', collapsed=True).add_to(m)
    
    # Determinar estado inicial del botón
    initial_active = "true" if edit_mode else "false"
    initial_bg = "#02bfad" if edit_mode else "white"
    initial_color = "white" if edit_mode else "#333"
    initial_cursor = "crosshair" if edit_mode else "grab" # 'grab' es mejor que 'default' en mapas
    
    edit_control = MacroElement()
    edit_control._template = Template(f'''
        {{% macro script(this, kwargs) %}}
        // Usem 'topright' però forçarem la posició amb CSS
        var editControl = L.control({{position: 'topright'}});
        
        editControl.onAdd = function (map) {{
            var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
            
            // Reduïm el margin per igualar l'espai entre botons
            div.style.marginTop = '10px'; 
            div.style.marginRight = '10px'; // Una mica separat de la vora
            
            div.innerHTML = '<a title="Mode Edició" style="background-color: {initial_bg}; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; cursor: pointer; color: {initial_color}; border: 2px solid rgba(0,0,0,0.2); border-radius: 4px;"><i class="fa fa-map-marker" id="edit-icon"></i></a>';
            
            var editMode = {initial_active};
            
            // Aplicar cursor inicial tras un pequeño delay para asegurar que el mapa cargó
            setTimeout(function() {{
                map.getContainer().style.cursor = editMode ? 'crosshair' : 'grab';
            }}, 100);
            
            div.onclick = function(e) {{
                L.DomEvent.stopPropagation(e);
                editMode = !editMode;
                
                // Actualizar UI
                this.querySelector('a').style.backgroundColor = editMode ? "#02bfad" : "white";
                document.getElementById("edit-icon").style.color = editMode ? "white" : "#333";
                map.getContainer().style.cursor = editMode ? 'crosshair' : 'grab';
                
                // Enviar estado del modo edición a Streamlit
                window.parent.postMessage({{
                    isStreamlitMessage: true,
                    type: "streamlit:setComponentValue",
                    key: "mapa_principal",
                    value: {{
                        map_edit_mode_active: editMode
                    }}
                }}, "*");
                
                // Notificar a Streamlit del cambio de modo (fallback)
                window.parent.postMessage({{
                    type: 'streamlit:set_widget_value', 
                    key: 'map_edit_mode_active', 
                    value: editMode
                }}, '*');
            }};
            
            map.on('click', function(e) {{
                if (editMode) {{
                    var clickData = {{
                        lat: e.latlng.lat, 
                        lng: e.latlng.lng, 
                        t: Date.now()
                    }};
                    
                    // CORRECCIÓN: Usar la API correcta de comunicación con Streamlit
                    window.parent.postMessage({{
                        isStreamlitMessage: true,
                        type: "streamlit:setComponentValue",
                        key: "mapa_principal", // IMPORTANTE: Debe ser la misma KEY que usas en st_folium()
                        value: {{
                            last_map_click: clickData
                            // Si quieres, puedes añadir más datos aquí
                        }}
                    }}, "*");
                    
                    // También enviamos el mensaje genérico por si acaso
                    window.parent.postMessage({{
                        type: 'streamlit:set_widget_value', 
                        key: 'last_map_click', 
                        value: clickData
                    }}, '*');
                }}
            }});
            
            return div;
        }};
        editControl.addTo({{{{this._parent.get_name()}}}});
        {{% endmacro %}}
    ''')
    
    # Coordenadas y zoom de España
    lat_home, lon_home = 40.4637, -3.7492  # Centro de España
    zoom_home = 5.8  # Zoom para ver toda España
    
    # Crear botón personalizado con branca
    boton_centrar = MacroElement()
    boton_centrar._template = Template(f"""
        {{% macro script(this, kwargs) %}}
        var custom_button = L.control({{position: 'topright'}});
        custom_button.onAdd = function (map) {{
            var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
            div.innerHTML = '<a title="Vista general" style="background-color: white; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; cursor: pointer; text-decoration: none; border: 2px solid rgba(0,0,0,0.2); border-radius: 4px; margin-bottom: 0px; color: #333;"><i class="fa fa-home"></i></a>';
            div.onclick = function(){{
                map.flyTo([{lat_home}, {lon_home}], {zoom_home});
            }};
            return div;
        }};
        custom_button.addTo({{{{this._parent.get_name()}}}});
        {{% endmacro %}}
    """)
    
    # Añadir al mapa PRIMERO (para que quede arriba)
    m.add_child(boton_centrar)
    
    # Afegir botó de geolocalización (LocateControl) - a la dreta (DESPUÉS del home)
    if len(dff) > 0:
        # Forçar càrrega de Font Awesome 4.7 per als iconos
        font_awesome_css = folium.Element("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        """)
        m.get_root().add_child(font_awesome_css)
        
        # CSS per reduir la font dels crèdits, selector de capes i escala del mapa - només si hi ha dades
        if len(dff) > 0:
            credits_css = folium.Element("""
            <style>
            .leaflet-control-attribution {
                font-size: 10px !important;
                background-color: rgba(255,255,255,0.7) !important;
                padding: 1px 3px !important;
                line-height: 10px !important;
                height: auto !important;
            }
            .leaflet-control-attribution a {
                font-size: 10px !important;
                line-height: 10px !important;
            }
            .leaflet-control-attribution span {
                font-size: 10px !important;
                line-height: 10px !important;
            }
            .leaflet-control-attribution-prefix {
                display: none !important;
            }
            /* Reduir font del selector de capes */
            .leaflet-control-layers {
                font-size: 12px !important;
            }
            .leaflet-control-layers label {
                font-size: 12px !important;
                line-height: 12px !important;
            }
            .leaflet-control-layers input {
                transform: scale(0.8);
                margin-right: 3px;
            }
            /* Reduir font de l'escala */
            .leaflet-control-scale {
                font-size: 10px !important;
                line-height: 12px !important;
            }
            </style>
            """)
            m.get_root().header.add_child(credits_css)
    
    # Afegir Fullscreen (a l'esquerra)
    from folium.plugins import Fullscreen
    Fullscreen(position='topleft').add_to(m)
    
    # Afegir botó de geolocalización (LocateControl) - a la dreta (DESPUÉS del home)
    if len(dff) > 0:
        from folium.plugins import LocateControl
        LocateControl(
            position='topright',
            flyTo=True,
            keepCurrentZoomLevel=False,
            icon='fa fa-crosshairs',  # Prefijo doble: 'fa fa-crosshairs'
            strings={
                'title': 'Anar a la meva posició',
                'popup': 'Mostrar la meva ubicació actual'
            }
        ).add_to(m)
    
    # 4. FINALMENT afegeix el control d'edició
    # Com que és l'últim, el seu "marginTop: 150px" comptarà des del sostre del mapa
    m.add_child(edit_control)
    
    # --- CORRECCIÓN MARCADOR DE BORRADOR ---
    if new_point and isinstance(new_point, dict):
        lat = new_point.get('lat')
        lng = new_point.get('lng')
        if lat and lng:
            folium.Marker(
                location=[lat, lng],
                icon=folium.Icon(color='blue', icon='info-sign', prefix='glyphicon'),
                popup='<b>Borrador</b><br>Emplena el formulari a sota',
                tooltip='Nou accident'
            ).add_to(m)
    
    # Afegir llegenda de colors d'accidents (Ús de MacroElement per estabilitat)
    legend_macro = MacroElement()
    legend_macro._template = Template("""
        {% macro html(this, kwargs) %}
        <div id="accident-legend" style="
            position: fixed; 
            bottom: 30px; 
            right: 20px; 
            width: 140px;
            background-color: rgba(0, 0, 0, 0.7); 
            border: 4px solid rgba(155, 215, 207,0.99); 
            border-radius: 4px; 
            padding: 10px; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            font-size: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 9999;
            pointer-events: none;
        ">
            <div style="
            font-weight: bold; 
            margin-bottom: 8px; 
            color: #9bd7cf; 
            border-bottom: 1px solid rgba(155, 215, 207, 0.5); /* Línia color turquesa */
            padding-bottom: 3px;">
                Llegenda
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 12px; height: 12px; background-color: #FF0000; border-radius: 50%; margin-right: 8px; border: 0px solid black;"></div>
                <span style="color: #ffff;">Amb morts</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="width: 12px; height: 12px; background-color: #FFA500; border-radius: 50%; margin-right: 8px; border: 0px solid black;"></div>
                <span style="color: #ffff;">Amb ferits</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 12px; height: 12px; background-color: #FFFF00; border-radius: 50%; margin-right: 8px; border: 0px solid black;"></div>
                <span style="color: #ffff;">Sense danys</span>
            </div>
        </div>
        {% endmacro %}
    """)

    m.get_root().add_child(legend_macro)
    
    # Afegir capa de punts
    if show_points and len(dff) > 0:
        _add_points_layer(m, dff)
    
    # Ajustar vista si cal
    if auto_fit and len(dff) > 0:
        _fit_bounds(m, dff)
    
    return m


def _add_points_layer(m, dff):
    """
    Afegeix una capa de punts amb colors segons el grau de perill.
    """
    
    if len(dff) <= 0:
        return

    # 1. Injectem el CSS al header (estils del popup)
    style_html = """
    <style>
        .leaflet-popup-content-wrapper {
            background: rgba(0, 0, 0, 0.7) !important;
            border: 3px solid #9bd7cf !important;
            border-radius: 4px !important;
            padding: 0 !important;
        }
        .leaflet-popup-content { margin: 0 !important; padding: 0 !important; }
        .leaflet-popup-tip { background: #9bd7cf !important; }
        .popup-container {
            padding: 10px;
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 13px;
            color: #ffffff;
        }
        .popup-title {
            font-weight: 600; 
            color: #9bd7cf; 
            margin-bottom: 4px; 
            font-size: 16px;
        }
        .popup-grid { display: grid; gap: 2px; }
        .popup-label { color: #9ca3af; }
        .popup-value { color: #ffffff; }

        /* Estil per al Tooltip (el que surt al passar el cursor) */
        .leaflet-tooltip {
            font-size: 14px !important;
            font-weight: 500;
            color: #9bd7cf;
            background-color: rgba(0, 0, 0, 0.95) !important;
            border: 3px solid #9bd7cf !important;
            border-radius: 4px !important;

    </style>
    """
    m.get_root().header.add_child(folium.Element(style_html))

    # 2. Iterar sobre els punts
    for index, row in dff.iterrows():
        lat = pd.to_numeric(row.get('Latitud'), errors='coerce')
        lon = pd.to_numeric(row.get('Longitud'), errors='coerce')
        
        if pd.isna(lat) or pd.isna(lon):
            continue
        
        # --- TRACTAMENT DE DADES BUIDES SEGONS EL TEU CRITERI ---
        def get_clean_val(key, default=""):
            val = row.get(key)
            # Si és nul, NaN o la cadena "nan" (comú en pandas), retornem buit
            if pd.isna(val) or str(val).lower() == 'nan' or val is None:
                return default
            return str(val).strip()

        # Data formatada o buida
        data_valor = row.get('Data')
        if pd.notnull(data_valor) and hasattr(data_valor, 'strftime'):
            data_display = data_valor.strftime('%d/%m/%Y')
        else:
            data_display = ""

        # Altres valors categòrics
        perill = get_clean_val('Grau de perill')
        desenc = get_clean_val('Desencadenant')
        origen = get_clean_val('Origen')
        mida = get_clean_val('Mida allau')
        activitat = get_clean_val('Tipus activitat')

        # Valors numèrics (mantenim el 0 si és 0, o buit si és nul)
        def get_num_val(key):
            val = pd.to_numeric(row.get(key), errors='coerce')
            return int(val) if pd.notnull(val) else ""

        morts = get_num_val('Morts')
        ferits = get_num_val('Ferits')
        arrossegats = get_num_val('Arrossegats')

        # Lògica de colors per al punt (basada en dades numèriques)
        morts_count = int(morts) if morts != "" else 0
        ferits_count = int(ferits) if ferits != "" else 0
        
        if morts_count > 0:
            color = '#FF0000'
        elif ferits_count > 0:
            color = '#FFA500'
        else:
            color = '#FFFF00'
        
        # 3. HTML del Popup
        popup_html = f"""
        <div class="popup-container">
            <div class="popup-title">{get_clean_val('Lloc', 'Accident')}</div>
            <div class="popup-grid">
                <div><span class="popup-label">Data:</span> <span class="popup-value">{data_display}</span></div>
                <div><span class="popup-label">Perill:</span> <span class="popup-value">{perill}</span></div>
                <div><span class="popup-label">Desencadenant:</span> <span class="popup-value">{desenc}</span></div>
                <div><span class="popup-label">Origen:</span> <span class="popup-value">{origen}</span></div>
                <div><span class="popup-label">Mida allau:</span> <span class="popup-value">{mida}</span></div>
                <div><span class="popup-label">Activitat:</span> <span class="popup-value">{activitat}</span></div>
                <div><span class="popup-label">Morts:</span> <span class="popup-value">{morts}</span></div>
                <div><span class="popup-label">Ferits:</span> <span class="popup-value">{ferits}</span></div>
                <div><span class="popup-label">Arrossegats:</span> <span class="popup-value">{arrossegats}</span></div>
            </div>
        </div>
        """
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            tooltip=f"{get_clean_val('Lloc', 'Accident')} | {data_display}" # 'Accident' es mostra si no hi ha nom
        ).add_to(m)


def _fit_bounds(m, dff):
    """
    Ajusta la vista del mapa per mostrar tots els punts.
    
    Paràmetres:
    -----------
    m : folium.Map
        Mapa a ajustar
    dff : pandas.DataFrame
        Dades dels accidents
    """
    
    if len(dff) > 0:
        # Calcular límits amb robustesa
        lats = pd.to_numeric(dff['Latitud'], errors='coerce').dropna()
        lons = pd.to_numeric(dff['Longitud'], errors='coerce').dropna()
        
        # Verificar que tengamos coordenadas válidas
        if len(lats) > 0 and len(lons) > 0:
            min_lat = lats.min()
            max_lat = lats.max()
            min_lon = lons.min()
            max_lon = lons.max()
            
            # Afegir marge
            lat_margin = (max_lat - min_lat) * 0.1
            lon_margin = (max_lon - min_lon) * 0.1
            
            # Ajustar el mapa
            m.fit_bounds([
                [min_lat - lat_margin, min_lon - lon_margin],
                [max_lat + lat_margin, max_lon + lon_margin]
            ])


def get_folium_html(m):
    """
    Retorna el mapa de Folium per usar amb streamlit_folium.
    
    Paràmetres:
    -----------
    m : folium.Map
        Mapa de Folium
    
    Retorna:
    --------
    folium.Map
        Mapa de Folium per usar amb st_folium
    """
    # Retornar el mapa directament per usar amb streamlit_folium
    return m
