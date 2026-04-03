"""
Mòdul de Processament de Dades per a BDACC ACNA
================================================

Funcionalitat:
- Càrrega de dades des de diferents fonts (Excel, Google Sheets)
- Neteja i estandardització de dades
- Aplicació de filtres
- Validació de coordenades i dates

Autor: Òscar Alemán-Milán © 2026
"""

import os
import pandas as pd
import streamlit as st
import re

# Variables globals per a l'anàlisi de composició
VARS_PERCENT = [
    "Grau de perill", "Desencadenant", "Origen", "Orientacio", 
    "Mida allau", "Tipus activitat", "Pais", "Regio", "Serralada", "Altitud"
]

# Columnes categòriques que necessiten neteja
CAT_COLS = [
    "Temporada","Tipus activitat","Pais","Regio","Serralada","Orientacio",
    "Origen","Progressio","Desencadenant","Material","Altitud",
    "Grau de perill","Mes","Mida allau"
]

# Columnes numèriques que s'han de convertir a enters
NUMERIC_COLS = ["Morts","Ferits","Arrossegats"]

# Mapa de mesos en català
MESOS_CAT = {
    1:"Gener",2:"Febrer",3:"Març",4:"Abril",5:"Maig",6:"Juny",
    7:"Juliol",8:"Agost",9:"Setembre",10:"Octubre",11:"Novembre",12:"Desembre"
}

# Límits geogràfics per a la Península Ibèrica
GEO_BOUNDS = {
    "lat_min": 30, "lat_max": 50,
    "lon_min": -10, "lon_max": 10
}


@st.cache_data
def process_data(df):
    """
    Neteja i estandardització de les dades d'accidents d'allaus.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame original amb les dades brutes
    
    Retorna:
    --------
    pandas.DataFrame
        DataFrame net i estandarditzat
    
    Transformacions realitzades:
    ---------------------------
    1. Neteja de noms de columnes (elimina espais)
    2. Conversió de coordenades (coma → punt decimal)
    3. Filtratge geogràfic (Península Ibèrica)
    4. Normalització de dates (dd/mm/yyyy prioritari)
    5. Creació de columnes auxiliars (Data_str, Any, Mes)
    6. Conversió de columnes numèriques a enters
    7. Estandardització de valors categòrics buits
    """
    
    # 1. Neteja de noms de columnes
    df.columns = df.columns.str.strip()
    
    # 2. Conversió de coordenades a numèric
    for col in ["Latitud", "Longitud"]:
        df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # 3. Filtratge geogràfic - Península Ibèrica
    df = df.dropna(subset=["Latitud","Longitud"])
    df = df[(df["Latitud"] > GEO_BOUNDS["lat_min"]) & 
            (df["Latitud"] < GEO_BOUNDS["lat_max"])]
    df = df[(df["Longitud"] > GEO_BOUNDS["lon_min"]) & 
            (df["Longitud"] < GEO_BOUNDS["lon_max"])]
    
    # 4. Normalització de dates
    raw = df["Data"].astype(str)
    # Primer intenta dia/mes/any (format europeu)
    d1 = pd.to_datetime(raw, errors="coerce", dayfirst=True)
    # Per a les que fallen, intenta mes/dia/any (format americà)
    mask = d1.isna()
    d2 = pd.to_datetime(raw[mask], errors="coerce", dayfirst=False)
    d1.loc[mask] = d2
    df["Data"] = d1
    
    # 5. Columnes auxiliars per a dates
    df["Data_str"] = df["Data"].dt.strftime("%d/%m/%Y").fillna("Desconegut")
    df["Any"] = df["Data"].dt.year
    df["Mes"] = df["Data"].dt.month.map(MESOS_CAT)
    df["Accidents"] = 1  # Cada fila és un accident
    
    # 6. Conversió de columnes numèriques a enters
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    
    # 7. Estandardització de categories buides
    for col in CAT_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan":"Desconegut","None":"Desconegut","": "Desconegut"})
    
    return df


@st.cache_data
def load_data(file_path="data/bd_accidents_200726_net_c.xlsx"):
    """
    Carrega dades des d'un fitxer Excel local.
    
    Paràmetres:
    -----------
    file_path : str o UploadedFile
        Ruta al fitxer Excel o objecte de fitxer pujat
    
    Retorna:
    --------
    pandas.DataFrame
        Dades processades i netejades
    """
    if isinstance(file_path, str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Fitxer no trobat: {file_path}")
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        # Fitxer pujat mitjançant Streamlit
        df = pd.read_excel(file_path, engine="openpyxl")
    
    return process_data(df)


@st.cache_data
def load_from_gsheet(url):
    """
    Carrega dades des d'un Google Sheet públic.
    
    Paràmetres:
    -----------
    url : str
        URL del Google Sheet compartit
    
    Retorna:
    --------
    pandas.DataFrame
        Dades processades i netejades
    
    Notes:
    ------
    - El Google Sheet ha de ser públic o compartir-se amb 'qualsevol amb l'enllaç'
    - Es converteix a CSV automàticament
    """
    # Extreu l'ID del full de càlcul de l'URL
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    if not match:
        raise ValueError("Enllaç invàlid. Assegura't que sigui un enllaç compartit de Google Sheets.")
    
    sheet_id = match.group(1)
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    df = pd.read_csv(csv_url)
    return process_data(df)


def apply_filters(df, filters_dict, metrica="Accidents"):
    """
    Aplica filtres a les dades segons els criteris seleccionats.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame original
    filters_dict : dict
        Diccionari amb {columna: [valors_seleccionats]}
    metrica : str
        Mètrica principal (Accidents, Morts, Ferits, Arrossegats)
    
    Retorna:
    --------
    pandas.DataFrame
        DataFrame filtrat
    """
    # Còpia per no modificar l'original
    dff = df.copy()
    
    # Filtra per mètrica (només files amb valors > 0)
    if metrica != "Accidents":
        if metrica in dff.columns:
            dff = dff[dff[metrica] > 0]
        else:
            # Si no existeix la columna, retorna DataFrame buit
            dff = dff.iloc[0:0]
    
    # Aplica filtres categòrics
    for col, vals in filters_dict.items():
        if vals and col in dff.columns:
            dff = dff[dff[col].isin(vals)]
    
    # Assegura que hi hagi coordenades vàlides
    if "Latitud" in dff.columns and "Longitud" in dff.columns:
        dff = dff.dropna(subset=["Latitud","Longitud"])
    
    return dff


def get_column_options(df, column_name):
    """
    Obté les opcions úniques i ordenades per a una columna categòrica.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame amb les dades
    column_name : str
        Nom de la columna
    
    Retorna:
    --------
    list
        Llista d'opcions ordenades (Desconegut al final)
    """
    if df is None or column_name not in df.columns:
        return []
    
    s = df[column_name].dropna().astype(str).str.strip()
    s = s.replace({"nan":"Desconegut","None":"Desconegut","": "Desconegut"})
    
    # Ordena posant "Desconegut" al final
    return sorted(s.unique().tolist(), key=lambda x: (x=="Desconegut", x.lower()))


def validate_data_structure(df):
    """
    Valida que el DataFrame tingui l'estructura esperada.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame a validar
    
    Retorna:
    --------
    tuple
        (es_valid, missatges_error)
    """
    errors = []
    
    # Columnes obligatòries
    required_cols = ["Data", "Latitud", "Longitud"]
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Falta la columna obligatòria: {col}")
    
    # Comprova que hi hagi dades
    if df.empty:
        errors.append("El DataFrame està buit")
    
    return len(errors) == 0, errors
