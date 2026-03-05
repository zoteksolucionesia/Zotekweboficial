const admin = require('firebase-admin');
const serviceAccount = require('./functions/serviceAccountKey.json');

admin.initializeApp({
    credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function check() {
    const doc = await db.collection('clients').doc('demo_clinica').collection('config').doc('menu').get();
    console.log(JSON.stringify(doc.data(), null, 2));
}

check().catch(console.error);
