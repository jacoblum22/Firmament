s3_storage:
Using relative_to(Path(".")) depends on the current working directory, which may not be consistent.

Calculate relative paths from a known base:

-    relative_path = file_path.relative_to(Path("."))
+    # Calculate relative path from the application's base directory (not CWD)
+    base_dir = Path(__file__).parent.parent.resolve()  # backend directory  
+    base_path = base_dir / "uploads" if "uploads" in str(local_prefix) else base_dir
+    relative_path = file_path.relative_to(base_path)
     key = str(relative_path).replace("\\", "/")

Handle S3 pagination for large buckets

The current implementation doesn't handle pagination, which means it will only return up to 1000 objects (S3's default limit).

Implement pagination to handle large buckets:

 if self.use_s3 and self.s3_client:
     # List from S3
-    response = self.s3_client.list_objects_v2(
-        Bucket=self.settings.s3_bucket_name, Prefix=prefix
-    )
-    return [obj["Key"] for obj in response.get("Contents", [])]
+    files = []
+    paginator = self.s3_client.get_paginator('list_objects_v2')
+    page_iterator = paginator.paginate(
+        Bucket=self.settings.s3_bucket_name,
+        Prefix=prefix
+    )
+    for page in page_iterator:
+        files.extend([obj["Key"] for obj in page.get("Contents", [])])
+    return files

Security: Prevent path traversal attacks

The _get_local_path method is vulnerable to path traversal attacks. A malicious key containing "../" could access files outside the intended directories.

Add path validation to prevent directory traversal:

 def _get_local_path(self, key: str) -> Path:
     """Get local file path for a given key"""
+    # Normalize and validate key to prevent path traversal (cross-platform)
+    normalized_key = key.replace("\\", "/")  # Normalize Windows separators
+    if ".." in normalized_key or normalized_key.startswith("/") or "\\" in key:
+        raise ValueError(f"Invalid key: {key}")
+    
     # Remove S3 prefixes and create local equivalent
-    clean_key = key.replace(self.settings.s3_uploads_prefix, "uploads/")
+    clean_key = normalized_key.replace(self.settings.s3_uploads_prefix, "uploads/")
     clean_key = clean_key.replace(self.settings.s3_cache_prefix, "cache/")
     clean_key = clean_key.replace(self.settings.s3_temp_prefix, "temp_chunks/")
 
     local_path = Path(clean_key)
+    # Ensure the resolved path is within expected directories
+    local_path_resolved = local_path.resolve()
+    # Resolve allowed_dirs to absolute paths for proper comparison
+    allowed_dirs = [Path("uploads").resolve(), Path("cache").resolve(), Path("temp_chunks").resolve()]
+    if not any(local_path_resolved.is_relative_to(d) for d in allowed_dirs):
+        raise ValueError(f"Path outside allowed directories: {local_path_resolved}")
+    
     local_path.parent.mkdir(parents=True, exist_ok=True)
-    return local_path

Consider thread safety and settings management

The singleton implementation has potential issues:

Not thread-safe - concurrent calls could create multiple instances
Creating Settings() without parameters might not use the correct configuration
Consider using thread-safe initialization and requiring explicit settings:

+import threading
+
 # Global storage manager instance
 _storage_manager: Optional[S3StorageManager] = None
+_lock = threading.Lock()
 
 
-def get_storage_manager() -> S3StorageManager:
+def get_storage_manager(settings: Optional[Settings] = None) -> S3StorageManager:
     """Get the global storage manager instance"""
     global _storage_manager
-    if _storage_manager is None:
-        settings = Settings()
-        _storage_manager = S3StorageManager(settings)
-    return _storage_manager
+    
+    if _storage_manager is None:
+        with _lock:
+            if _storage_manager is None:
+                if settings is None:
+                    raise ValueError("Settings must be provided for initial setup")
+                _storage_manager = S3StorageManager(settings)
+    return _storage_manager

MVP_COMPLETION_REPORT:
Remove personal e-mail address – PII leakage
The report includes a real personal e-mail (jacobdavidandersenlum@gmail.com). This is unnecessary for a public repo and violates privacy best practices. Mask or drop it.

- User Profile: Jacob Andersen (jacobdavidandersenlum@gmail.com)
+ User Profile: Jacob Andersen

