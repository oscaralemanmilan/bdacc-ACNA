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


def create_folium_map(dff, show_points=True, auto_fit=True, edit_mode=False, new_point=None):
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
    
    Retorna:
    --------
    folium.Map
        Mapa interactiu amb tots els elements configurats
    """
    
    # Centre i zoom per defecte (sempre iguals)
    center = MAP_CONFIG['default_center']
    
    # Crear mapa base fosc per defecte
    m = folium.Map(
        location=[center["lat"], center["lon"]], 
        zoom_start=5.5,  # Zoom original
        tiles=None,  # No especificar tiles per defecte
        control_scale=True,  # Reactivar escala gràfica
        control_zoom=True
    )
    
    # Afegir capes en ordre invers (Folium posa per defecte l'última capa)
    # Satèl·lit primer (quedarà a baix)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri | OpenStreetMap contributors',
        name='Satèl·lit',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='OpenTopoMap | OpenStreetMap contributors',
        name='Topogràfic',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='OpenStreetMap contributors',
        name='Standard',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        attr='CARTO | OpenStreetMap contributors',
        name='Clar',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Fosc últim (quedarà seleccionat per defecte)
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        attr='CARTO | OpenStreetMap contributors',
        name='Fosc',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Afegir control de capes (selecció única)
    folium.LayerControl().add_to(m)
    
    # Determinar estado inicial del botón
    initial_active = "true" if edit_mode else "false"
    initial_bg = "#9bd7cf" if edit_mode else "white"
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
                this.querySelector('a').style.backgroundColor = editMode ? "#9bd7cf" : "white";
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
        
        # CSS per reduir la font dels crèdits, selector de capes i escala del mapa - sempre carregat
        credits_css = folium.Element("""
        <style>
        .leaflet-control-attribution {
            font-size: 10px !important;
            background-color: rgba(255, 255, 255, 0.7) !important;
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
    
    Paràmetres:
    -----------
    m : folium.Map
        Mapa de Folium
    dff : pandas.DataFrame
        Dades dels accidents
    """
    
    if len(dff) > 0:
        for index, row in dff.iterrows():
            # Verificar que las coordenadas no sean NaN
            lat = pd.to_numeric(row.get('Latitud'), errors='coerce')
            lon = pd.to_numeric(row.get('Longitud'), errors='coerce')
            
            # Saltar si las coordenadas no son válidas
            if pd.isna(lat) or pd.isna(lon):
                continue
            
            # Color segons víctimes (no segons grau de perill)
            morts_value = pd.to_numeric(row.get('Morts', 0), errors='coerce')
            ferits_value = pd.to_numeric(row.get('Ferits', 0), errors='coerce')
            arrossegats_value = pd.to_numeric(row.get('Arrossegats', 0), errors='coerce')
            
            morts = 0 if pd.isna(morts_value) else int(morts_value)
            ferits = 0 if pd.isna(ferits_value) else int(ferits_value)
            arrossegats = 0 if pd.isna(arrossegats_value) else int(arrossegats_value)
            
            if morts > 0:
                color = '#FF0000'  # Rojo si hay al menos un muerto
            elif ferits > 0:
                color = '#FFA500'  # Naranja si hay heridos pero no muertos
            else:
                color = '#FFFF00'  # Amarillo si no hay muertos ni heridos
            
            # Mida fixa per a tots els punts
            radius = 5
            
            # Tooltip simple i directe amb tota la informació (estils personalitzats)
            tooltip_text = f"""

            <style>

            .leaflet-popup-content-wrapper {{

                background: rgba(0, 0, 0, 0.6) !important; /* Fons fosc amb transparència */

                border: 5px solid #9bd7cf !important;

                border-radius:4px !important;

                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;

                padding: 0 !important;

            }}

            .leaflet-popup-content {{

                margin: 0 !important;

                padding: 0 !important;

                background: transparent !important;

            }}

            .leaflet-popup-tip {{

                background: #9bd7cf !important;

                border-top: 2px solid #263042 !important;

                border-right: 2px solid #263042 !important;

            }}

            </style>

            <div style="background: rgba(0, 0, 0, 0.6); /* Fons fosc amb transparència */

            border: 2px solid #263042;

            border-radius: 2px;

            padding: 10px;

            margin: 0;

            font-family: system-ui, -apple-system, sans-serif;

            font-size: 13px;

            color: #ffffff;">

                <div style="font-weight: 600; color: #9bd7cf; margin-bottom: 4px; font-size: 16px;">

                    {row.get('Lloc', 'Desconegut')}

                </div>

                <div style="display: grid; gap: 2px; margin-bottom: 0;">

                    <div><span style="color: #9ca3af;">Data:</span> <span style="color: #ffffff;">{row.get('Data_str', 'Desconeguda')}</span></div>

                    <div><span style="color: #9ca3af;">Perill:</span> <span style="color: #ffffff;">{row.get('Grau de perill', '1')}</span></div>

                    <div><span style="color: #9ca3af;">Desencadenant:</span> <span style="color: #ffffff;">{row.get('Desencadenant', 'Desconegut')}</span></div>

                    <div><span style="color: #9ca3af;">Origen:</span> <span style="color: #ffffff;">{row.get('Origen', 'Desconegut')}</span></div>

                    <div><span style="color: #9ca3af;">Mida allau:</span> <span style="color: #ffffff;">{row.get('Mida allau', 'Desconegut')}</span></div>

                    <div><span style="color: #9ca3af;">Activitat:</span> <span style="color: #ffffff;">{row.get('Tipus activitat', 'Desconegut')}</span></div>

                    <div><span style="color: #9ca3af;">Morts:</span> <span style="color: #ffffff;">{morts}</span></div>

                    <div><span style="color: #9ca3af;">Ferits:</span> <span style="color: #ffffff;">{ferits}</span></div>

                    <div><span style="color: #9ca3af;">Arrossegats:</span> <span style="color: #ffffff;">{arrossegats}</span></div>

                </div>

            </div>
            """
            
            # Crear marcador
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=folium.Popup(tooltip_text, max_width=300),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                tooltip=f"{row.get('Lloc', 'Desconegut')}"
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
