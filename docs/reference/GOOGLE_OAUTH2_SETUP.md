# Google OAuth2 Setup Guide for MATHESIS LAB

## Overview

This guide walks through setting up Google OAuth2 authentication for MATHESIS LAB local development. The implementation supports two OAuth2 flows:

1. **Frontend Google Sign-In (ID Token Flow)** - Recommended for single-page apps
2. **Backend Authorization Code Flow** - For secure backend-to-backend token exchange

## Prerequisites

- Google Cloud Account (free tier works for development)
- Node.js and npm installed
- Python backend running with virtual environment activated
- MATHESIS LAB repository cloned

## Part 1: Google Cloud Console Setup

### Step 1: Create a Google Cloud Project

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Log in with your Google account
3. Click **Create Project** (or select existing project)
4. Enter project name: `MATHESIS-LAB`
5. Click **Create**
6. Wait for project to be created (may take a few seconds)

### Step 2: Enable Google OAuth2 API

1. In the Google Cloud Console, search for **"OAuth consent screen"** in the top search bar
2. Click on **OAuth consent screen** in the results
3. Select **External** as the User Type (for development)
4. Click **Create**
5. Fill in the form:
   - **App name**: MATHESIS LAB
   - **User support email**: Your Google account email
   - **Developer contact**: Your Google account email
6. Click **Save and Continue**
7. On the **Scopes** page, click **Add or Remove Scopes**
8. Search for and add these scopes:
   - `openid`
   - `email`
   - `profile`
9. Click **Update** and then **Save and Continue**
10. On the **Test users** page, click **Add Users** and add your Google account email
11. Click **Save and Continue**, then **Back to Dashboard**

### Step 3: Create OAuth2 Credentials

1. In Google Cloud Console, click **Credentials** in the left sidebar
2. Click **Create Credentials** > **OAuth 2.0 Client ID**
3. If prompted to create OAuth consent screen, you've already done that
4. Select **Web application** as the Application type
5. Enter name: `MATHESIS LAB Frontend`
6. Under **Authorized JavaScript origins**, add:
   ```
   http://localhost:3000
   http://localhost:3002
   ```
7. Under **Authorized redirect URIs**, add:
   ```
   http://localhost:3000/auth/google/callback
   http://localhost:3002/auth/google/callback
   ```
