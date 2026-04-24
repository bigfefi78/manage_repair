# Version 2.5 - main.py (Passaggio EEL_WEB_DIR)

import eel
import os
import sys
from backend import RepairManager

# --- CONFIGURAZIONE PERCORSI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EEL_WEB_DIR = os.path.join(BASE_DIR, 'web')
APP_DATA_DIR = os.path.join(BASE_DIR, 'app_data')
DATABASE_PATH = os.path.join(APP_DATA_DIR, 'production_db.sqlite')

# --- INIZIALIZZAZIONE BACKEND (RepairManager) ---
# AGGIUNTA: Passiamo EEL_WEB_DIR al RepairManager
repair_manager = RepairManager(DATABASE_PATH, EEL_WEB_DIR)

# --- FUNZIONI PYTHON ESPOSTE A JAVASCRIPT ---
@eel.expose
def init_db_backend():
    """Espone la funzione di inizializzazione DB del RepairManager al frontend."""
    return repair_manager._initialize_db()

@eel.expose
def add_repair(repair_data):
    return repair_manager.add_repair(repair_data)

@eel.expose
def get_repairs_summary():
    return repair_manager.get_repairs_summary()

@eel.expose
def get_repair_details(repair_id):
    return repair_manager.get_repair_details(repair_id)

@eel.expose
def update_repair(repair_id, repair_data):
    return repair_manager.update_repair(repair_id, repair_data)

@eel.expose
def delete_repair(repair_id):
    return repair_manager.delete_repair(repair_id)

@eel.expose
def generate_repair_report_pdf(repair_id):
    return repair_manager.generate_repair_report_pdf(repair_id)

# --- FUNZIONE DI AVVIO EEL ---
def start_eel_app(page_to_serve='main.html'):
    """
    Avvia l'applicazione Eel, configurando l'host, la porta e altre opzioni.
    page_to_serve: Il nome del file HTML da servire come pagina iniziale.
    """
    eel.init(EEL_WEB_DIR)
    print(f"Avvio dell'applicazione Eel da '{EEL_WEB_DIR}' servendo '{page_to_serve}'")

    # Assicuriamo che la directory 'app_data' esista per il database
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    print(f"Verificata/Creata la directory per i dati dell'applicazione: {APP_DATA_DIR}")
    
    try:
        eel.start(page_to_serve, host='0.0.0.0', port=8000, size=(1200, 800), mode=None)
    except Exception as e:
        print(f"\nErrore durante l'avvio dell'applicazione Eel: {e}")
        print("Assicurati che la porta 8000 non sia già in uso e che Eel sia installato correttamente.")
        print("Potrebbe essere necessario chiudere il programma manualmente se si blocca.")
        sys.exit(1)

# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":

    print("\n--- Applicazione Eel Pronta ---")
    print(f"Server Eel in ascolto su tutte le interfacce sulla porta: 8000")
    print(f"Punto di accesso (Home Page): http://<IP_o_Nome_Host>:8000/main.html")
    print("\n!! Importante: Assicurati di aver copiato i contenuti completi HTML, CSS e JS nei rispettivi file, se non lo hai già fatto. !!")
    print("Premi Ctrl+C nel terminale per fermare il server.")

    start_eel_app('main.html')