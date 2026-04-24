# Version 3.1 - backend/repair_manager.py (Integrazione WeasyPrint per PDF)

import sqlite3
from datetime import datetime
import json
import os
import uuid 

# Rimosse le importazioni di ReportLab
# from reportlab.lib.pagesizes import A4
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.units import mm
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
# from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
# from reportlab.lib.colors import black, HexColor

# Importa WeasyPrint
from weasyprint import HTML, CSS

# Importa Jinja2 per il templating
from jinja2 import Environment, FileSystemLoader

class RepairManager:
    """
    Gestisce tutte le operazioni CRUD (Create, Read, Update, Delete) per le riparazioni
    e l'interazione con il database SQLite.
    """
    def __init__(self, db_path, eel_web_dir):
        self.db_path = db_path
        self.eel_web_dir = eel_web_dir 
        self.pdf_output_dir = os.path.join(self.eel_web_dir, 'generated_reports') 
        # La cartella dei template HTML per i report (non più RML)
        self.report_template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app_data', 'report_templates')
        
        os.makedirs(self.pdf_output_dir, exist_ok=True) 
        os.makedirs(self.report_template_dir, exist_ok=True) # Assicura che la cartella dei template esista
        
        print(f"DEBUG: PDF generati salvati in: {self.pdf_output_dir}")
        print(f"DEBUG: Template HTML report caricati da: {self.report_template_dir}")
        self._initialize_db()

        # Inizializza l'ambiente Jinja2
        self.jinja_env = Environment(loader=FileSystemLoader(self.report_template_dir))
        self.report_template = self.jinja_env.get_template('repair_report.html')
        print(f"DEBUG: Template Jinja2 'repair_report.html' caricato.")


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
                    repair_oa_2 TEXT,                        
                    service_ods_2 TEXT,                      
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
            self._add_column_if_not_exists(cursor, 'repairs', 'repair_oa_2', 'TEXT') 
            self._add_column_if_not_exists(cursor, 'repairs', 'service_ods_2', 'TEXT') 

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

            cursor.execute("""
                INSERT INTO repairs (
                    repair_oa, service_ods, creation_date, status, code, serial_no,
                    code_2, serial_no_2, repair_oa_2, service_ods_2, repaired_material_type, fault_found, remarks_note, report_date,
                    signature_name, signature_name_2
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                repair_data['repair_oa'], repair_data['service_ods'],
                datetime.now().strftime('%Y-%m-%d'), 
                repair_data.get('status', 'Aperto'), repair_data.get('code'),
                repair_data.get('serial_no'), repair_data.get('code_2'), repair_data.get('serial_no_2'),
                repair_data.get('repair_oa_2'), repair_data.get('service_ods_2'), 
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

            cursor.execute("""
                UPDATE repairs SET
                    repair_oa = ?, service_ods = ?, status = ?,
                    code = ?, serial_no = ?, code_2 = ?, serial_no_2 = ?, 
                    repair_oa_2 = ?, service_ods_2 = ?, repaired_material_type = ?,
                    fault_found = ?, remarks_note = ?, report_date = ?,
                    signature_name = ?, signature_name_2 = ?
                WHERE id = ?
            """, (
                repair_data['repair_oa'], repair_data['service_ods'], repair_data['status'],
                repair_data['code'], repair_data['serial_no'], repair_data['code_2'], repair_data['serial_no_2'],
                repair_data['repair_oa_2'], repair_data['service_ods_2'], 
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

    def generate_repair_report_pdf(self, repair_id):
        """
        Genera un report PDF per una riparazione specifica, utilizzando un template HTML/CSS e WeasyPrint.
        """
        try: 
            result = self.get_repair_details(repair_id)
            if result['status'] == 'error':
                return result 

            repair_data = result['data']

            pdf_filename = f"repair_report_{repair_data['repair_oa'].replace('/', '_')}_{uuid.uuid4().hex[:8]}.pdf"
            pdf_filepath = os.path.join(self.pdf_output_dir, pdf_filename)
            
            # --- Prepara il contesto dati per Jinja2 ---
            context = {
                'code': repair_data['code'] or '',
                'serial_no': repair_data['serial_no'] or '',
                'code_2': repair_data['code_2'] or '',
                'serial_no_2': repair_data['serial_no_2'] or '',
                'repair_oa': repair_data['repair_oa'] or '',
                'service_ods': repair_data['service_ods'] or '',
                'repair_oa_2': repair_data['repair_oa_2'] or '',
                'service_ods_2': repair_data['service_ods_2'] or '',
                'status': repair_data['status'] or '',

                'repaired_material_checked': 'X' if repair_data['repaired_material_type'] == 'Repaired' else '',
                'non_repairable_material_checked': 'X' if repair_data['repaired_material_type'] == 'Non-repairable' else '',
                'no_problem_found_checked': 'X' if repair_data['repaired_material_type'] == 'No problem found' else '',
                
                'fault_found': repair_data['fault_found'] or '',
                'remarks_note': repair_data['remarks_note'] or '',
                
                'parts': repair_data['parts'], # Array di dict, i nomi delle chiavi sono già compatibili con il template HTML
                'hours': [{'name': h['technician_name'], 'hours': h['hours_spent']} 
                          for h in repair_data['hours_spent']], # Adatta i nomi delle chiavi per il template
                'tests_formatted': [], # Da popolare e formattare

                'report_date': repair_data['report_date'] or '',
                'signature_name': repair_data['signature_name'] or '',
                'signature_name_2': repair_data['signature_name_2'] or '',
            }

            # Formatta i test per il template HTML
            test_names_map_for_template = { 
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
            db_test_results = {test['test_name']: {'checked': test['is_checked'], 'notes': test['notes']} 
                                for test in repair_data['tests']}

            for db_name, report_name in test_names_map_for_template.items():
                checked_val = "X" if db_test_results.get(db_name, {}).get('checked', 0) == 1 else ""
                notes_val = db_test_results.get(db_name, {}).get('notes', '') if db_name == "Any other / Altri:" else ""
                context['tests_formatted'].append({
                    'test_name': report_name,
                    'checked': checked_val,
                    'notes': notes_val
                })
            
            # 4. Renderizza il template HTML con il contesto dati
            rendered_html = self.report_template.render(context)
            
            # 5. Converte l'HTML renderizzato in PDF usando WeasyPrint
            HTML(string=rendered_html, base_url=self.report_template_dir).write_pdf(pdf_filepath)
            
            print(f"PDF generato e salvato correttamente in: {pdf_filepath}")

            relative_path_for_eel = os.path.relpath(pdf_filepath, self.eel_web_dir)
            print(f"DEBUG: Percorso relativo per Eel: /{relative_path_for_eel.replace(os.sep, '/')}")

            return {"status": "success", "message": "Report PDF generato con successo!", "filepath": f"/{relative_path_for_eel.replace(os.sep, '/')}"}

        except Exception as e:
            print(f"Error generating PDF report for repair ID {repair_id}: {e}")
            return {"status": "error", "message": f"Errore nella generazione del PDF: {e}"}