8. Click **Create**
9. Copy the **Client ID** (you'll see a modal with credentials)
10. Click **Download JSON** to save credentials file (save as `google-oauth-credentials.json`)

### Step 4: Store Credentials

The credentials JSON looks like:
```json
{
  "web": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "client_secret": "YOUR_CLIENT_SECRET",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uris": ["http://localhost:3000/auth/google/callback"]
  }
}
```

## Part 2: Backend Environment Configuration

### Step 1: Set Environment Variables

Create or update `.env` file in the `backend/` directory:

```bash
# JWT Configuration
JWT_SECRET_KEY="your-super-secret-jwt-key-change-this-in-production"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth2 Configuration
GOOGLE_OAUTH_CLIENT_ID="YOUR_CLIENT_ID.apps.googleusercontent.com"
GOOGLE_OAUTH_CLIENT_SECRET="YOUR_CLIENT_SECRET"

# Database Configuration
DATABASE_URL="sqlite:///./mathesis_lab.db"

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:3002"]
```

### Step 2: Load Environment Variables

The application uses Pydantic Settings to load from `.env`. Verify `backend/app/core/config.py` includes:

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    google_oauth_client_id: Optional[str] = None
    google_oauth_client_secret: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False
```

## Part 3: Backend Implementation Status

### ✅ Already Implemented

**OAuth2 Handler** (`backend/app/auth/oauth_handler.py`):
- ✅ `verify_id_token()` - Verifies Google ID tokens
- ✅ `extract_user_info()` - Extracts user data from token
- ✅ `get_authorization_url()` - Generates OAuth2 authorization URL
- ✅ `exchange_code_for_token()` - Backend token exchange

**API Endpoints** (`backend/app/api/v1/endpoints/auth.py`):
- ✅ `POST /auth/google/verify-token` - ID token verification (frontend flow)
- ✅ `GET /auth/google/auth-url` - Get authorization URL

**Database Models**:
- ✅ User model with OAuth2 support (password_hash can be null for OAuth users)
- ✅ User fields for profile picture, email verification

### 🚧 Still TODO

**Backend Endpoints**:
- ⬜ `POST /auth/google/callback` - Backend OAuth2 callback handler
- ⬜ `POST /auth/link-oauth` - Link OAuth account to existing user account

**Frontend Implementation**:
- ⬜ Google Sign-In button component
- ⬜ OAuth2 callback page
- ⬜ Environment variable setup (.env.local)

## Part 4: Testing the Setup

### Test 1: Verify Backend OAuth Handler (Unit Test)

```bash
cd /mnt/d/progress/MATHESIS\ LAB
source .venv/bin/activate

# This test verifies GoogleOAuthHandler initialization
python -c "
import os
os.environ['GOOGLE_OAUTH_CLIENT_ID'] = 'test-client-id.apps.googleusercontent.com'

from backend.app.auth.oauth_handler import GoogleOAuthHandler
handler = GoogleOAuthHandler()
print('✅ OAuth handler initialized successfully')

# Test authorization URL generation
url = handler.get_authorization_url(
    redirect_uri='http://localhost:3000/auth/google/callback',
    state='test-state'
)
print(f'✅ Authorization URL generated: {url[:50]}...')
"
```

### Test 2: Verify Environment Variables

```bash
cd backend
source ../.venv/bin/activate

python -c "
from app.core.config import settings
print(f'Google Client ID configured: {bool(settings.google_oauth_client_id)}')
print(f'Google Client Secret configured: {bool(settings.google_oauth_client_secret)}')
"
```

### Test 3: Test API Endpoint

```bash
# Start the backend server (in one terminal)
cd /mnt/d/progress/MATHESIS\ LAB
source .venv/bin/activate
python -m uvicorn backend.app.main:app --reload --port 8000

# In another terminal, test the endpoint
curl "http://localhost:8000/api/v1/auth/google/auth-url?redirect_uri=http://localhost:3000/auth/google/callback"
```

Expected response:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&response_type=code&scope=openid+email+profile"
}
```

## Part 5: Frontend Setup

### Step 1: Create `.env.local` in Frontend

Create `MATHESIS-LAB_FRONT/.env.local`:

```
VITE_API_URL=http://localhost:8000/api/v1
VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
```

### Step 2: Install Google Sign-In SDK

The frontend will use the official Google Sign-In library. Installation is done via HTML script tag in the component.

### Step 3: Create Google Sign-In Button Component

See **Part 6** for detailed implementation.

## Part 6: Frontend Google Sign-In Implementation

### File: `MATHESIS-LAB_FRONT/components/GoogleSignInButton.tsx`

```typescript
import { useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

interface GoogleSignInButtonProps {
  onSuccess?: (response: any) => void;
  onError?: (error: any) => void;
}

export const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onSuccess,
  onError,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Load Google Sign-In SDK
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;

    script.onload = () => {
      if (window.google && containerRef.current) {
        window.google.accounts.id.initialize({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
          callback: handleCredentialResponse,
        });

        window.google.accounts.id.renderButton(
          containerRef.current,
          {
            theme: 'outline',
            size: 'large',
            text: 'signin',
          }
        );
      }
    };

    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  const handleCredentialResponse = useCallback(async (response: any) => {
    try {
      // Send ID token to backend for verification
      const res = await fetch(
        `${import.meta.env.VITE_API_URL}/auth/google/verify-token`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id_token: response.credential }),
        }
      );

      if (!res.ok) {
        throw new Error('Google OAuth verification failed');
      }

      const data = await res.json();

      // Store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);

      onSuccess?.(data);
      navigate('/curriculums');
    } catch (error) {
      console.error('Google Sign-In failed:', error);
      onError?.(error);
    }
  }, [navigate, onSuccess, onError]);

  return (
    <div
      ref={containerRef}
      style={{
        display: 'flex',
        justifyContent: 'center',
        margin: '20px 0',
      }}
    />
  );
};
```

### File: `MATHESIS-LAB_FRONT/pages/GoogleOAuthCallback.tsx`

```typescript
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

export const GoogleOAuthCallback: React.FC = () => {
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');

        if (!code) {
          setError('No authorization code received');
          return;
        }

        // Exchange code for tokens (backend handles this)
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/auth/google/callback`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              code,
              state,
              redirect_uri: window.location.origin + '/auth/google/callback',
            }),
          }
        );

        if (!response.ok) {
          throw new Error('Token exchange failed');
        }

        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);

        navigate('/curriculums');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'OAuth callback failed');
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  if (error) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h2>Authentication Failed</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h2>Processing login...</h2>
      <p>Please wait while we authenticate you.</p>
    </div>
  );
};
```

## Part 7: Complete OAuth2 Flow Diagram

```
Frontend                           Backend                    Google
   |                                  |                          |
   +-- Click "Sign in with Google" -->|                          |
   |                                  +-- GET /auth/google/auth-url
   |                                  |                          |
   |<-- Return auth URL --------------|<-- Authorization URL ----+
   |                                  |                          |
   +-- Redirect to Google ------------|------------------------->|
   |                                  |                          |
   |<-- Google login & consent -------|<------------------------+
   |                                  |                          |
   +-- Receive ID token --------------|                          |
   |                                  |                          |
   +-- POST /auth/google/verify-token |                          |
   |    (with ID token)               |                          |
   |                                  +-- Verify token signature |
   |                                  |    using Google public key
   |                                  |                          |
   |                                  +-- Find or create user    |
   |                                  |                          |
   |                                  +-- Create JWT tokens      |
   |                                  |                          |
   |<-- Return JWT access/refresh ----|                          |
   |                                  |                          |
   +-- Store tokens in localStorage   |                          |
   |                                  |                          |
   +-- Redirect to /curriculums       |                          |
