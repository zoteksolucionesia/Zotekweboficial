async function fetchClients() {
    const response = await fetch('/api/clients');
    const clients = await response.json();
    const tbody = document.getElementById('client-table-body');
    tbody.innerHTML = '';

    clients.forEach(client => {
        const row = `
            <tr>
                <td>${client.id}</td>
                <td>${client.name}</td>
                <td><code>${client.phone_number_id}</code></td>
                <td>${new Date(client.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn" onclick="editClient(${client.id})">Editar</button>
                </td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

function openModal(isEdit = false) {
    document.getElementById('clientModal').style.display = 'flex';
    document.getElementById('modalTitle').innerText = isEdit ? 'Editar Cliente' : 'Agregar Cliente';
    if (!isEdit) {
        document.getElementById('clientForm').reset();
        document.getElementById('clientId').value = '';
    }
}

function closeModal() {
    document.getElementById('clientModal').style.display = 'none';
}

async function editClient(id) {
    const response = await fetch(`/api/clients/${id}`);
    const client = await response.json();

    document.getElementById('clientId').value = client.id;
    document.getElementById('clientName').value = client.name;
    document.getElementById('whatsappToken').value = client.whatsapp_token;
    document.getElementById('phoneNumberId').value = client.phone_number_id;
    document.getElementById('verifyToken').value = client.verify_token;
    document.getElementById('systemInstruction').value = client.system_instruction || '';

    openModal(true);
}

async function saveClient(event) {
    event.preventDefault();
    const id = document.getElementById('clientId').value;
    const data = {
        name: document.getElementById('clientName').value,
        whatsapp_token: document.getElementById('whatsappToken').value,
        phone_number_id: document.getElementById('phoneNumberId').value,
        verify_token: document.getElementById('verifyToken').value,
        system_instruction: document.getElementById('systemInstruction').value,
    };

    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/clients/${id}` : '/api/clients';

    const response = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (response.ok) {
        closeModal();
        fetchClients();
    } else {
        alert('Error al guardar cliente');
    }
}

// Initial load
document.addEventListener('DOMContentLoaded', fetchClients);
