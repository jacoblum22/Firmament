// Simple Node.js test to simulate browser upload behavior
const fs = require('fs');
const fetch = require('node-fetch');
const FormData = require('form-data');

async function testBrowserLikeUpload() {
    const url = 'http://localhost:8000/upload';
    const filePath = '../test_upload.txt';
    
    try {
        const formData = new FormData();
        const fileStream = fs.createReadStream(filePath);
        formData.append('file', fileStream, 'test_upload.txt');
        
        console.log('Testing browser-like upload...');
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            // Don't set Content-Type - let FormData handle it
        });
        
        console.log(`Status: ${response.status}`);
        const text = await response.text();
        console.log(`Response: ${text}`);
        
        if (response.status === 422) {
            console.log('❌ Still getting 422 error');
        } else if (response.status === 200) {
            console.log('✅ Upload successful');
        }
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

testBrowserLikeUpload();
