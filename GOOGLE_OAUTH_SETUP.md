# Google OAuth Setup Guide for Firmament

This guide will help you set up Google OAuth authentication for user login.

## Prerequisites
- Google account
- Google Cloud Console access

## Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console**: Visit [console.cloud.google.com](https://console.cloud.google.com)
2. **Create a new project**:
   - Click "Select a project" dropdown → "New Project"
   - Project name: `Firmament`
   - Leave organization blank (or select if you have one)
   - Click "Create"

## Step 2: Enable Google People API

1. **Navigate to APIs & Services**:
   - In the sidebar, click "APIs & Services" → "Library"
2. **Search for Google People API**:
   - Search for "People API" or "Google People API"
   - Click on "Google People API"
   - Click "Enable"

## Step 3: Configure OAuth Consent Screen

1. **Go to OAuth consent screen**:
   - Sidebar → "APIs & Services" → "OAuth consent screen"
2. **Choose User Type**:
   - Select "External" (for public app)
   - Click "Create"
3. **Fill in App Information**:
   - App name: `Firmament`
   - User support email: Your email
   - Developer contact email: Your email
   - App logo: (optional)
4. **Add scopes** (click "Add or Remove Scopes"):
   - `email`
   - `profile`
   - `openid`
5. **Test users** (for development):
   - Add your email address as a test user
6. **Review and submit**

## Step 4: Create OAuth 2.0 Credentials

1. **Go to Credentials**:
   - Sidebar → "APIs & Services" → "Credentials"
2. **Create credentials**:
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. **Configure the OAuth client**:
   - Application type: "Web application"
   - Name: `Firmament Web Client`
4. **Add Authorized JavaScript origins**:
   - For development: `http://localhost:5173`
   - For production: `https://your-production-domain.com`
5. **Add Authorized redirect URIs**:
   - For development: `http://localhost:5173/auth/callback`
   - For production: `https://your-production-domain.com/auth/callback`
6. **Create the client**

## Step 5: Save Your Credentials

After creating the OAuth client, you'll see:
- **Client ID**: `1234567890-abcdefghijk.apps.googleusercontent.com`
- **Client Secret**: `GOCSPX-abcdefghijklmnop`

⚠️ **Important**: Save these securely! You'll need them for your environment variables.

## Step 6: Update Environment Variables

Add the credentials to your `.env.production` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=1234567890-abcdefghijk.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnop
```

## Step 7: Frontend Integration

### Install Google OAuth Library
In your frontend project:
```bash
npm install @google-cloud/local-auth google-auth-library
# or
npm install react-google-login  # for React
```

### Basic Implementation (React)
```javascript
import { GoogleLogin } from 'react-google-login';

const GoogleAuthButton = () => {
  const handleSuccess = async (response) => {
    // Send the token to your backend
    const result = await fetch('/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: response.tokenId })
    });
    
    const data = await result.json();
    if (data.success) {
      // Store the session token
      localStorage.setItem('sessionToken', data.session_token);
      // Redirect to main app
    }
  };

  return (
    <GoogleLogin
      clientId="your-google-client-id"
      buttonText="Login with Google"
      onSuccess={handleSuccess}
      onFailure={(error) => console.error('Login failed:', error)}
      cookiePolicy={'single_host_origin'}
    />
  );
};
```

## Step 8: Test the Integration

1. **Start your backend**: `python main.py`
2. **Start your frontend**: `npm run dev`
3. **Test the login flow**:
   - Click the Google login button
   - Authorize the app
   - Check that you receive a session token
   - Verify you can access protected routes

## Step 9: Production Configuration

### Update OAuth Settings for Production
1. **Go back to Google Cloud Console**
2. **Update Authorized origins and redirect URIs**:
   - Replace localhost URLs with your production domain
   - Example: `https://firmament.com`

### Environment Variables for Production
```bash
# Production Google OAuth
GOOGLE_CLIENT_ID=your-production-client-id
GOOGLE_CLIENT_SECRET=your-production-client-secret
```

## Security Best Practices

1. **Never expose client secret** in frontend code
2. **Use HTTPS** in production for OAuth redirects
3. **Validate tokens** on the backend before creating sessions
4. **Set appropriate token expiration** times
5. **Log authentication events** for monitoring

## Troubleshooting

### Common Issues

1. **"Invalid client" error**:
   - Check that your client ID is correct
   - Verify your domain is in authorized origins

2. **"Redirect URI mismatch"**:
   - Ensure your redirect URI exactly matches what's configured
   - Check for trailing slashes and protocol (http vs https)

3. **"Access blocked" error**:
   - Your app needs to be verified for public use
   - Add your email as a test user for development

4. **Token verification fails**:
   - Check that your backend has the correct client ID
   - Ensure system time is synchronized

### Getting Help
- Google OAuth Documentation: [developers.google.com/identity/protocols/oauth2](https://developers.google.com/identity/protocols/oauth2)
- Google Cloud Console Support: Available in the console

## Testing Checklist

- [ ] Google Cloud project created
- [ ] OAuth consent screen configured
- [ ] OAuth 2.0 credentials created
- [ ] Environment variables updated
- [ ] Frontend integration implemented
- [ ] Login flow tested
- [ ] Protected routes work with authentication
- [ ] Production domains configured

## Cost Information

Google OAuth is **free** for most use cases:
- No cost for basic authentication
- Rate limits are generous for typical applications
- Only enterprise features have costs

Perfect for MVP and small to medium applications!
