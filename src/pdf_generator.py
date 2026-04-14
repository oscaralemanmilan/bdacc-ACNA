import io
import datetime
import pandas as pd
from fpdf import FPDF

class AccidentPDF(FPDF):
    def header(self):
        # Logo
        try:
            self.image('assets/brand-acna-02.jpg', 15, 10, 45)  # Logo més gran (abans 30)
        except Exception:
            pass # Si falla no vull que trenqui
        
        # Arial bold 15
        self.set_font('helvetica', 'B', 16)
        # Moure costat adient apartant-se del logo (ara que el logo és més ample a 45)
        self.cell(50)
        # Títol
        self.set_text_color(0, 66, 128)
        self.cell(0, 10, "Informe d'Accident per Allau", border=0, align='C', new_x="LMARGIN", new_y="NEXT")
        
        self.set_font('helvetica', 'I', 11)
        self.cell(50)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Base de Dades d'Accidents per Allaus - ACNA", align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(16)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # helvetica italic 8
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        # Page number
        self.cell(0, 10, f'Pàgina {self.page_no()}', align='C')

def generate_accident_pdf(row_dict):
    pdf = AccidentPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Colors corporatius
    color_blau = (0, 66, 128)
    color_gris = (240, 245, 250)
    
    def section_title(title):
        pdf.set_font('helvetica', 'B', 12)
        pdf.set_fill_color(*color_blau)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, f"   {title}", fill=True, border=0, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)

    def format_value(key, val):
        if pd.isna(val) or val == "" or val is None:
            return "-"
            
        # Formatejar data
        if key == 'Data':
            if isinstance(val, str) and len(val) >= 10:
                try:
                    dt = pd.to_datetime(val[:10]) # Assegurar que agafem la part de data
                    return dt.strftime('%d/%m/%Y')
                except Exception:
                    pass
            elif isinstance(val, (pd.Timestamp, datetime.date, datetime.datetime)):
                try:
                    return val.strftime('%d/%m/%Y')
                except Exception:
                    pass
                
        # Formatejar números enters si n'hi ha (treure '.0')
        if isinstance(val, float):
            if val.is_integer():
                return str(int(val))
        elif isinstance(val, str):
            if val.endswith('.0') and val.replace('.0', '').isdigit():
                return val.replace('.0', '')
                
        return str(val)

    usable_width = pdf.epw

    def row_field(label, value, full_width=False, bold_value=False):
        width = usable_width if full_width else usable_width / 2
        
        val_str = format_value(label, value)
        val_str = val_str.encode('latin-1', 'replace').decode('latin-1')
        
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_fill_color(*color_gris)
        
        label_prop = 0.2 if full_width else 0.4
        val_prop = 0.8 if full_width else 0.6
        
        pdf.cell(width * label_prop, 8, f" {label}: ", border=1, fill=True)
        
        if bold_value:
            pdf.set_font('helvetica', 'B', 10)
        else:
            pdf.set_font('helvetica', '', 10)
            
        pdf.cell(width * val_prop, 8, f" {val_str} ", border=1)

    # SECCIÓ 1: Identificadors
    section_title("IDENTIFICACIÓ I DADES GEOGRÀFIQUES")
    
    # Lloc destacat
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_fill_color(220, 235, 250)
    pdf.set_text_color(*color_blau)
    pdf.cell(usable_width * 0.2, 10, " LLOC:", border=1, fill=True)
    pdf.set_font('helvetica', 'B', 11)
    pdf.set_text_color(0, 0, 0)
    lloc_val = format_value('Lloc', row_dict.get('Lloc', '-')).encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(usable_width * 0.8, 10, f" {lloc_val} ", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    row_field("Codi", row_dict.get('Codi', '-'))
    row_field("ID Web", row_dict.get('id', '-'))
    pdf.ln()
    
    row_field("Data", row_dict.get('Data', '-'))
    row_field("Temporada", row_dict.get('Temporada', '-'))
    pdf.ln()
    
    row_field("Latitud", row_dict.get('Latitud', '-'))
    row_field("Longitud", row_dict.get('Longitud', '-'))
    pdf.ln()

    row_field("País", row_dict.get('Pais', '-'))
    row_field("Regió", row_dict.get('Regio', '-'))
    pdf.ln()

    row_field("Serralada", row_dict.get('Serralada', '-'))
    row_field("Orientació", row_dict.get('Orientacio', '-'))
    pdf.ln()

    row_field("Altitud", row_dict.get('Altitud', '-'))
    pdf.ln(10) # Espai afegit extra abans de proper títol

    # SECCIÓ 2: Activitat i danys
    section_title("ACTIVITAT I DANYS")
    row_field("Tipus d'activitat", row_dict.get('Tipus activitat', '-'))
    row_field("Material", row_dict.get('Material', '-'))
    pdf.ln()
    
    row_field("Progressió", row_dict.get('Progressio', '-'))
    row_field("Grup", row_dict.get('Grup', '-'))
    pdf.ln()

    row_field("Sobrecàrrega", row_dict.get('Desenc', '-'))
    row_field("Arrossegats", row_dict.get('Arrossegats', '-'))
    pdf.ln()

    row_field("Ferits", row_dict.get('Ferits', '-'))
    row_field("Morts", row_dict.get('Morts', '-'))
    pdf.ln(10) # Espai afegit extra abans de proper títol

    # SECCIÓ 3: Perill i Allaus
    section_title("PERILL, NEU I ALLAUS")
    row_field("Grau perill", row_dict.get('Grau de perill', '-'))
    row_field("Origen", row_dict.get('Origen', '-'))
    pdf.ln()

    row_field("Desencadenant", row_dict.get('Desencadenant', '-'))
    row_field("Neu", row_dict.get('Neu', '-'))
    pdf.ln()

    row_field("Mida allau", row_dict.get('Mida allau', '-'))
    pdf.ln(10) # Espai afegit extra abans de proper títol

    # SECCIÓ 4: Altres
    section_title("OBSERVACIONS I ENLLAÇOS")
    
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_fill_color(*color_gris)
    pdf.cell(0, 8, " Observacions:", fill=True, border='LTR', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 10)
    obs = format_value('Observacions', row_dict.get('Observacions', '-'))
    obs = obs.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, f"{obs}", border='LBR')
    pdf.ln(6)

    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 8, " Enllaç / Font:", fill=True, border='LTR', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', '', 10)
    enllac = format_value('Link', row_dict.get('Link', '-'))
    enllac = enllac.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, f"{enllac}", border='LBR')
    pdf.ln(4)

    return bytes(pdf.output())
