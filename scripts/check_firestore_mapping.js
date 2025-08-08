// Check actual Firestore story IDs vs generated IDs
const admin = require('firebase-admin');
const serviceAccount = require('/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function checkMappings() {
  try {
    console.log('🔍 Checking actual Firestore story IDs...\n');
    
    const snapshot = await db.collection('stories').get();
    const stories = [];
    
    snapshot.forEach(doc => {
      const data = doc.data();
      stories.push({
        id: doc.id,
        title: data.title || 'No title',
        countryCode: data.countryCode || 'No country',
        imageUrl: data.imageUrl || 'No image'
      });
    });
    
    // Sort by country code
    stories.sort((a, b) => a.countryCode.localeCompare(b.countryCode));
    
    console.log('📊 Actual stories in Firestore:');
    console.log('===============================');
    
    const byCountry = {};
    
    stories.forEach(story => {
      const cc = story.countryCode.toUpperCase();
      if (!byCountry[cc]) byCountry[cc] = [];
      byCountry[cc].push(story);
      
      console.log(`${cc}: ${story.id}`);
      console.log(`   Title: ${story.title}`);
      console.log(`   Current imageUrl: ${story.imageUrl.substring(0, 50)}...`);
      console.log();
    });
    
    console.log('\n📈 Summary by country:');
    Object.keys(byCountry).sort().forEach(cc => {
      console.log(`${cc}: ${byCountry[cc].length} stories`);
    });
    
    console.log(`\n✅ Total: ${stories.length} stories found`);
    
    // Check uploaded images
    console.log('\n🖼️  Checking uploaded Firebase Storage images...');
    
    // This would require Firebase Storage API call
    // For now, just show what we expect vs reality
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
  
  process.exit();
}

checkMappings();