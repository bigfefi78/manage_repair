// Version 2.6 - web/js/repair_detail.js (Gestione Campi Codice/Matricola 2 + Fix bug add/remove row)

let currentRepairId = null;

document.addEventListener('DOMContentLoaded', async (event) => {
    console.log('repair/detail.html DOM caricato.');

    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');

    if (id && id !== 'new') {
        currentRepairId = id;
        document.getElementById('pageTitle').innerText = 'Modifica Riparazione';
        document.getElementById('pageSubtitle').innerText = `Modifica i dettagli per la riparazione ID: ${currentRepairId}.`;
        document.getElementById('deleteRepairDetailBtn').style.display = 'inline-block';
        document.getElementById('printReportBtn').style.display = 'inline-block';
        await loadRepairDetails(currentRepairId);
    } else {
        document.getElementById('pageTitle').innerText = 'Aggiungi Nuova Riparazione';
        document.getElementById('pageSubtitle').innerText = 'Compila il modulo per aggiungere una nuova riparazione.';
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('reportDate').value = today;
    }

    document.getElementById('repairForm').addEventListener('submit', handleRepairFormSubmit);
    document.getElementById('addPartBtn').addEventListener('click', addPartRow);
    document.getElementById('addHoursBtn').addEventListener('click', addHoursRow);
    document.getElementById('deleteRepairDetailBtn').addEventListener('click', async () => {
        if (currentRepairId && confirm(`Sei sicuro di voler eliminare questa riparazione (ID: ${currentRepairId})?`)) {
            await deleteRepairAndNavigate(currentRepairId);
        }
    });
    document.getElementById('printReportBtn').addEventListener('click', () => {
        printRepairReport(currentRepairId);
    });

    if (!currentRepairId) {
        addPartRow();
        addHoursRow();
    }
});

async function loadRepairDetails(repairId) {
    console.log('Chiamata loadRepairDetails per ID:', repairId);
    try {
        const result = await eel.get_repair_details(parseInt(repairId))();

        if (result.status === 'success') {
            const data = result.data;
            console.log('Dati riparazione ricevuti:', data); // Lasciato per debugging, utile per i nuovi campi

            if (!data) {
                alert('Errore: Nessun dato riparazione ricevuto per ID ' + repairId);
                navigateTo('/repair/index.html');
                return;
            }

            // Popola i campi del form
            document.getElementById('repairId').value = data.id;
            document.getElementById('repairOa').value = data.repair_oa || '';
            document.getElementById('serviceOds').value = data.service_ods || '';
            document.getElementById('code').value = data.code || '';
            document.getElementById('serialNo').value = data.serial_no || '';
            // --- NUOVO: Popola campi Codice 2 e Matricola 2 ---
            document.getElementById('code2').value = data.code_2 || '';
            document.getElementById('serialNo2').value = data.serial_no_2 || '';
            // --- FINE NUOVO ---
            document.getElementById('status').value = data.status || 'Aperto';

            const repairedMaterialTypeRadio = document.querySelector(`input[name="repaired_material_type"][value="${data.repaired_material_type}"]`);
            if (repairedMaterialTypeRadio) {
                repairedMaterialTypeRadio.checked = true;
            } else {
                document.getElementById('repairedMaterial').checked = true;
            }

            document.getElementById('faultFound').value = data.fault_found || '';
            document.getElementById('remarksNote').value = data.remarks_note || '';
            document.getElementById('reportDate').value = data.report_date || '';
            document.getElementById('signatureName').value = data.signature_name || '';
            document.getElementById('signatureName2').value = data.signature_name_2 || '';

            const replacedPartsContainer = document.getElementById('replacedPartsContainer');
            replacedPartsContainer.innerHTML = '';
            if (data.parts && data.parts.length > 0) {
                data.parts.forEach(part => addPartRow(part));
            } else {
                addPartRow();
            }

            const hoursSpentContainer = document.getElementById('hoursSpentContainer');
            hoursSpentContainer.innerHTML = '';
            if (data.hours_spent && data.hours_spent.length > 0) {
                data.hours_spent.forEach(hours => addHoursRow(hours));
            } else {
                addHoursRow();
            }

            document.querySelectorAll('.form-check-input[type="checkbox"]').forEach(checkbox => {
                checkbox.checked = false;
            });
            document.getElementById('test9Notes').value = '';

            if (data.tests && data.tests.length > 0) {
                data.tests.forEach(test => {
                    const testInput = document.querySelector(`input[type="checkbox"][value="${test.test_name}"]`);
                    if (testInput) {
                        testInput.checked = (test.is_checked === 1);
                        if (test.test_name === "Any other / Altri:" && test.notes) {
                            document.getElementById('test9Notes').value = test.notes;
                        }
                    }
                });
            }

        } else {
            alert('Errore nel caricamento dei dettagli riparazione: ' + result.message);
            console.error('Errore nel recupero dettagli riparazione:', result.message);
            navigateTo('/repair/index.html');
        }
    } catch (error) {
        console.error('Eel call failed for get_repair_details:', error);
        alert('Errore di comunicazione con il backend per i dettagli riparazione.');
        navigateTo('/repair/index.html');
    }
}

