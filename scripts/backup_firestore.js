// Backup current imageUrls before updating
const admin = require('firebase-admin');
const fs = require('fs');
const serviceAccount = require('/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function backupImageUrls() {
  try {
    const snapshot = await db.collection('stories').get();
    const backup = [];
    
    snapshot.forEach(doc => {
      const data = doc.data();
      backup.push({
        id: doc.id,
        oldImageUrl: data.imageUrl || ''
      });
    });
    
    fs.writeFileSync('imageurl_backup.json', JSON.stringify(backup, null, 2));
    console.log(`✅ Backed up ${backup.length} imageUrls to imageurl_backup.json`);
    
  } catch (error) {
    console.error('❌ Backup failed:', error);
  }
  
  process.exit();
}

backupImageUrls();