#!/usr/bin/env python3
"""
Script para convertir archivos Markdown a PDF
Requiere: pip install markdown pdfkit wkhtmltopdf
"""

import os
import markdown
import pdfkit
from datetime import datetime

def md_to_pdf(md_file_path, output_dir=None):
    """
    Convierte un archivo Markdown a PDF
    
    Args:
        md_file_path (str): Ruta al archivo Markdown
        output_dir (str): Directorio de salida (opcional)
    """
    if output_dir is None:
        output_dir = os.path.dirname(md_file_path)
    
    # Leer archivo Markdown
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convertir Markdown a HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'codehilite', 'toc']
    )
    
    # Agregar estilos CSS
    css_styles = """
    <style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
        margin-top: 30px;
        margin-bottom: 15px;
    }
    h1 { font-size: 28px; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { font-size: 24px; border-bottom: 1px solid #bdc3c7; padding-bottom: 8px; }
    h3 { font-size: 20px; }
    code {
        background-color: #f8f9fa;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
    }
    pre {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        overflow-x: auto;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 12px;
        text-align: left;
    }
    th {
        background-color: #3498db;
        color: white;
        font-weight: bold;
    }
    ul, ol {
        margin: 15px 0;
        padding-left: 30px;
    }
    li {
        margin: 5px 0;
    }
    blockquote {
        border-left: 4px solid #3498db;
        margin: 20px 0;
        padding: 10px 20px;
        background-color: #f8f9fa;
        font-style: italic;
    }
    </style>
    """
    
    # Crear HTML completo
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{os.path.basename(md_file_path)}</title>
        {css_styles}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Generar nombre de archivo PDF
    base_name = os.path.splitext(os.path.basename(md_file_path))[0]
    pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
    
    # Configuración de PDF
    options = {
        'page-size': 'A4',
        'margin-top': '1cm',
        'margin-right': '1cm',
        'margin-bottom': '1cm',
        'margin-left': '1cm',
        'encoding': "UTF-8",
        'no-outline': None,
        'enable-local-file-access': None
    }
    
    try:
        # Convertir HTML a PDF
        pdfkit.from_string(html_template, pdf_path, options=options)
        print(f"✅ PDF generado exitosamente: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"❌ Error al generar PDF: {e}")
        return None

def main():
    """Función principal para convertir los archivos específicos"""
    docs_dir = "e:/OneDrive - UAB/APPs_dev/bdacc-ACNA/docs"
    
    # Archivos a convertir
    archivos = [
        "guia-arquitectura-2026-04-09.md",
        "bdacc-acna-codebase-2026-04-09.md"
    ]
    
    print("🔄 Iniciando conversión de archivos Markdown a PDF...")
    print("=" * 50)
    
    for archivo in archivos:
        md_path = os.path.join(docs_dir, archivo)
        if os.path.exists(md_path):
            print(f"\n📄 Procesando: {archivo}")
            resultado = md_to_pdf(md_path, docs_dir)
            if resultado:
                print(f"✅ Guardado como: {os.path.basename(resultado)}")
            else:
                print(f"❌ Falló la conversión de: {archivo}")
        else:
            print(f"❌ No se encontró el archivo: {md_path}")
    
    print("\n" + "=" * 50)
    print("🎉 Proceso de conversión finalizado")

if __name__ == "__main__":
    main()
