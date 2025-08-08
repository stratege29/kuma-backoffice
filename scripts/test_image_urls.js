// Test if Firebase Storage images are accessible
const https = require('https');
const fs = require('fs');

// List of image URLs to test (from the uploaded images)
const testUrls = [
  'https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_ao_001.jpg?alt=media',
  'https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_za_001.jpg?alt=media',
  'https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_gh_001.jpg?alt=media',
  'https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_eg_001.jpg?alt=media',
  'https://firebasestorage.googleapis.com/v0/b/kumafire-7864b.appspot.com/o/stories%2Fstory_dj_001.jpg?alt=media'
];

function testUrl(url) {
  return new Promise((resolve) => {
    const req = https.get(url, (res) => {
      resolve({
        url: url,
        status: res.statusCode,
        contentType: res.headers['content-type'],
        contentLength: res.headers['content-length'],
        success: res.statusCode === 200
      });
    });
    
    req.on('error', (error) => {
      resolve({
        url: url,
        status: 'ERROR',
        error: error.message,
        success: false
      });
    });
    
    req.setTimeout(5000, () => {
      req.destroy();
      resolve({
        url: url,
        status: 'TIMEOUT',
        success: false
      });
    });
  });
}

async function testAllUrls() {
  console.log('🔍 Testing Firebase Storage image URLs...\n');
  
  const results = [];
  
  for (const url of testUrls) {
    console.log(`📡 Testing: ${url.split('/').pop()}`);
    const result = await testUrl(url);
    results.push(result);
    
    if (result.success) {
      console.log(`   ✅ Success (${result.contentLength} bytes, ${result.contentType})`);
    } else {
      console.log(`   ❌ Failed (Status: ${result.status})`);
      if (result.error) console.log(`      Error: ${result.error}`);
    }
    console.log();
  }
  
  // Summary
  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log('📊 Test Summary:');
  console.log(`   ✅ Successful: ${successful}/${testUrls.length}`);
  console.log(`   ❌ Failed: ${failed}/${testUrls.length}`);
  
  if (failed > 0) {
    console.log('\n🔧 Possible issues:');
    console.log('   1. Files were not uploaded successfully');
    console.log('   2. Firebase Storage rules are too restrictive');
    console.log('   3. Files exist but with different names');
    console.log('\n💡 Solutions:');
    console.log('   1. Check Firebase Storage console');
    console.log('   2. Verify file names match exactly');
    console.log('   3. Check Storage security rules');
  } else {
    console.log('\n✅ All images are accessible!');
    console.log('   The URLs are working correctly.');
  }
  
  // Save results for reference
  fs.writeFileSync('url_test_results.json', JSON.stringify(results, null, 2));
  console.log('\n📄 Results saved to url_test_results.json');
}

testAllUrls().catch(console.error);