Second occurrence of e-mail address – please redact consistently
The same e-mail is repeated under “File Processing Evidence”. Ensure all instances are removed.

- User Authentication: `jacobdavidandersenlum@gmail.com`
+ User Authentication: `<redacted>`

Avoid exposing real S3 bucket names in public documentation
Publishing the production bucket name (studymate-prod-storage) can make the account an easier target for enumeration or social-engineering attacks. Replace it with a placeholder or move this detail to a private, internal doc.

- **S3 Bucket**: `studymate-prod-storage` (us-east-2)
+ **S3 Bucket**: `<redacted-bucket-name>` (us-east-2)

test_frontend_upload.py:
Fix Content-Type header in Test 3.

Setting Content-Type: multipart/form-data without the boundary parameter will cause the request to fail.

The requests library automatically generates the correct Content-Type header with boundary when using the files parameter. Manually overriding it without the boundary will break the request.

-            print("=== Test 3: Upload with explicit multipart Content-Type ===")
-            # Try with explicit multipart content type
-            headers = {"Content-Type": "multipart/form-data"}
-            response = requests.post(url, files=files, headers=headers)
+            print("=== Test 3: Upload letting requests handle Content-Type ===")
+            # Let requests automatically set the correct multipart Content-Type with boundary
+            response = requests.post(url, files=files)

Fix Content-Type header handling in Test 2.

Setting Content-Type: application/json while sending multipart form data will cause the request to fail because the boundary parameter will be missing from the Content-Type header.

When you manually set the Content-Type header, requests won't automatically add the required boundary parameter for multipart data. This test scenario might not accurately simulate the frontend issue you're trying to debug.

Consider either:

Removing this test if it doesn't represent a real frontend scenario
Or documenting that this is expected to fail and why
             print("=== Test 2: Upload with Content-Type application/json header ===")
-            # This might simulate the issue where the frontend accidentally sets Content-Type
+            # This will fail because multipart data needs boundary parameter
             headers = {"Content-Type": "application/json"}
             response = requests.post(url, files=files, headers=headers)

Consider making the test more flexible and robust.

The hardcoded URL and relative file path make this test environment-dependent and potentially fragile.

Consider these improvements:

-def test_frontend_like_upload():
+def test_frontend_like_upload(base_url="http://localhost:8000", test_file_path="../test_upload.txt"):
     """Test upload simulating frontend behavior"""
-    url = "http://localhost:8000/upload"
+    url = f"{base_url}/upload"
 
     # Test with the test file we created
-    file_path = "../test_upload.txt"
+    file_path = test_file_path
Alternatively, consider using environment variables or a proper test configuration.

Consider making this a proper test with assertions.

This script prints results for manual inspection but doesn't make any assertions about expected behavior.

For a proper integration test, consider adding assertions:

+    expected_success_status = 200  # or whatever your API returns on success
+    
     try:
         with open(file_path, "rb") as f:
             # Test 1: Normal upload (should succeed)
             files = {"file": ("test_upload.txt", f, "text/plain")}
             response = requests.post(url, files=files)
             print(f"Status: {response.status_code}")
             print(f"Response: {response.text}")
+            assert response.status_code == expected_success_status, f"Expected {expected_success_status}, got {response.status_code}"

test_google_oath.py:
Avoid printing sensitive credential information.

Printing even partial client IDs could pose a security risk, especially in logs or CI/CD environments. Consider removing or making this optional with a debug flag.

-        print(f"✓ Client ID: {settings.google_client_id[:20]}...")
+        print("✓ Client ID: [CONFIGURED]")

Avoid hardcoding production environment in test scripts.

Setting the environment to "production" in a test script is problematic and could lead to unintended side effects or security risks. Consider using a test environment or making this configurable.

-# Set production environment
-os.environ["ENVIRONMENT"] = "production"
+# Set test environment (or make configurable)
+os.environ["ENVIRONMENT"] = os.getenv("TEST_ENVIRONMENT", "test")

Consider improving import structure instead of modifying sys.path.

Modifying sys.path is generally not a best practice and suggests potential issues with the project's import structure. Consider using proper package imports or running the script from the correct directory.

If this path modification is necessary, consider adding error handling:

