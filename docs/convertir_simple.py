#!/usr/bin/env python3
"""
Script simple para convertir archivos Markdown a PDF usando markdown2pdf
"""

import os
from datetime import datetime

def convertir_md_a_pdf():
    """Convierte los archivos MD a PDF usando una alternativa simple"""
    
    # Ruta de los archivos
    docs_dir = r"e:\OneDrive - UAB\APPs_dev\bdacc-ACNA\docs"
    
    # Archivos a convertir
    archivos = [
        "guia-arquitectura-2026-04-09.md",
        "bdacc-acna-codebase-2026-04-09.md"
    ]
    
    print("🔄 Intentando convertir archivos Markdown a PDF...")
    print("=" * 60)
    
    for archivo in archivos:
        md_path = os.path.join(docs_dir, archivo)
        pdf_path = os.path.join(docs_dir, archivo.replace('.md', '.pdf'))
        
        if os.path.exists(md_path):
            print(f"\n📄 Procesando: {archivo}")
            print(f"📂 Origen: {md_path}")
            print(f"📂 Destino: {pdf_path}")
            
            try:
                # Intentar convertir usando pandoc si está disponible
                import subprocess
                result = subprocess.run([
                    'pandoc', 
                    md_path, 
                    '-o', pdf_path,
                    '--pdf-engine=xelatex',
                    '-V', 'geometry:margin=1in',
                    '-V', 'fontsize=12pt'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ PDF generado exitosamente: {os.path.basename(pdf_path)}")
                else:
                    print(f"❌ Error con pandoc: {result.stderr}")
                    print("💡 Sugerencia: Instala pandoc o usa una herramienta online")
                    
            except FileNotFoundError:
                print("❌ Pandoc no encontrado")
                print("💡 Para instalar Pandoc:")
                print("   - Windows: https://pandoc.org/installing.html")
                print("   - O con conda: conda install -c conda-forge pandoc")
                
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
        else:
            print(f"❌ No se encontró el archivo: {md_path}")
    
    print("\n" + "=" * 60)
    print("🎉 Proceso finalizado")
    print("\n📋 Alternativas si no funcionó:")
    print("1. Instala Pandoc: https://pandoc.org/installing.html")
    print("2. Usa herramientas online como:")
    print("   - https://markdown2pdf.com")
    print("   - https://dillinger.io")
    print("3. Abre el archivo en VS Code y usa Imprimir > Guardar como PDF")

if __name__ == "__main__":
    convertir_md_a_pdf()
