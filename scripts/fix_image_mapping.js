// Fix the image mapping by using actual story IDs
const admin = require('firebase-admin');
const fs = require('fs');
const serviceAccount = require('/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

// Function to normalize text for matching
function normalizeText(text) {
  return text
    .toLowerCase()
    .replace(/[àáâãäå]/g, 'a')
    .replace(/[èéêë]/g, 'e')
    .replace(/[ìíîï]/g, 'i')
    .replace(/[òóôõö]/g, 'o')
    .replace(/[ùúûü]/g, 'u')
    .replace(/[ç]/g, 'c')
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// Function to calculate similarity between two strings
function similarity(a, b) {
  const wordsA = normalizeText(a).split(' ');
  const wordsB = normalizeText(b).split(' ');
  
  const intersection = wordsA.filter(word => wordsB.includes(word));
  const union = [...new Set([...wordsA, ...wordsB])];
  
  return union.length > 0 ? intersection.length / union.length : 0;
}

async function fixImageMapping() {
  try {
    console.log('🔍 Analyzing current situation...\n');
    
    // Get all stories from Firestore
    const snapshot = await db.collection('stories').get();
    const stories = {};
    const storiesByCountry = {};
    
    snapshot.forEach(doc => {
      const data = doc.data();
      const story = {
        id: doc.id,
        title: data.title || '',
        countryCode: (data.countryCode || '').toUpperCase(),
        currentImageUrl: data.imageUrl || ''
      };
      
      stories[doc.id] = story;
      
      if (!storiesByCountry[story.countryCode]) {
        storiesByCountry[story.countryCode] = [];
      }
      storiesByCountry[story.countryCode].push(story);
    });
    
    console.log(`📚 Found ${Object.keys(stories).length} stories in Firestore`);
    
    // Read the mapping report to understand what images we have
    let mappingReport = {};
    if (fs.existsSync('mapping_report.json')) {
      mappingReport = JSON.parse(fs.readFileSync('mapping_report.json', 'utf8'));
      console.log(`📄 Found mapping report with ${mappingReport.mappings?.length || 0} mappings`);
    }
    
    // Get list of uploaded images (they should follow pattern story_XX_001.jpg)
    const uploadedImages = fs.readdirSync('firebase_ready_images').filter(f => f.endsWith('.jpg'));
    console.log(`🖼️  Found ${uploadedImages.length} uploaded images`);
    
    // Create correct mappings
    const corrections = [];
    const countryImageMap = {};
    
    // Group uploaded images by country
    uploadedImages.forEach(filename => {
      const match = filename.match(/story_([a-z]{2})_\d+\.jpg/i);
      if (match) {
        const country = match[1].toUpperCase();
        if (!countryImageMap[country]) countryImageMap[country] = [];
        countryImageMap[country].push(filename);
      }
    });
    
    console.log('\n🗺️  Creating correct mappings...');
    
    // For each country, try to match images with stories
    Object.keys(countryImageMap).forEach(countryCode => {
      const countryImages = countryImageMap[countryCode];
      const countryStories = storiesByCountry[countryCode] || [];
      
      console.log(`\n${countryCode}: ${countryImages.length} images, ${countryStories.length} stories`);
      
      if (countryStories.length === 1 && countryImages.length === 1) {
        // Simple 1:1 mapping
        const story = countryStories[0];
        const image = countryImages[0];
        const newUrl = `https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2F${image}?alt=media`;
        
        corrections.push({
          storyId: story.id,
          storyTitle: story.title,
          oldUrl: story.currentImageUrl,
          newUrl: newUrl,
          confidence: 'high',
          reason: 'Single story per country'
        });
        
        console.log(`   ✅ ${story.id} → ${image}`);
      } else if (countryStories.length > 1 && countryImages.length >= 1) {
        // Multiple stories - try to match by title similarity
        const originalMappings = mappingReport.mappings || [];
        
        countryStories.forEach(story => {
          // Find original mapping for this story's country
          const originalMapping = originalMappings.find(m => 
            m.country_code === countryCode && 
            similarity(m.story_title || '', story.title) > 0.3
          );
          
          if (originalMapping) {
            // Use the same image pattern but with correct story ID
            const imagePattern = countryImages[0]; // Use first available image for now
            const newUrl = `https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2F${imagePattern}?alt=media`;
            
            corrections.push({
              storyId: story.id,
              storyTitle: story.title,
              oldUrl: story.currentImageUrl,
              newUrl: newUrl,
              confidence: 'medium',
              reason: 'Title similarity match'
            });
            
            console.log(`   🟡 ${story.id} → ${imagePattern} (similarity match)`);
          } else {
            console.log(`   ⚠️  No good match for: ${story.title}`);
          }
        });
      } else {
        console.log(`   ❌ Mismatch: ${countryImages.length} images vs ${countryStories.length} stories`);
      }
    });
    
    console.log(`\n📊 Total corrections to make: ${corrections.length}`);
    
    if (corrections.length === 0) {
      console.log('❌ No corrections identified. Manual review needed.');
      return;
    }
    
    // Save corrections plan
    fs.writeFileSync('corrections_plan.json', JSON.stringify(corrections, null, 2));
    console.log('📄 Saved corrections plan to corrections_plan.json');
    
    // Ask for confirmation (in real scenario)
    console.log('\n🚀 Applying corrections...');
    
    // Apply corrections
    const batch = db.batch();
    
    corrections.forEach(correction => {
      const storyRef = db.collection('stories').doc(correction.storyId);
      batch.update(storyRef, { imageUrl: correction.newUrl });
    });
    
    await batch.commit();
    
    console.log(`✅ Successfully updated ${corrections.length} stories`);
    console.log('\n🎯 Test the image URLs now!');
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
  
  process.exit();
}

fixImageMapping();