```

## Part 8: Troubleshooting

### Issue: "GOOGLE_OAUTH_CLIENT_ID not set"

**Solution**: Ensure `.env` file exists in `backend/` directory and contains:
```
GOOGLE_OAUTH_CLIENT_ID=your_client_id
```

### Issue: "Token audience does not match client ID"

**Solution**: Verify that:
1. The Client ID in `.env` matches the one from Google Cloud Console
2. The ID token was issued for your app (check `aud` claim in JWT)
3. Whitelist is properly configured in Google Cloud Console

### Issue: "Invalid redirect URI"

**Solution**: Ensure the redirect URI in Google Cloud Console matches exactly:
- Development: `http://localhost:3000/auth/google/callback`
- Production: `https://yourdomain.com/auth/google/callback`

### Issue: "CORS error from Google"

**Solution**:
1. Add localhost origins to Google Cloud Console OAuth credentials
2. Ensure CORS is configured in FastAPI backend:
   ```python
   CORSMiddleware(
       app,
       allow_origins=["http://localhost:3000", "http://localhost:3002"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

## Part 9: Security Best Practices

### 1. Never Commit Credentials

Add to `.gitignore`:
```
backend/.env
backend/.env.local
google-oauth-credentials.json
```

### 2. Use Different Credentials Per Environment

- **Development**: Use `http://localhost` origins
- **Staging**: Use staging domain origins
- **Production**: Use production domain origins

### 3. Rotate Secrets Regularly

1. Delete old OAuth credentials from Google Cloud Console
2. Create new credentials with updated secret
3. Update `.env` files
4. Restart application

### 4. Validate ID Tokens

The backend already validates:
- ✅ Signature (using Google's public keys)
- ✅ Audience (`aud` claim matches client ID)
- ✅ Expiration time (`exp` claim)
- ✅ Issued at (`iat` claim)

### 5. Use HTTPS in Production

Update Google Cloud Console redirect URIs to use `https://` for production deployments.

## Part 10: Next Steps

1. **Obtain Credentials**: Complete Part 1 (Google Cloud Setup)
2. **Configure Backend**: Complete Part 2 (Environment Variables)
3. **Test Backend**: Complete Part 4 (Unit Tests)
4. **Setup Frontend**: Complete Part 5 (Frontend Configuration)
5. **Implement Components**: Complete Part 6 (Google Sign-In Button)
6. **Create Backend Callback**: Implement `POST /auth/google/callback` endpoint
7. **Run Integration Tests**: Test full OAuth2 flow end-to-end
8. **Deploy to GCP**: Use Google Cloud Run for production deployment

## References

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In SDK](https://developers.google.com/identity/gsi/web)
- [Google Cloud Console](https://console.cloud.google.com/)
- [FastAPI + Google OAuth](https://fastapi.tiangolo.com/advanced/security/oauth2-jwt/)
