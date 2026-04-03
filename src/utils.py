"""
Mòdul d'Utilitats per a BDACC ACNA
===================================

Funcionalitat:
- Funcions auxiliars generals
- Validacions
- Utilitats de format i conversió

Autor: Òscar Alemán-Milán © 2026
"""

import pandas as pd
import re
from typing import List, Dict, Any, Optional, Tuple


def clean_column_names(df):
    """
    Neteja els noms de columnes d'un DataFrame.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame amb noms de columnes a netejar
    
    Retorna:
    --------
    pandas.DataFrame
        DataFrame amb noms de columnes netejats
    """
    df.columns = df.columns.str.strip()
    return df


def validate_coordinates(lat, lon):
    """
    Valida si unes coordenades dins dels límits de la Península Ibèrica.
    
    Paràmetres:
    -----------
    lat : float
        Latitud
    lon : float
        Longitud
    
    Retorna:
    --------
    bool
        True si les coordenades són vàlides
    """
    try:
        lat = float(lat)
        lon = float(lon)
        return (30 <= lat <= 50) and (-10 <= lon <= 10)
    except (ValueError, TypeError):
        return False


def extract_google_sheet_id(url):
    """
    Extreu l'ID d'un Google Sheet de la seva URL.
    
    Paràmetres:
    -----------
    url : str
        URL del Google Sheet
    
    Retorna:
    --------
    str or None
        ID del full de càlcul o None si no és vàlid
    """
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None


def normalize_categorical_values(series, unknown_value="Desconegut"):
    """
    Normalitza els valors categòrics d'una sèrie.
    
    Paràmetres:
    -----------
    series : pandas.Series
        Sèrie amb valors categòrics
    unknown_value : str
        Valor a usar per a dades buides/invàlides
    
    Retorna:
    --------
    pandas.Series
        Sèrie normalitzada
    """
    s = series.astype(str).str.strip()
    s = s.replace({"nan": unknown_value, "None": unknown_value, "": unknown_value})
    return s


def safe_numeric_conversion(series, default_value=0):
    """
    Converteix una sèrie a numèrica de forma segura.
    
    Paràmetres:
    -----------
    series : pandas.Series
        Sèrie a convertir
    default_value : int or float
        Valor per defecte per a valors invàlids
    
    Retorna:
    --------
    pandas.Series
        Sèrie convertida a numèrica
    """
    return pd.to_numeric(series, errors="coerce").fillna(default_value)


def format_number(value, decimal_places=1):
    """
    Formateja un número per a la seva visualització.
    
    Paràmetres:
    -----------
    value : float or int
        Valor a formatejar
    decimal_places : int
        Nombre de decimals
    
    Retorna:
    --------
    str
        Número formatejat
    """
    if pd.isna(value):
        return "N/A"
    
    if isinstance(value, (int, float)):
        return f"{value:.{decimal_places}f}"
    
    return str(value)


