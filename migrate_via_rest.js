const fs = require('fs');

const PROJECT_ID = 'zotek-ia';
const TOKEN = 'YOUR_TOKEN_HERE'; // I will replace this or use a bash command to get it

async function migrate() {
    const data = JSON.parse(fs.readFileSync('migration_data.json', 'utf8'));
    const clients = data.clients || [];

    for (const client of clients) {
        const docId = client.phone_number_id;
        const url = `https://firestore.googleapis.com/v1/projects/${PROJECT_ID}/databases/(default)/documents/clients/${docId}`;

        const fields = {};
        for (const [key, value] of Object.entries(client)) {
            if (value === null) continue;
            if (typeof value === 'string') fields[key] = { stringValue: value };
            else if (typeof value === 'number') fields[key] = { integerValue: value.toString() };
        }

        console.log(`Migrating client ${client.name}...`);
        const res = await fetch(url, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ fields })
        });

        if (res.ok) {
            console.log(`Successfully migrated ${client.name}`);
        } else {
            console.error(`Failed to migrate ${client.name}:`, await res.text());
        }
    }
}

migrate();
