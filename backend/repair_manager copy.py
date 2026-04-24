# Version 2.10 - backend/repair_manager.py (Correzione definitiva Piè di Pagina PDF)

import sqlite3
from datetime import datetime
import json
import os
import uuid 

# Importa le classi necessarie da ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import black, HexColor

class RepairManager:
    """
    Gestisce tutte le operazioni CRUD (Create, Read, Update, Delete) per le riparazioni
    e l'interazione con il database SQLite.
    """
    def __init__(self, db_path, eel_web_dir):
        self.db_path = db_path
        self.eel_web_dir = eel_web_dir 
        self.pdf_output_dir = os.path.join(self.eel_web_dir, 'generated_reports') 
        os.makedirs(self.pdf_output_dir, exist_ok=True) 
        print(f"DEBUG: PDF generati salvati in: {self.pdf_output_dir}")
        self._initialize_db()

    def _get_connection(self):
        """Restituisce una connessione al database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        return conn

    def _initialize_db(self):
        """Inizializza le tabelle del database se non esistono."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- MODIFICA QUI: Aggiunte code_2 e serial_no_2 ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repairs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repair_oa TEXT NOT NULL UNIQUE,          
                    service_ods TEXT NOT NULL,               
                    creation_date TEXT,                      
                    status TEXT DEFAULT 'Aperto',            
                    code TEXT,                               
                    serial_no TEXT,                          
                    code_2 TEXT,                             
                    serial_no_2 TEXT,                        
                    repaired_material_type TEXT,             
                    fault_found TEXT,                        
                    remarks_note TEXT,                       
                    report_date TEXT,                        
                    signature_name TEXT,                     
                    signature_name_2 TEXT                    
                );
            """)

            self._add_column_if_not_exists(cursor, 'repairs', 'code_2', 'TEXT')
            self._add_column_if_not_exists(cursor, 'repairs', 'serial_no_2', 'TEXT')

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repair_parts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repair_id INTEGER NOT NULL,
                    part_code TEXT,                          
                    description TEXT,                        
                    amount INTEGER,                          
                    position TEXT,                           
                    FOREIGN KEY (repair_id) REFERENCES repairs(id) ON DELETE CASCADE
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repair_hours (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repair_id INTEGER NOT NULL,
                    technician_name TEXT NOT NULL,           
                    hours_spent REAL NOT NULL,               
                    FOREIGN KEY (repair_id) REFERENCES repairs(id) ON DELETE CASCADE
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS repair_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repair_id INTEGER NOT NULL,
                    test_name TEXT NOT NULL,                 
                    is_checked INTEGER DEFAULT 0,            
                    notes TEXT,                              
                    FOREIGN KEY (repair_id) REFERENCES repairs(id) ON DELETE CASCADE
                );
            """)

            conn.commit()
            print("Database 'repairs' tables initialized or already exist.")
            return {"status": "success", "message": "Database initialized."}
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            return {"status": "error", "message": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()

    def _add_column_if_not_exists(self, cursor, table_name, column_name, column_type):
        """Aggiunge una colonna a una tabella se non esiste già."""
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type};")
            print(f"Added column '{column_name}' to table '{table_name}'.")


    def add_repair(self, repair_data):
        """Aggiunge un nuovo record di riparazione e i suoi dettagli correlati."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- MODIFICA QUI: Inclusi code_2 e serial_no_2 ---
            cursor.execute("""
                INSERT INTO repairs (
                    repair_oa, service_ods, creation_date, status, code, serial_no,
                    code_2, serial_no_2, repaired_material_type, fault_found, remarks_note, report_date,
                    signature_name, signature_name_2
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repair_data['repair_oa'], repair_data['service_ods'],
                datetime.now().strftime('%Y-%m-%d'), 
                repair_data.get('status', 'Aperto'), repair_data.get('code'),
                repair_data.get('serial_no'), repair_data.get('code_2'), repair_data.get('serial_no_2'),
                repair_data.get('repaired_material_type'), repair_data.get('fault_found'),
                repair_data.get('remarks_note'), repair_data.get('report_date'),
                repair_data.get('signature_name'), repair_data.get('signature_name_2')
            ))
            repair_id = cursor.lastrowid

            for part in repair_data.get('parts', []):
                if part.get('part_code') or part.get('description') or (part.get('amount') is not None) or part.get('position'): 
                    cursor.execute("""
                        INSERT INTO repair_parts (repair_id, part_code, description, amount, position)
                        VALUES (?, ?, ?, ?, ?)
                    """, (repair_id, part['part_code'], part['description'], part.get('amount', 0), part['position']))

            for hours_entry in repair_data.get('hours_spent', []):
                if hours_entry.get('technician_name') or (hours_entry.get('hours_spent') is not None): 
                    cursor.execute("""
                        INSERT INTO repair_hours (repair_id, technician_name, hours_spent)
                        VALUES (?, ?, ?)
                    """, (repair_id, hours_entry['technician_name'], hours_entry.get('hours_spent', 0.0)))

            for test in repair_data.get('tests', []):
                cursor.execute("""
                    INSERT INTO repair_tests (repair_id, test_name, is_checked, notes)
                    VALUES (?, ?, ?, ?)
                """, (repair_id, test['test_name'], test['is_checked'], test.get('notes')))

            conn.commit()
            return {"status": "success", "message": "Riparazione aggiunta con successo!", "id": repair_id}
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: repairs.repair_oa" in str(e):
                return {"status": "error", "message": f"Errore: L'Ordine di Riparazione (Repair OA) '{repair_data['repair_oa']}' esiste già."}
            return {"status": "error", "message": f"Errore di integrità del database: {e}"}
        except sqlite3.Error as e:
            return {"status": "error", "message": f"Errore database: {e}"}
        finally:
            if conn:
                conn.close()

    def get_repairs_summary(self):
        """Recupera un riassunto di tutte le riparazioni per la tabella."""
        conn = None
        repairs = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, repair_oa, service_ods, creation_date, status
                FROM repairs
                ORDER BY creation_date DESC, id DESC
            """)
            repairs = [dict(row) for row in cursor.fetchall()]
            return {"status": "success", "data": repairs}
        except sqlite3.Error as e:
            print(f"Error getting repairs summary: {e}")
            return {"status": "error", "message": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()

    def get_repair_details(self, repair_id):
        """Recupera tutti i dettagli di una singola riparazione."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM repairs WHERE id = ?", (repair_id,))
            repair = cursor.fetchone()
            if not repair:
                return {"status": "error", "message": "Riparazione non trovata."}
            repair_data = dict(repair)

            cursor.execute("SELECT part_code, description, amount, position FROM repair_parts WHERE repair_id = ?", (repair_id,))
            repair_data['parts'] = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT technician_name, hours_spent FROM repair_hours WHERE repair_id = ?", (repair_id,))
            repair_data['hours_spent'] = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT test_name, is_checked, notes FROM repair_tests WHERE repair_id = ?", (repair_id,))
            repair_data['tests'] = [dict(row) for row in cursor.fetchall()]

            return {"status": "success", "data": repair_data}
        except sqlite3.Error as e:
            print(f"Error getting repair details: {e}")
            return {"status": "error", "message": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()

    def update_repair(self, repair_id, repair_data):
        """Aggiorna un record di riparazione esistente e i suoi dettagli correlati."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- MODIFICA QUI: Inclusi code_2 e serial_no_2 nell'UPDATE ---
            cursor.execute("""
                UPDATE repairs SET
                    repair_oa = ?, service_ods = ?, status = ?,
                    code = ?, serial_no = ?, code_2 = ?, serial_no_2 = ?, 
                    repaired_material_type = ?,
                    fault_found = ?, remarks_note = ?, report_date = ?,
                    signature_name = ?, signature_name_2 = ?
                WHERE id = ?
            """, (
                repair_data['repair_oa'], repair_data['service_ods'], repair_data['status'],
                repair_data['code'], repair_data['serial_no'], repair_data['code_2'], repair_data['serial_no_2'],
                repair_data['repaired_material_type'], repair_data['fault_found'],
                repair_data['remarks_note'], repair_data['report_date'],
                repair_data['signature_name'], repair_data['signature_name_2'],
                repair_id
            ))

            cursor.execute("DELETE FROM repair_parts WHERE repair_id = ?", (repair_id,))
            for part in repair_data.get('parts', []):
                if part.get('part_code') or part.get('description') or (part.get('amount') is not None) or part.get('position'): 
                    cursor.execute("""
                        INSERT INTO repair_parts (repair_id, part_code, description, amount, position)
                        VALUES (?, ?, ?, ?, ?)
                    """, (repair_id, part['part_code'], part['description'], part.get('amount', 0), part['position']))

            cursor.execute("DELETE FROM repair_hours WHERE repair_id = ?", (repair_id,))
            for hours_entry in repair_data.get('hours_spent', []):
                if hours_entry.get('technician_name') or (hours_entry.get('hours_spent') is not None): 
                    cursor.execute("""
                        INSERT INTO repair_hours (repair_id, technician_name, hours_spent)
                        VALUES (?, ?, ?)
                    """, (repair_id, hours_entry['technician_name'], hours_entry.get('hours_spent', 0.0)))

            cursor.execute("DELETE FROM repair_tests WHERE repair_id = ?", (repair_id,))
            for test in repair_data.get('tests', []):
                cursor.execute("""
                    INSERT INTO repair_tests (repair_id, test_name, is_checked, notes)
                    VALUES (?, ?, ?, ?)
                """, (repair_id, test['test_name'], test['is_checked'], test.get('notes')))

            conn.commit()
            return {"status": "success", "message": "Riparazione aggiornata con successo!"}
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: repairs.repair_oa" in str(e):
                cursor.execute("SELECT id FROM repairs WHERE repair_oa = ?", (repair_data['repair_oa'],))
                existing_id = cursor.fetchone()
                if existing_id and existing_id['id'] != repair_id:
                     return {"status": "error", "message": f"Errore: L'Ordine di Riparazione (Repair OA) '{repair_data['repair_oa']}' esiste già per un'altra riparazione."}
                
            return {"status": "error", "message": f"Errore di integrità del database: {e}"}
        except sqlite3.Error as e:
            return {"status": "error", "message": f"Errore database: {e}"}
        finally:
            if conn:
                conn.close()

    def delete_repair(self, repair_id):
        """Elimina un record di riparazione e tutti i suoi dettagli correlati."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM repairs WHERE id = ?", (repair_id,))
            conn.commit() 
            if cursor.rowcount == 0:
                return {"status": "error", "message": "Riparazione non trovata per l'eliminazione."}
            return {"status": "success", "message": "Riparazione eliminata con successo!"}
        except sqlite3.Error as e:
            print(f"Error deleting repair: {e}")
            return {"status": "error", "message": f"Database error: {e}"}
        finally:
            if conn:
                conn.close()

    # --- MODIFICA QUI: Funzione per disegnare il piè di pagina (semplificata) ---
    def _draw_footer_on_page(self, canvas, doc):
        """Disegna il piè di pagina su ogni pagina del PDF."""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)

        # DR 0077 rev 00 (sinistra)
        canvas.drawString(doc.leftMargin, 15*mm, "DR 0077 rev 00")

        # rif PO 105 (centro)
        # doc.pagesize è una tupla (width, height)
        canvas.drawCentredString(doc.pagesize[0]/2, 15*mm, "rif PO 105")

        # page X of Y (destra)
        # getPageNumber() è il modo corretto per ReportLab per ottenere il numero di pagina corrente
        page_num = canvas.getPageNumber() 
        canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 15*mm, f"page {page_num}")
        
        canvas.restoreState()


    def generate_repair_report_pdf(self, repair_id):
        """
        Genera un report PDF per una riparazione specifica, replicando il layout
        del report allegato.
        """
        try: 
            result = self.get_repair_details(repair_id)
            if result['status'] == 'error':
                return result 

            repair_data = result['data']

            pdf_filename = f"repair_report_{repair_data['repair_oa'].replace('/', '_')}_{uuid.uuid4().hex[:8]}.pdf"
            pdf_filepath = os.path.join(self.pdf_output_dir, pdf_filename)

            doc = SimpleDocTemplate(pdf_filepath, pagesize=A4,
                                    rightMargin=10*mm, leftMargin=10*mm,
                                    topMargin=10*mm, bottomMargin=10*mm)
            
            styles = getSampleStyleSheet()
            
            styles.add(ParagraphStyle(name='SmallTextBold', fontSize=8, leading=10, alignment=TA_LEFT, fontName='Helvetica-Bold'))
            styles.add(ParagraphStyle(name='TitleStyle', fontSize=16, leading=18, alignment=TA_CENTER, fontName='Helvetica-Bold'))
            styles.add(ParagraphStyle(name='SubtitleStyle', fontSize=12, leading=14, alignment=TA_CENTER, fontName='Helvetica-Bold'))
            styles.add(ParagraphStyle(name='SectionTitle', fontSize=10, leading=12, alignment=TA_LEFT, fontName='Helvetica-Bold',
                                      spaceBefore=6, spaceAfter=3, textColor=HexColor('#00008B'))) 
            styles.add(ParagraphStyle(name='NormalText', fontSize=9, leading=11, alignment=TA_LEFT, fontName='Helvetica'))
            styles.add(ParagraphStyle(name='SmallText', fontSize=8, leading=10, alignment=TA_LEFT, fontName='Helvetica'))
            styles.add(ParagraphStyle(name='SmallTextRight', fontSize=8, leading=10, alignment=TA_RIGHT, fontName='Helvetica'))
            styles.add(ParagraphStyle(name='SmallTextCenter', fontSize=8, leading=10, alignment=TA_CENTER, fontName='Helvetica'))
            styles.add(ParagraphStyle(name='TableCaption', fontSize=9, leading=11, alignment=TA_LEFT, fontName='Helvetica-Bold', spaceAfter=3))
            styles.add(ParagraphStyle(name='TableContent', fontSize=8, leading=10, alignment=TA_LEFT, fontName='Helvetica'))
            styles.add(ParagraphStyle(name='TableContentCenter', fontSize=8, leading=10, alignment=TA_CENTER, fontName='Helvetica'))
            styles.add(ParagraphStyle(name='TableContentBold', fontSize=8, leading=10, alignment=TA_LEFT, fontName='Helvetica-Bold'))
            
            story = []

            # Logo (se hai un logo Marposs, altrimenti ometti o metti placeholder)
            # logo_path = os.path.join(self.pdf_output_dir, '..', 'logo.png') 
            # if os.path.exists(logo_path):
            #     logo = Image(logo_path, width=20*mm, height=10*mm)
            #     story.append(logo)
            #     story.append(Spacer(1, 2*mm))

            story.append(Paragraph("REPAIR REPORT", styles['TitleStyle']))
            story.append(Paragraph("RAPPORTO DI RIPARAZIONE", styles['SubtitleStyle']))
            story.append(Spacer(1, 5*mm))

            # --- Sezione Dettagli Generali (Tabella a 2 colonne, replica l'immagine) ---
            data_generale = [
                [Paragraph("Code / Codice:", styles['NormalText']), Paragraph(f"{repair_data['code'] or ''}", styles['NormalText']),Paragraph(f"{repair_data['code_2'] or ''}", styles['NormalText'])],
                # [Paragraph("Code / Codice:", styles['NormalText']), Paragraph(f"{repair_data['code'] or ''}", styles['NormalText']),
                #  Paragraph("Code / Codice:", styles['NormalText']), Paragraph(f"{repair_data['code_2'] or ''}", styles['NormalText'])],
                [Paragraph("Serial # / Matricola:", styles['NormalText']), Paragraph(f"{repair_data['serial_no'] or ''}", styles['NormalText']),Paragraph(f"{repair_data['serial_no_2'] or ''}", styles['NormalText'])],
                # [Paragraph("Serial # / Matricola:", styles['NormalText']), Paragraph(f"{repair_data['serial_no'] or ''}", styles['NormalText']),
                #  Paragraph("Serial # / Matricola:", styles['NormalText']), Paragraph(f"{repair_data['serial_no_2'] or ''}", styles['NormalText'])],
                [Paragraph("Repair OA / Ordine di riparazione:", styles['NormalText']), Paragraph(f"{repair_data['repair_oa'] or ''}", styles['NormalText']), None],
                [Paragraph("Service ODS/ Ordine di servizio:", styles['NormalText']), Paragraph(f"{repair_data['service_ods'] or ''}", styles['NormalText']), None],
            ]

            table_generale = Table(data_generale, colWidths=[50*mm, 50*mm, 50*mm]) 
            table_generale.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), HexColor('#F0F0F0')), 
                ('GRID', (0,0), (-1,-1), 0.25, black),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                ('LEFTPADDING', (0,0), (-1,-1), 2*mm),
                ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1*mm),
                ('TOPPADDING', (0,0), (-1,-1), 1*mm),
                # ('SPAN', (2,2), (3,2)), # Spanna Code/Matricola 2 per Repair OA
                # ('SPAN', (2,3), (3,3)), # Spanna Code/Matricola 2 per Service ODS
            ]))
            story.append(table_generale)
            story.append(Spacer(1, 5*mm))

            # Tipo di Riparazione (Materiale riparato / non riparabile / nessun problema)
            repaired_type = repair_data['repaired_material_type']
            repair_type_data = [
                [
                    Paragraph("Repair*<br/>Riparazione*:", styles['SmallTextBold']),
                    Paragraph("Repaired material<br/>Materiale riparato", styles['SmallText']),
                    Paragraph("X" if repaired_type == "Repaired" else "", styles['TableContentCenter']),
                    Paragraph("Non-repairable material<br/>(to be scrapped)<br/>Materiale non riparabile<br/>(da rottamare)", styles['SmallText']),
                    Paragraph("X" if repaired_type == "Non-repairable" else "", styles['TableContentCenter']),
                    Paragraph("No problem found<br/>Nessun problema rilevato", styles['SmallText']),
                    Paragraph("X" if repaired_type == "No problem found" else "", styles['TableContentCenter']),
                ]
            ]
            table_repair_type = Table(repair_type_data, colWidths=[25*mm, 40*mm, 8*mm, 40*mm, 8*mm, 40*mm, 8*mm])
            table_repair_type.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, black),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (2,0), (2,0), 'CENTER'),
                ('ALIGN', (4,0), (4,0), 'CENTER'),
                ('ALIGN', (6,0), (6,0), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 1*mm),
                ('RIGHTPADDING', (0,0), (-1,-1), 1*mm),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0.5*mm),
                ('TOPPADDING', (0,0), (-1,-1), 0.5*mm),
            ]))
            story.append(table_repair_type)
            story.append(Spacer(1, 5*mm))

            # Difetto riscontrato
            story.append(Paragraph("<b>Fault found (by the repair shop) / Difetto riscontrato (dal centro di riparazione):</b>", styles['NormalText']))
            story.append(Paragraph(f"{repair_data['fault_found'] or ''}", styles['NormalText']))
            story.append(Spacer(1, 5*mm))

            # --- Pezzi Sostituiti (Tabella) ---
            story.append(Paragraph("<b>Replaced parts / Pezzi sostituiti:</b>", styles['TableCaption']))
            parts_data = [[Paragraph("Code / Codice", styles['TableContentBold']),
                           Paragraph("Description / Descrizione", styles['TableContentBold']),
                           Paragraph("Amount / Quantità", styles['TableContentBold']),
                           Paragraph("Position** / Posizione**", styles['TableContentBold'])]]
            
            for part in repair_data['parts']:
                parts_data.append([
                    Paragraph(f"{part['part_code'] or ''}", styles['TableContent']),
                    Paragraph(f"{part['description'] or ''}", styles['TableContent']),
                    Paragraph(f"{part['amount'] if part['amount'] is not None else ''}", styles['TableContentCenter']),
                    Paragraph(f"{part['position'] or ''}", styles['TableContent'])
                ])
            
            if not repair_data['parts']:
                parts_data.append([Paragraph("", styles['TableContent']), Paragraph("", styles['TableContent']), Paragraph("", styles['TableContent']), Paragraph("", styles['TableContent'])])

            table_parts = Table(parts_data, colWidths=[35*mm, 70*mm, 25*mm, 35*mm])
            table_parts.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, black),
                ('BACKGROUND', (0,0), (-1,0), HexColor('#D3D3D3')), 
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (2,1), (2,-1), 'CENTER'), 
                ('LEFTPADDING', (0,0), (-1,-1), 2*mm),
                ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1*mm),
                ('TOPPADDING', (0,0), (-1,-1), 1*mm),
            ]))
            story.append(table_parts)
            story.append(Spacer(1, 5*mm))

            # --- Ore Impiegate (Tabella) ---
            story.append(Paragraph("<b>Hours spent / Ore impiegate:</b>", styles['TableCaption']))
            hours_data = [[Paragraph("Technician Name / Nome Tecnico", styles['TableContentBold']),
                           Paragraph("Hours / Ore", styles['TableContentBold'])]]
            
            for hours_entry in repair_data['hours_spent']:
                hours_data.append([
                    Paragraph(f"{hours_entry['technician_name'] or ''}", styles['TableContent']),
                    Paragraph(f"{hours_entry['hours_spent'] if hours_entry['hours_spent'] is not None else ''}", styles['TableContentCenter'])
                ])
            
            if not repair_data['hours_spent']:
                hours_data.append([Paragraph("", styles['TableContent']), Paragraph("", styles['TableContent'])])

            table_hours = Table(hours_data, colWidths=[105*mm, 60*mm])
            table_hours.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, black),
                ('BACKGROUND', (0,0), (-1,0), HexColor('#D3D3D3')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (1,1), (1,-1), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 2*mm),
                ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1*mm),
                ('TOPPADDING', (0,0), (-1,-1), 1*mm),
            ]))
            story.append(table_hours)
            story.append(Spacer(1, 5*mm))

            # --- Test e Verifiche (Tabella) ---
            story.append(Paragraph("<b>TESTS AND VERIFICATIONS PERFORMED *</b>", styles['TableCaption']))
            story.append(Paragraph("<b>PROVE E VERIFICHE ESEGUITE *</b>", styles['TableCaption']))
            
            test_names_map = {
                "Adjustment / Regolazione": "1. Adjustment / Regolazione",
                "Leak test / Prova di tenuta": "2. Leak test / Prova di tenuta",
                "ESACT": "3. ESACT",
                "Repeatability / Ripetibilità": "4. Repeatability / Ripetibilità",
                "Drift / Deriva": "5. Drift / Deriva",
                "Electrical test / Collaudo Elettrico": "6. Electrical test / Collaudo Elettrico",
                "Functional test / Collaudo Funzionale": "7. Functional test / Collaudo Funzionale",
                "Dynamic test / Test Dinamico": "8. Dynamic test / Test Dinamico",
                "Any other / Altri:": "9. Any other / Altri:"
            }
            
            test_results = {test['test_name']: {'checked': test['is_checked'], 'notes': test['notes']} 
                            for test in repair_data['tests']}

            tests_rows = []
            for db_name, report_name in test_names_map.items():
                checked_val = "X" if test_results.get(db_name, {}).get('checked', 0) == 1 else ""
                notes_val = test_results.get(db_name, {}).get('notes', '') if db_name == "Any other / Altri:" else ""
                
                if db_name == "Any other / Altri:":
                    tests_rows.append([
                        Paragraph(report_name, styles['TableContent']),
                        Paragraph(checked_val, styles['TableContentCenter']),
                        Paragraph(notes_val, styles['TableContent'])
                    ])
                else:
                    tests_rows.append([
                        Paragraph(report_name, styles['TableContent']),
                        Paragraph(checked_val, styles['TableContentCenter']),
                        Paragraph("", styles['TableContent']) 
                    ])
            
            table_tests = Table(tests_rows, colWidths=[80*mm, 15*mm, 70*mm]) 
            table_tests.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, black),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (1,0), (1,-1), 'CENTER'), 
                ('LEFTPADDING', (0,0), (-1,-1), 2*mm),
                ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1*mm),
                ('TOPPADDING', (0,0), (-1,-1), 1*mm),
            ]))
            story.append(table_tests)
            story.append(Spacer(1, 5*mm))


            # --- Remarks / Note ---
            story.append(Paragraph("<b>Remarks / Note:</b>", styles['TableCaption']))
            story.append(Paragraph(f"{repair_data['remarks_note'] or ''}", styles['NormalText']))
            story.append(Spacer(1, 10*mm))


            # --- Firme e Data (Seconda pagina del report) ---
            table_signatures_data = [
                [
                    Paragraph("<b>Date<br/>Data</b>", styles['SmallTextCenter']),
                    Paragraph(f"{repair_data['report_date'] or ''}", styles['NormalText']),
                    Paragraph("<b>Signature<br/>Firma</b>", styles['SmallTextCenter']),
                    Paragraph(f"{repair_data['signature_name'] or ''}<br/>{repair_data['signature_name_2'] or ''}", styles['NormalText']),
                ]
            ]
            table_signatures = Table(table_signatures_data, colWidths=[20*mm, 50*mm, 20*mm, 70*mm])
            table_signatures.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.25, black),
                ('ALIGN', (0,0), (0,0), 'CENTER'), ('ALIGN', (2,0), (2,0), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 2*mm),
                ('RIGHTPADDING', (0,0), (-1,-1), 2*mm),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1*mm),
                ('TOPPADDING', (0,0), (-1,-1), 1*mm),
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ]))
            story.append(table_signatures)
            story.append(Spacer(1, 5*mm))
            story.append(Paragraph("*Indicate with a cross / Indicare con una croce ** In case of electronic cards only / Solo in caso di schede elettroniche", styles['SmallText']))

            # --- MODIFICA QUI: Uso delle callback onFirstPage/onLaterPages direttamente ---
            doc.build(story, onFirstPage=self._draw_footer_on_page, onLaterPages=self._draw_footer_on_page)
            
            print(f"PDF generato e salvato correttamente in: {pdf_filepath}")

            relative_path_for_eel = os.path.relpath(pdf_filepath, self.eel_web_dir)
            print(f"DEBUG: Percorso relativo per Eel: /{relative_path_for_eel.replace(os.sep, '/')}")

            return {"status": "success", "message": "Report PDF generato con successo!", "filepath": f"/{relative_path_for_eel.replace(os.sep, '/')}"}

        except Exception as e:
            print(f"Error generating PDF report for repair ID {repair_id}: {e}")
            return {"status": "error", "message": f"Errore nella generazione del PDF: {e}"}