async function handleRepairFormSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const repairData = {};

    repairData.repair_oa = formData.get('repair_oa');
    repairData.service_ods = formData.get('service_ods');
    repairData.code = formData.get('code');
    repairData.serial_no = formData.get('serial_no');
    // --- NUOVO: Raccogli campi Codice 2 e Matricola 2 ---
    repairData.code_2 = formData.get('code_2');
    repairData.serial_no_2 = formData.get('serial_no_2');
    // --- FINE NUOVO ---
    repairData.status = formData.get('status');
    repairData.repaired_material_type = formData.get('repaired_material_type');
    repairData.fault_found = formData.get('fault_found');
    repairData.remarks_note = formData.get('remarks_note');
    repairData.report_date = formData.get('report_date');
    repairData.signature_name = formData.get('signature_name');
    repairData.signature_name_2 = formData.get('signature_name_2');

    repairData.parts = [];
    document.querySelectorAll('#replacedPartsContainer .part-row').forEach(row => {
        const part_code = row.querySelector('[name="part_code[]"]').value;
        const description = row.querySelector('[name="part_description[]"]').value;
        const amount = row.querySelector('[name="part_amount[]"]').value;
        const position = row.querySelector('[name="part_position[]"]').value;
        if (part_code || description || (amount !== '') || position) {
            repairData.parts.push({
                part_code: part_code,
                description: description,
                amount: parseInt(amount) || 0,
                position: position
            });
        }
    });

    repairData.hours_spent = [];
    document.querySelectorAll('#hoursSpentContainer .hours-row').forEach(row => {
        const technician_name = row.querySelector('[name="technician_name[]"]').value;
        const hours_spent = row.querySelector('[name="hours_spent_amount[]"]').value;
        if (technician_name || (hours_spent !== '')) {
            repairData.hours_spent.push({
                technician_name: technician_name,
                hours_spent: parseFloat(hours_spent) || 0
            });
        }
    });

    repairData.tests = [];
    document.querySelectorAll('.form-check-input[type="checkbox"]').forEach(checkbox => {
        let notes = null;
        if (checkbox.value === 'Any other / Altri:') {
            notes = document.getElementById('test9Notes').value;
        }
        repairData.tests.push({
            test_name: checkbox.value,
            is_checked: checkbox.checked ? 1 : 0,
            notes: notes
        });
    });

    console.log("Dati inviati:", repairData);

    try {
        let result;
        if (currentRepairId) {
            result = await eel.update_repair(parseInt(currentRepairId), repairData)();
        } else {
            result = await eel.add_repair(repairData)();
        }

        if (result.status === 'success') {
            alert(result.message);
            navigateTo('/repair/index.html');
        } else {
            alert('Errore: ' + result.message);
            console.error('Errore nel salvare la riparazione:', result.message);
        }
    } catch (error) {
        console.error('Eel call failed for add/update repair:', error);
        alert('Errore di comunicazione con il backend per salvare la riparazione.');
    }
}

