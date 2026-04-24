// Version 2.1 - web/js/repair.js

document.addEventListener('DOMContentLoaded', (event) => {
    console.log('repair/index.html DOM caricato.');
    loadRepairsTable(); // Carica la tabella delle riparazioni all'avvio della pagina

    // Listener per il pulsante "Aggiungi Nuova Riparazione"
    const addNewRepairBtn = document.getElementById('addNewRepairBtn');
    if (addNewRepairBtn) {
        addNewRepairBtn.addEventListener('click', () => {
            // Reindirizza alla pagina per aggiungere una nuova riparazione
            navigateTo('/repair/detail.html?id=new');
        });
    }
});

async function loadRepairsTable() {
    const repairsTableBody = document.getElementById('repairsTableBody');
    if (!repairsTableBody) {
        console.error("Elemento 'repairsTableBody' non trovato.");
        return;
    }

    repairsTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-primary">Caricamento riparazioni...</td></tr>';

    try {
        const result = await eel.get_repairs_summary()(); // Chiama la funzione Python esposta
        if (result.status === 'success') {
            const repairs = result.data;
            repairsTableBody.innerHTML = ''; // Pulisci il messaggio di caricamento
            if (repairs.length === 0) {
                repairsTableBody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nessuna riparazione trovata.</td></tr>';
            } else {
                repairs.forEach(repair => {
                    const row = repairsTableBody.insertRow();
                    row.innerHTML = `
                        <td>${repair.repair_oa}</td>
                        <td>${repair.service_ods}</td>
                        <td>${repair.creation_date || 'N.D.'}</td>
                        <td><span class="badge ${getStatusBadgeClass(repair.status)}">${repair.status}</span></td>
                        <td class="text-center">
                            <button class="btn btn-sm btn-primary view-details-btn" data-id="${repair.id}" title="Visualizza/Modifica">
                                <i class="bi bi-pencil-square"></i>
                            </button>
                            <button class="btn btn-sm btn-danger delete-repair-btn ms-2" data-id="${repair.id}" title="Elimina Riparazione">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                });

                // Aggiungi listener per i pulsanti Dettagli/Modifica e Elimina
                document.querySelectorAll('.view-details-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        const repairId = e.currentTarget.dataset.id;
                        navigateTo(`/repair/detail.html?id=${repairId}`);
                    });
                });
                document.querySelectorAll('.delete-repair-btn').forEach(button => {
                    button.addEventListener('click', async (e) => {
                        const repairId = e.currentTarget.dataset.id;
                        if (confirm(`Sei sicuro di voler eliminare la riparazione con ID ${repairId} (Repair OA: ${e.currentTarget.closest('tr').cells[0].innerText})?`)) {
                            await deleteRepair(repairId);
                        }
                    });
                });
            }
        } else {
            repairsTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Errore durante il caricamento: ${result.message}</td></tr>`;
            console.error('Errore nel recupero riassunto riparazioni:', result.message);
        }
    } catch (error) {
        repairsTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Errore di comunicazione con il backend.</td></tr>`;
        console.error('Errore Eel call get_repairs_summary:', error);
    }
}

async function deleteRepair(repairId) {
    try {
        const result = await eel.delete_repair(repairId)(); // Chiama la funzione Python esposta
        if (result.status === 'success') {
            alert(result.message);
            loadRepairsTable(); // Ricarica la tabella dopo l'eliminazione
        } else {
            alert('Errore: ' + result.message);
        }
    } catch (error) {
        console.error('Eel call failed for delete_repair:', error);
        alert('Errore di comunicazione con il backend per l\'eliminazione.');
    }
}

// Funzione helper per ottenere la classe del badge Bootstrap in base allo stato
function getStatusBadgeClass(status) {
    switch (status) {
        case 'Aperto': return 'bg-primary status-open';
        case 'Chiuso': return 'bg-success status-closed';
        case 'Sospeso': return 'bg-warning text-dark status-suspended';
        default: return 'bg-secondary';
    }
}