// Update Firestore with correct Firebase Storage URLs
// New structure: stories/{storyId}/image.jpg
// New domain: kumafire-7864b.firebasestorage.app

const admin = require('firebase-admin');
const serviceAccount = require('/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function updateCorrectUrls() {
  try {
    console.log('🔄 Updating Firestore with correct Firebase Storage URLs...\n');
    
    // Get all stories
    const snapshot = await db.collection('stories').get();
    const updates = [];
    
    snapshot.forEach(doc => {
      const data = doc.data();
      const storyId = doc.id;
      
      // Generate correct URL with new domain and structure
      const newUrl = `https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.firebasestorage.app/o/stories%2F${storyId}%2Fimage.jpg?alt=media`;
      
      updates.push({
        id: storyId,
        title: data.title || 'No title',
        oldUrl: data.imageUrl || 'No image',
        newUrl: newUrl
      });
    });
    
    console.log(`📊 Found ${updates.length} stories to update\n`);
    
    // Show what will be updated
    console.log('🔍 Preview of updates:');
    updates.slice(0, 3).forEach(update => {
      console.log(`   ${update.id}: ${update.title}`);
      console.log(`   Old: ${update.oldUrl.substring(0, 50)}...`);
      console.log(`   New: ${update.newUrl.substring(0, 50)}...`);
      console.log();
    });
    
    if (updates.length > 3) {
      console.log(`   ... and ${updates.length - 3} more stories\n`);
    }
    
    // Apply updates in batches (Firestore limit is 500 per batch)
    const batchSize = 100;
    let updated = 0;
    
    for (let i = 0; i < updates.length; i += batchSize) {
      const batch = db.batch();
      const batchUpdates = updates.slice(i, i + batchSize);
      
      console.log(`📝 Updating batch ${Math.floor(i/batchSize) + 1}/${Math.ceil(updates.length/batchSize)} (${batchUpdates.length} stories)...`);
      
      batchUpdates.forEach(update => {
        const storyRef = db.collection('stories').doc(update.id);
        batch.update(storyRef, { imageUrl: update.newUrl });
      });
      
      await batch.commit();
      updated += batchUpdates.length;
      
      console.log(`   ✅ Updated ${updated}/${updates.length} stories`);
    }
    
    console.log(`\n✅ Successfully updated all ${updates.length} stories!`);
    console.log('\n🎯 New URL format:');
    console.log('https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.firebasestorage.app/o/stories%2F{storyId}%2Fimage.jpg?alt=media');
    
    // Save update log
    const updateLog = {
      timestamp: new Date().toISOString(),
      totalUpdated: updates.length,
      newUrlFormat: 'stories/{storyId}/image.jpg',
      newDomain: 'kumafire-7864b.firebasestorage.app',
      updates: updates
    };
    
    require('fs').writeFileSync('firestore_url_update_log.json', JSON.stringify(updateLog, null, 2));
    console.log('\n📄 Update log saved to firestore_url_update_log.json');
    
  } catch (error) {
    console.error('❌ Error updating Firestore:', error);
  }
  
  process.exit();
}

updateCorrectUrls();