function addPartRow(part = {}) {
    const container = document.getElementById('replacedPartsContainer');
    const partRow = document.createElement('div');
    partRow.className = 'row g-3 mb-2 part-row align-items-center';
    partRow.innerHTML = `
        <div class="col-md-3">
            <input type="text" class="form-control form-control-sm" name="part_code[]" placeholder="Codice" value="${part.part_code || ''}">
        </div>
        <div class="col-md-4">
            <input type="text" class="form-control form-control-sm" name="part_description[]" placeholder="Descrizione" value="${part.description || ''}">
        </div>
        <div class="col-md-2">
            <input type="number" class="form-control form-control-sm" name="part_amount[]" placeholder="Quantità" value="${part.amount !== undefined ? part.amount : ''}">
        </div>
        <div class="col-md-2">
            <input type="text" class="form-control form-control-sm" name="part_position[]" placeholder="Posizione" value="${part.position || ''}">
        </div>
        <div class="col-md-1 d-flex justify-content-end">
            <button type="button" class="btn btn-danger btn-sm add-remove-btn remove-part-btn"><i class="bi bi-x"></i></button>
        </div>
    `;
    container.appendChild(partRow);

    partRow.querySelector('.remove-part-btn').addEventListener('click', (e) => {
        const allPartRows = container.querySelectorAll('.part-row');
        if (allPartRows.length > 1) {
            e.target.closest('.part-row').remove();
        } else {
            const currentRow = e.target.closest('.part-row');
            currentRow.querySelector('[name="part_code[]"]').value = '';
            currentRow.querySelector('[name="part_description[]"]').value = '';
            currentRow.querySelector('[name="part_amount[]"]').value = '';
            currentRow.querySelector('[name="part_position[]"]').value = '';
            alert("Deve esserci almeno una riga per i pezzi sostituiti. I campi sono stati svuotati.");
        }
    });
}

function addHoursRow(hours = {}) {
    const container = document.getElementById('hoursSpentContainer');
    const hoursRow = document.createElement('div');
    hoursRow.className = 'row g-3 mb-2 hours-row align-items-center';
    hoursRow.innerHTML = `
        <div class="col-md-5">
            <input type="text" class="form-control form-control-sm" name="technician_name[]" placeholder="Nome Tecnico" value="${hours.technician_name || ''}">
        </div>
        <div class="col-md-4">
            <input type="number" step="0.5" class="form-control form-control-sm" name="hours_spent_amount[]" placeholder="Ore Impiegate" value="${hours.hours_spent !== undefined ? hours.hours_spent : ''}">
        </div>
        <div class="col-md-1 d-flex justify-content-end">
            <button type="button" class="btn btn-danger btn-sm add-remove-btn remove-hours-btn"><i class="bi bi-x"></i></button>
        </div>
    `;
    container.appendChild(hoursRow);

    hoursRow.querySelector('.remove-hours-btn').addEventListener('click', (e) => {
        const allHoursRows = container.querySelectorAll('.hours-row');
        if (allHoursRows.length > 1) {
            e.target.closest('.hours-row').remove();
        } else {
            const currentRow = e.target.closest('.hours-row');
            currentRow.querySelector('[name="technician_name[]"]').value = '';
            currentRow.querySelector('[name="hours_spent_amount[]"]').value = '';
            alert("Deve esserci almeno una riga per le ore impiegate. I campi sono stati svuotati.");
        }
    });
}

async function deleteRepairAndNavigate(repairId) {
    try {
        const result = await eel.delete_repair(repairId)();
        if (result.status === 'success') {
            alert(result.message);
            navigateTo('/repair/index.html');
        } else {
            alert('Errore durante l\'eliminazione: ' + result.message);
            console.error('Errore durante l\'eliminazione:', result.message);
        }
    } catch (error) {
        console.error('Eel call failed for deleteRepairAndNavigate:', error);
        alert('Errore di comunicazione con il backend per l\'eliminazione.');
    }
}

async function printRepairReport(repairId) {
    if (!repairId) {
        alert("Impossibile stampare: ID riparazione non disponibile.");
        return;
    }

    try {
        const result = await eel.generate_repair_report_pdf(parseInt(repairId))();
        if (result.status === 'success') {
            const pdfUrl = result.filepath;
            console.log('PDF generato:', pdfUrl);
            window.open(pdfUrl, '_blank');
        } else {
            alert('Errore nella generazione del report PDF: ' + result.message);
            console.error('Errore generazione PDF:', result.message);
        }
    } catch (error) {
        console.error('Eel call failed for generate_repair_report_pdf:', error);
        alert('Errore di comunicazione con il backend per la generazione del PDF.');
    }
}