def calculate_percentage(numerator, denominator, decimal_places=1):
    """
    Calcula un percentatge de forma segura.
    
    Paràmetres:
    -----------
    numerator : float or int
        Numerador
    denominator : float or int
        Denominador
    decimal_places : int
        Nombre de decimals
    
    Retorna:
    --------
    float
        Percentatge calculat
    """
    if denominator == 0 or pd.isna(denominator):
        return 0.0
    
    try:
        return (numerator / denominator * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def validate_dataframe_structure(df, required_columns=None):
    """
    Valida l'estructura bàsica d'un DataFrame.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame a validar
    required_columns : list
        Llista de columnes obligatòries
    
    Retorna:
    --------
    tuple
        (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # Comprova que no sigui buit
    if df.empty:
        errors.append("El DataFrame està buit")
        return False, errors, warnings
    
    # Comprova columnes obligatòries
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            errors.append(f"Falten columnes obligatòries: {', '.join(missing_cols)}")
    
    # Comprova duplicats
    if df.duplicated().any():
        warnings.append(f"Hi ha {df.duplicated().sum()} files duplicades")
    
    return len(errors) == 0, errors, warnings


def get_data_summary(df):
    """
    Obté un resum estadístic de les dades.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame a analitzar
    
    Retorna:
    --------
    dict
        Diccionari amb estadístiques bàsiques
    """
    if df.empty:
        return {}
    
    summary = {
        'total_records': len(df),
        'columns': list(df.columns),
        'numeric_columns': list(df.select_dtypes(include=['number']).columns),
        'categorical_columns': list(df.select_dtypes(include=['object']).columns),
        'missing_values': df.isnull().sum().to_dict(),
        'memory_usage': df.memory_usage(deep=True).sum()
    }
    
    # Estadístiques per columnes numèriques
    if summary['numeric_columns']:
        summary['numeric_stats'] = df[summary['numeric_columns']].describe().to_dict()
    
    return summary


def create_safe_filename(filename):
    """
    Crea un nom de fitxer segur eliminant caràcters problemàtics.
    
    Paràmetres:
    -----------
    filename : str
        Nom de fitxer original
    
    Retorna:
    --------
    str
        Nom de fitxer segur
    """
    # Elimina caràcters no desitjats
    safe_name = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Reemplaça espais amb guions baixos
    safe_name = safe_name.replace(' ', '_')
    # Elimina caràcters múltiples
    safe_name = re.sub(r'_+', '_', safe_name)
    # Elimina guions baixos al principi/final
    safe_name = safe_name.strip('_')
    
    return safe_name or "unnamed"


def filter_dataframe_by_bounds(df, lat_col="Latitud", lon_col="Longitud", 
                              lat_min=30, lat_max=50, lon_min=-10, lon_max=10):
    """
    Filtra un DataFrame per límits geogràfics.
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame a filtrar
    lat_col, lon_col : str
        Noms de les columnes de coordenades
    lat_min, lat_max, lon_min, lon_max : float
        Límits geogràfics
    
    Retorna:
    --------
    pandas.DataFrame
        DataFrame filtrat
    """
    if lat_col not in df.columns or lon_col not in df.columns:
        return df
    
    # Converteix a numèric si cal
    df_copy = df.copy()
    df_copy[lat_col] = pd.to_numeric(df_copy[lat_col], errors='coerce')
    df_copy[lon_col] = pd.to_numeric(df_copy[lon_col], errors='coerce')
    
    # Aplica filtres
    mask = (
        (df_copy[lat_col] >= lat_min) & 
        (df_copy[lat_col] <= lat_max) &
        (df_copy[lon_col] >= lon_min) & 
        (df_copy[lon_col] <= lon_max)
    )
    
    return df_copy[mask]


def create_date_parser():
    """
    Crea una funció per parsejar dates en múltiples formats.
    
    Retorna:
    --------
    function
        Funció que parseja dates intentant diversos formats
    """
    def parse_dates(date_series):
        """
        Parseja dates intentant dd/mm/yyyy primer, després mm/dd/yyyy.
        
        Paràmetres:
        -----------
        date_series : pandas.Series
            Sèrie de dates en format text
        
        Retorna:
        --------
        pandas.Series
            Sèrie de dates parsejades
        """
        raw = date_series.astype(str)
        
        # Primer intenta dia/mes/any (format europeu)
        d1 = pd.to_datetime(raw, errors="coerce", dayfirst=True)
        
        # Per a les que fallen, intenta mes/dia/any (format americà)
        mask = d1.isna()
        d2 = pd.to_datetime(raw[mask], errors="coerce", dayfirst=False)
        d1.loc[mask] = d2
        
        return d1
    
    return parse_dates


def log_data_operation(operation, details):
    """
    Registra una operació de dades (útil per a debugging).
    
    Paràmetres:
    -----------
    operation : str
        Tipus d'operació
    details : dict
        Detalls de l'operació
    """
    print(f"[{operation}] {details}")


# Alias per compatibilitat amb el codi original
opts = lambda df, col: get_column_options(df, col)

def get_column_options(df, column_name):
    """
    Obté opcions úniques i ordenades per a una columna.
    (Funció adaptada del codi original)
    
    Paràmetres:
    -----------
    df : pandas.DataFrame
        DataFrame amb les dades
    column_name : str
        Nom de la columna
    
    Retorna:
    --------
    list
        Llista d'opcions ordenades
    """
    if df is None or column_name not in df.columns:
        return []
    
    s = df[column_name].dropna().astype(str).str.strip()
    s = s.replace({"nan":"Desconegut","None":"Desconegut","": "Desconegut"})
    
    return sorted(s.unique().tolist(), key=lambda x: (x=="Desconegut", x.lower()))
