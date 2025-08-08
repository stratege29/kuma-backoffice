// Export Firestore stories to JSON
// Run with: node export_firestore_stories.js

const admin = require('firebase-admin');
const fs = require('fs');

// Initialize Firebase Admin with credentials
const serviceAccount = require('/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function exportStories() {
  try {
    console.log('🔄 Fetching stories from Firestore...');
    const snapshot = await db.collection('stories').get();
    const stories = [];
    
    snapshot.forEach(doc => {
      const data = doc.data();
      stories.push({
        id: doc.id,
        title: data.title || '',
        countryCode: data.countryCode || '',
        imageUrl: data.imageUrl || '',
        country: data.country || '',
        order: data.order || 0
      });
    });
    
    // Sort by order
    stories.sort((a, b) => a.order - b.order);
    
    const exportData = {
      exportDate: new Date().toISOString(),
      count: stories.length,
      stories: stories
    };
    
    fs.writeFileSync('firestore_stories.json', JSON.stringify(exportData, null, 2));
    console.log(`✅ Exported ${stories.length} stories to firestore_stories.json`);
    
    // Print summary by country
    const byCountry = {};
    stories.forEach(story => {
      const cc = story.countryCode || 'UNKNOWN';
      byCountry[cc] = (byCountry[cc] || 0) + 1;
    });
    
    console.log('\n📊 Stories by country:');
    Object.entries(byCountry).sort().forEach(([cc, count]) => {
      console.log(`   ${cc}: ${count} stories`);
    });
    
  } catch (error) {
    console.error('❌ Error exporting stories:', error);
  }
  
  process.exit();
}

exportStories();