-# Add the current directory to Python path for imports
-sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
+# Add the backend directory to Python path for imports
+backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
+if os.path.exists(backend_dir):
+    sys.path.insert(0, backend_dir)
+else:
+    raise ImportError("Backend directory not found")
Remove misleading status claims without verification.

The script claims various setup steps are "Complete" and "Created" without actually verifying these claims. This could mislead developers about the actual state of their OAuth setup.

-    print("\n📋 OAuth Setup Status:")
-    print("✓ Backend configuration: Complete")
-    print("✓ Google Cloud Project: Created")
-    print("✓ OAuth consent screen: Configured")
-    print("✓ OAuth credentials: Generated and configured")
-    print("\n🎉 Google OAuth setup is complete!")
+    print("\n📋 Configuration Status:")
+    print("✓ Backend OAuth configuration: Loaded")
+    if settings.google_client_id and settings.google_client_secret:
+        print("✓ Google OAuth credentials: Present")
+        print("\n🎉 OAuth credentials are configured!")
+    else:
+        print("❌ Google OAuth credentials: Missing")
+        print("\n⚠️  OAuth credentials need to be configured!")

GOOGLE_OAUTH_SETUP:
Out-of-date & server-side packages suggested for the frontend
@google-cloud/local-auth / google-auth-library are Node-only and not needed in a browser bundle; react-google-login is archived. Recommend the modern GIS SDK or @react-oauth/google.

-npm install @google-cloud/local-auth google-auth-library
-# or
-npm install react-google-login  # for React
+npm install @react-oauth/google           # React wrapper around Google Identity Services
+# (Optional, server-side token verification)
+# npm install google-auth-library

Google+ API is long-deprecated – instruct users to enable Google Identity / People APIs instead
The Google+ API was shut down in 2019. Continuing to reference it will lead to “API has been shut down” errors and unnecessary support noise.

-## Step 2: Enable Google+ API
+# ## Step 2: Enable Google Identity / People APIs
 ...
-2. **Search for Google+ API**:
-   - Search for "Google+ API" or "Google Identity"
-   - Click on "Google+ API"
-   - Click "Enable"
+2. **Search for and enable**:
+   - “Google People API”  (basic profile / email scopes)
+   - “Google Identity Services” (OAuth infrastructure)

React example uses deprecated component & response fields
react-google-login returns tokenId; GIS now returns credential. Modern example:

-import { GoogleLogin } from 'react-google-login';
+import { GoogleOAuthProvider, GoogleLogin } from '@react-oauth/google';
 ...
