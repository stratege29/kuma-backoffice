// Firestore batch update script
// Generated: 2025-07-05 14:43:14
// Updates 21 stories

const admin = require('firebase-admin');
const serviceAccount = require('/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

const updates = [
  {
    "id": "story_za_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_za_001.jpg?alt=media"
  },
  {
    "id": "story_eg_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_eg_001.jpg?alt=media"
  },
  {
    "id": "story_dj_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_dj_001.jpg?alt=media"
  },
  {
    "id": "story_dz_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_dz_001.jpg?alt=media"
  },
  {
    "id": "story_gh_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_gh_001.jpg?alt=media"
  },
  {
    "id": "story_sl_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_sl_001.jpg?alt=media"
  },
  {
    "id": "story_ao_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_ao_001.jpg?alt=media"
  },
  {
    "id": "story_bf_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_bf_001.jpg?alt=media"
  },
  {
    "id": "story_ci_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_ci_001.jpg?alt=media"
  },
  {
    "id": "story_cd_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_cd_001.jpg?alt=media"
  },
  {
    "id": "story_zw_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_zw_001.jpg?alt=media"
  },
  {
    "id": "story_gn_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_gn_001.jpg?alt=media"
  },
  {
    "id": "story_cf_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_cf_001.jpg?alt=media"
  },
  {
    "id": "story_bj_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_bj_001.jpg?alt=media"
  },
  {
    "id": "story_et_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_et_001.jpg?alt=media"
  },
  {
    "id": "story_km_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_km_001.jpg?alt=media"
  },
  {
    "id": "story_cv_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_cv_001.jpg?alt=media"
  },
  {
    "id": "story_bw_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_bw_001.jpg?alt=media"
  },
  {
    "id": "story_mz_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_mz_001.jpg?alt=media"
  },
  {
    "id": "story_so_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_so_001.jpg?alt=media"
  },
  {
    "id": "story_cg_001",
    "imageUrl": "https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_cg_001.jpg?alt=media"
  }
];

async function updateStoryImages() {
  const batch = db.batch();
  
  console.log('📝 Updating', updates.length, 'stories...');
  
  for (const update of updates) {
    const storyRef = db.collection('stories').doc(update.id);
    batch.update(storyRef, { imageUrl: update.imageUrl });
  }
  
  try {
    await batch.commit();
    console.log('✅ Successfully updated', updates.length, 'stories');
  } catch (error) {
    console.error('❌ Error:', error);
  }
  
  process.exit();
}

updateStoryImages();