-const GoogleAuthButton = () => {
+const GoogleAuthButton = () => (
+  <GoogleOAuthProvider clientId="your-google-client-id">
+    <GoogleLogin
+      onSuccess={async (credentialResponse) => {
+        const res = await fetch('/auth/google', {
+          method: 'POST',
+          headers: { 'Content-Type': 'application/json' },
+          body: JSON.stringify({ token: credentialResponse.credential })
+        });
+        const data = await res.json();
+        if (data.success) {
+          localStorage.setItem('sessionToken', data.session_token);
+        }
+      }}
+      onError={() => console.error('Login failed')}
+    />
+  </GoogleOAuthProvider>
+);

UserProfile:
Add null checks for user properties to prevent runtime errors.

The code assumes user.name, user.email, and other properties exist, but these could be null or undefined, causing runtime errors.

        {user.picture ? (
          <img
            src={user.picture}
-           alt={user.name}
+           alt={user.name || 'User avatar'}
            className="w-8 h-8 rounded-full"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
-           {user.name.charAt(0).toUpperCase()}
+           {user.name?.charAt(0)?.toUpperCase() || '?'}
          </div>
        )}
        <div className="flex flex-col items-start">
-         <span className="text-sm font-medium text-gray-900">{user.name}</span>
-         <span className="text-xs text-gray-500">{user.email}</span>
+         <span className="text-sm font-medium text-gray-900">{user.name || 'Unknown'}</span>
+         <span className="text-xs text-gray-500">{user.email || 'No email'}</span>
        </div>

Same null safety issues and code duplication.

The same null reference issues exist here as in the main button. Additionally, the avatar rendering logic is duplicated.

Apply similar null checks as suggested for the main button:

                {user.picture ? (
                  <img
                    src={user.picture}
-                   alt={user.name}
+                   alt={user.name || 'User avatar'}
                    className="w-12 h-12 rounded-full"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium text-lg">
-                   {user.name.charAt(0).toUpperCase()}
+                   {user.name?.charAt(0)?.toUpperCase() || '?'}
                  </div>
                )}
                <div className="flex flex-col">
-                 <span className="font-medium text-gray-900">{user.name}</span>
-                 <span className="text-sm text-gray-500">{user.email}</span>
+                 <span className="font-medium text-gray-900">{user.name || 'Unknown'}</span>
+                 <span className="text-sm text-gray-500">{user.email || 'No email'}</span>
                </div>
Consider extracting the avatar rendering into a reusable component to reduce duplication.

test_cache:
Fix the path manipulation to correctly add the backend directory.

The current path manipulation adds the test directory itself (backend/tests/unit) rather than the backend root directory, which will cause import failures for utils.content_cache.

-# Add the backend directory to the Python path
-sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
+# Add the backend directory to the Python path
+backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
+sys.path.insert(0, os.path.abspath(backend_dir))

Add assertion to verify cache existence.

The test should assert that the cache exists after being saved in the previous test.

 # Test 2: Check cache exists
 print("\n2. Testing cache existence check...")
 has_cache = cache.has_transcription_cache(test_content)
+assert has_cache, "Cache should exist after being saved"
 print(f"Cache exists: {has_cache}")

 Add assertion for negative test case.

Verify that cache miss behavior works correctly by asserting the expected result.

 # Test 4: Test with different content (should not find cache)
 print("\n4. Testing cache miss...")
 different_content = b"This is different content."
 has_different_cache = cache.has_transcription_cache(different_content)
+assert not has_different_cache, "Different content should not have cache"
 print(f"Different content has cache: {has_different_cache}")

 Add assertions to validate cache statistics.

Verify that the statistics make sense given the operations performed so far.

 # Test 5: Cache statistics
 print("\n5. Testing cache statistics...")
 stats = cache.get_cache_stats()
+assert isinstance(stats, dict), "Stats should be a dictionary"
+assert stats['total_entries'] >= 1, "Should have at least one cache entry"
+assert stats['transcription_entries'] >= 1, "Should have at least one transcription entry"
+assert stats['total_size_mb'] >= 0, "Total size should be non-negative"
 print(f"Total entries: {stats['total_entries']}")
 print(f"Transcription entries: {stats['transcription_entries']}")
 print(f"Total size: {stats['total_size_mb']:.2f} MB")

 Add assertions and error handling to verify test correctness.

The test only prints output without verifying that the caching operation succeeded correctly. Add assertions to ensure the operation works as expected.

 # Test 1: Save transcription cache
 print("\n1. Testing transcription cache save...")
+try:
     content_hash = cache.save_transcription_cache(
         test_content, test_transcription, test_filename, test_extension
     )
+    assert content_hash, "Content hash should not be empty"
+    assert len(content_hash) >= 8, "Content hash should be at least 8 characters"
     print(f"Saved with content hash: {content_hash[:8]}...")
+except Exception as e:
+    print(f"❌ Failed to save transcription cache: {e}")
+    return False

Add assertions and improve data validation for processed cache test.

Add proper assertions and safer handling of retrieved data structures.

 # Test 6: Processed data cache
 print("\n6. Testing processed data cache...")
 test_processed_data = {
     "segments": [{"text": "Test segment", "position": 0}],
     "clusters": [{"cluster_id": 0, "heading": "Test Topic"}],
     "meta": {"total_words": 2},
 }

 processed_hash = cache.save_processed_cache(
     test_content, test_processed_data, test_filename
 )

 Add assertions and safer string handling.

Add proper assertions to verify the cached data structure and handle potential string length issues.

 # Test 3: Retrieve cached transcription
 print("\n3. Testing cache retrieval...")
 cached_data = cache.get_transcription_cache(test_content)
-if cached_data:
+assert cached_data, "Should be able to retrieve cached data"
+assert 'text' in cached_data, "Cached data should contain 'text' field"
+assert 'metadata' in cached_data, "Cached data should contain 'metadata' field"
+assert 'cache_info' in cached_data, "Cached data should contain 'cache_info' field"
+
+text_preview = cached_data['text'][:50] if len(cached_data['text']) > 50 else cached_data['text']
+print(f"Retrieved text: {text_preview}...")
+print(f"Original filename: {cached_data['metadata'].get('original_filename')}")
+print(f"Cache hit: {cached_data['cache_info']['cache_hit']}")
-    print(f"Retrieved text: {cached_data['text'][:50]}...")
-    print(f"Original filename: {cached_data['metadata'].get('original_filename')}")
-    print(f"Cache hit: {cached_data['cache_info']['cache_hit']}")
-else:
-    print("Failed to retrieve cached data!")

AuthContext:
Remove debug console.log statements and consider a more robust implementation.

Several issues to address:

Remove or conditionally include the console.log statements for production
The hidden button approach with hardcoded delays (100ms, 5000ms) is fragile
Consider using Google's One Tap or standard button implementation instead
-        console.log('Starting Google sign-in process...');
+        if (import.meta.env.DEV) console.log('Starting Google sign-in process...');
         
         const initializeGoogleAuth = async () => {
           // Load Google Sign-In script if not already loaded
           if (!window.google) {
-            console.log('Loading Google script...');
+            if (import.meta.env.DEV) console.log('Loading Google script...');
             await loadGoogleScript();
           }

-          console.log('Initializing Google ID...');
-          console.log('Google Client ID:', import.meta.env.VITE_GOOGLE_CLIENT_ID);
+          if (import.meta.env.DEV) {
+            console.log('Initializing Google ID...');
+            console.log('Google Client ID:', import.meta.env.VITE_GOOGLE_CLIENT_ID);
+          }
Consider using Google's standard button rendering without the programmatic click approach for better reliability.

Clean up console.log statements and add response validation.

The error handling is good, but the extensive logging should be conditional for production use.

   const handleGoogleSignIn = async (response: { credential: string; select_by: string }) => {
-    console.log('Google sign-in response received:', response);
+    if (import.meta.env.DEV) console.log('Google sign-in response received:', response);
     try {
-      console.log('Sending request to backend:', `${API_BASE_URL}/auth/google`);
+      if (import.meta.env.DEV) console.log('Sending request to backend:', `${API_BASE_URL}/auth/google`);
       
       // Send Google token to our backend
       const backendResponse = await fetch(`${API_BASE_URL}/auth/google`, {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
         },
         body: JSON.stringify({
           token: response.credential,
         }),
       });

-      console.log('Backend response status:', backendResponse.status);
+      if (import.meta.env.DEV) console.log('Backend response status:', backendResponse.status);
       
       if (!backendResponse.ok) {
         const errorText = await backendResponse.text();
-        console.error('Backend error response:', errorText);
+        if (import.meta.env.DEV) console.error('Backend error response:', errorText);
         throw new Error(`Backend authentication failed: ${backendResponse.status} ${errorText}`);
       }

+      // Validate response is JSON
+      const contentType = backendResponse.headers.get('content-type');
+      if (!contentType || !contentType.includes('application/json')) {
+        throw new Error('Invalid response format from backend');
+      }

       const data = await backendResponse.json();

AWS_SETUP_GUIDE:
Tighten IAM permissions – avoid AmazonS3FullAccess

AmazonS3FullAccess grants account-wide S3 admin rights.
Create a bucket-scoped least-privilege policy (s3:PutObject, s3:GetObject, s3:DeleteObject, s3:ListBucket on arn:aws:s3:::studymate-prod-storage/*) and attach that instead.

-   - Search for and select: `AmazonS3FullAccess`
+   - Click **“Create policy”** (JSON) and add a least-privilege policy limited to
+     the StudyMate bucket.  
+   - Attach the new policy to `studymate-s3-user`.

CORS config is overly permissive

Allowing * headers and destructive methods (DELETE, PUT, HEAD) invites abuse. Narrow to the exact methods and headers your front-end needs (usually GET, POST, optional PUT, and Content-Type).

-        "AllowedHeaders": ["*"],
-        "AllowedMethods": ["GET","PUT","POST","DELETE","HEAD"],
+        "AllowedHeaders": ["Content-Type","Authorization"],
+        "AllowedMethods": ["GET","POST","PUT"],

quick_test:
hash2 is calculated but never used – likely copy/paste oversight.

hash2 is generated on L30 but path2 is built with hash1 again (L32).
Either drop hash2 or pass it to get_user_storage_path; otherwise the intent of verifying “same hash, different paths” is obscured.

-    hash2 = auth.get_user_content_hash("user2", content)
+    hash2 = auth.get_user_content_hash("user2", content)

-    path2 = auth.get_user_storage_path("user2", hash1, "cache")
+    path2 = auth.get_user_storage_path("user2", hash2, "cache")

Test always reports success even if the invariant fails.

printing the comparison without asserting it means the function returns True even when the hashes differ or the paths are identical. Add explicit checks so the quick test actually fails when expectations aren’t met.

-    print(
-        f"✓ Hybrid sharing: Same hash ({hash1 == hash2}), Different paths ({path1 != path2})"
-    )
+    assert hash1 == hash2, "Content hash mismatch for identical payloads"
+    assert path1 != path2, "Storage path should vary per-user"
+    print("✓ Hybrid sharing: Same hash, different paths")

auth:
Security: Improve JWT secret key management

Using the API key as JWT secret and hardcoded fallback value presents security risks:

API keys and JWT secrets serve different purposes and should be separate
The hardcoded fallback "dev-jwt-secret-key" could accidentally be used in production
 def _get_jwt_secret(self) -> str:
     """Get JWT secret key for token signing"""
-    # Use API key as JWT secret (it's already secure)
-    return self.settings.api_key or "dev-jwt-secret-key"
+    # JWT secret should be a separate configuration
+    jwt_secret = os.environ.get("JWT_SECRET_KEY") or self.settings.jwt_secret
+    if not jwt_secret:
+        raise ValueError("JWT_SECRET_KEY must be configured for production")
+    return jwt_secret
Consider adding a dedicated JWT secret configuration to your Settings class.

Use timezone-aware datetime for JWT timestamps

datetime.utcnow() is deprecated. Use timezone-aware datetime for better compatibility and future-proofing.

-            "iat": datetime.utcnow(),
-            "exp": datetime.utcnow() + timedelta(hours=self.token_expire_hours),
+            "iat": datetime.now(timezone.utc),
+            "exp": datetime.now(timezone.utc) + timedelta(hours=self.token_expire_hours),
Also add the import:

-from datetime import datetime, timedelta
+from datetime import datetime, timedelta, timezone

MVP_PROGRESS_REPORT:
Google + API has been shut down—use People API instead

The checklist still references enabling the “Google+ API”. Google shut this API down years ago; current OAuth workflows require the Google People API (or no additional API at all when using the standard “Google Identity” OAuth consent screen). Update the bullet accordingly to prevent new integrators from following outdated steps.

- Enable Google+ API
+ Enable Google People API (required for OAuth2 scopes)

test_s3_connection:
Fix the path manipulation to correctly reference the backend root directory.

The current path manipulation gets the parent of the test file (backend/tests/), but the comment indicates it should add the backend root directory. This will likely cause import failures since the modules are expected to be imported from the backend root.

# Add the backend directory to the path so we can import our modules
-backend_dir = Path(__file__).parent
+backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

test_system_integration:
Fix the path manipulation to correctly reference the backend directory.

The current path manipulation adds backend/tests/ to the path instead of the backend directory. Since this file is located at backend/tests/integration/test_system_integration.py, using .parent only goes up one level to backend/tests/.

Apply this fix to correctly reference the backend directory:

-# Add the backend directory to the path
-backend_dir = Path(__file__).parent
-sys.path.insert(0, str(backend_dir))
+# Add the backend directory to the path
+backend_dir = Path(__file__).parent.parent.parent
+sys.path.insert(0, str(backend_dir))

package.json:
google-auth-library is Node-only → will break in the browser

google-auth-library depends on core Node modules (http, https, crypto, etc.) and is meant for server-side OAuth flows. Bundling it in a Vite/React front-end will:

• Inflate the bundle dramatically (hundreds of kB)
• Trigger polyfill warnings or crash at runtime (window.process is undefined)

Replace it with a browser-safe variant such as Google Identity Services (@react-oauth/google, @google/identity-services, or the Google One-Tap JS snippet).

-    "google-auth-library": "^10.1.0",
+    "@react-oauth/google": "^0.8.0"
and adapt the auth flow accordingly.

test_app_startup:
