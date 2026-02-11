# Authentication Service Integration Guide

## Service Overview
- **Service Name**: Authentication Service
- **Base URL**: External Google OAuth + Internal validation
- **Primary File**: `src/services/authService.ts`
- **Hook File**: N/A (uses direct service calls)
- **Authentication**: Google OAuth 2.0 with PKCE
- **Error Handling**: Built-in token refresh and session management

## Endpoints Reference

### 1. Google OAuth Initiation (External)
```
Method: GET
URL: https://accounts.google.com/o/oauth2/v2/auth
Type: External API
Authentication: None (public endpoint)
```

**Query Parameters:**
```typescript
{
  client_id: string;           // Google OAuth client ID
  redirect_uri: string;        // Callback URL
  response_type: "code";       // Fixed value
  scope: "openid email profile"; // Fixed scope
  state: string;              // CSRF protection token
  code_challenge: string;      // PKCE challenge
  code_challenge_method: "S256"; // Fixed method
  access_type: "offline";      // Fixed value
  prompt: "consent";          // Fixed value
}
```

**Response:**
- Redirects to `redirect_uri` with authorization code and state

### 2. Token Exchange (External)
```
Method: POST
URL: https://oauth2.googleapis.com/token
Type: External API
Authentication: None
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
```typescript
{
  client_id: string;        // Google OAuth client ID
  code: string;             // Authorization code from step 1
  code_verifier: string;    // PKCE verifier
  grant_type: "authorization_code"; // Fixed value
  redirect_uri: string;     // Same as step 1
}
```

**Response:**
```typescript
interface GoogleTokenResponse {
  access_token: string;
  refresh_token?: string;
  expires_in: number;       // Seconds until expiration
  token_type: string;       // Usually "Bearer"
  scope: string;
}
```

### 3. Token Refresh (External)
```
Method: POST
URL: https://oauth2.googleapis.com/token
Type: External API
Authentication: None
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
```typescript
{
  client_id: string;
  refresh_token: string;
  grant_type: "refresh_token"; // Fixed value
}
```

**Response:**
```typescript
interface GoogleTokenResponse {
  access_token: string;
  expires_in: number;
  token_type: string;
  scope: string;
  // Note: refresh_token not included in refresh response
}
```

### 4. Get User Info (External)
```
Method: GET
URL: https://www.googleapis.com/oauth2/v2/userinfo
Type: External API
Authentication: Bearer {google_access_token}
```

**Response:**
```typescript
interface GoogleUserInfo {
  id: string;               // Google user ID
  email: string;            // User email
  verified_email: boolean;  // Email verification status
  name: string;             // Full name
  given_name: string;       // First name
  family_name: string;      // Last name
  picture: string;          // Profile picture URL
}
```

### 5. Admin Validation (Internal)
```
Method: POST
URL: /auth/validate
Type: Internal API
Base URL: {config.apiBaseUrl}
Authentication: None (validation endpoint)
Content-Type: application/json
```

**Request Body:**
```typescript
{
  googleAccessToken: string; // Google access token
  email: string;            // User email from Google
}
```

**Response:**
```typescript
interface ApiResponse<AdminUser> {
  success: boolean;
  data?: AdminUser;
  error?: string;
}

interface AdminUser {
  id: string;
  email: string;
  name: string;
  picture?: string;
  role: "admin";
  permissions: string[];
  createdAt: string;
  lastLoginAt: string;
}
```

**Error Responses:**
- `403 Forbidden`: User not in Portal Admins group
- `400 Bad Request`: Invalid token or missing data
- `500 Internal Server Error`: Server error

## Service Methods

### Core Authentication Methods

#### `initiateGoogleLogin()`
```typescript
async initiateGoogleLogin(): Promise<void>
```
**Purpose**: Starts Google OAuth flow with PKCE
**Side Effects**: 
- Generates and stores PKCE verifier and state
- Redirects browser to Google OAuth
**Error Handling**: Throws Error on PKCE generation failure

#### `handleOAuthCallback(code: string, state: string)`
```typescript
async handleOAuthCallback(code: string, state: string): Promise<AdminUser>
```
**Purpose**: Handles OAuth callback and validates admin user
**Parameters**:
- `code`: Authorization code from Google
- `state`: CSRF state parameter
**Returns**: AdminUser object
**Side Effects**: Stores tokens and user info in localStorage
**Error Handling**: 
- Validates state parameter
- Throws Error on invalid state, missing verifier, or non-admin user

#### `refreshAccessToken()`
```typescript
async refreshAccessToken(): Promise<AuthTokens>
```
**Purpose**: Refreshes expired access token
**Returns**: New token data
**Side Effects**: Updates stored tokens
**Error Handling**: Clears auth and throws on refresh failure

### Utility Methods

#### `isAuthenticated()`
```typescript
isAuthenticated(): boolean
```
**Purpose**: Check if user is currently authenticated
**Logic**: Checks for stored tokens and expiration

#### `getCurrentUser()`
```typescript
getCurrentUser(): AdminUser | null
```
**Purpose**: Get current authenticated user
**Returns**: User object or null if not authenticated

#### `getAccessToken()`
```typescript
getAccessToken(): string | null
```
**Purpose**: Get current access token
**Returns**: Token string or null

#### `logout()`
```typescript
logout(): void
```
**Purpose**: Clear all authentication data
**Side Effects**: Removes all stored auth data

#### `needsTokenRefresh(thresholdMs?: number)`
```typescript
needsTokenRefresh(thresholdMs = 5 * 60 * 1000): boolean
```
**Purpose**: Check if token needs refresh
**Default Threshold**: 5 minutes before expiration

## Storage Management

### LocalStorage Keys
```typescript
const STORAGE_KEYS = {
  ACCESS_TOKEN: 'auth_access_token',
  REFRESH_TOKEN: 'auth_refresh_token',
  TOKEN_EXPIRY: 'auth_token_expiry',
  USER_INFO: 'auth_user_info'
};
```

### SessionStorage Keys (OAuth Flow)
```typescript
const SESSION_KEYS = {
  CODE_VERIFIER: 'oauth_code_verifier',
  OAUTH_STATE: 'oauth_state'
};
```

## Configuration

### Environment Variables
```typescript
interface AuthConfig {
  googleClientId: string;     // VITE_GOOGLE_CLIENT_ID
  googleRedirectUri: string;  // VITE_GOOGLE_REDIRECT_URI
  apiBaseUrl: string;        // VITE_API_BASE_URL
}
```

### Default Values
```typescript
const defaults = {
  googleRedirectUri: 'http://localhost:5173/auth/callback',
  apiBaseUrl: 'https://api.dev.purposepath.app/admin/api/v1'
};
```

## Integration Examples

### Basic Authentication Check
```typescript
import { authService } from '@/services/authService';

// Check if user is authenticated
if (!authService.isAuthenticated()) {
  // Redirect to login
  window.location.href = '/login';
  return;
}

// Get current user
const user = authService.getCurrentUser();
console.log('Current user:', user?.email);
```

### Handling Login
```typescript
import { authService } from '@/services/authService';

const handleLogin = async () => {
  try {
    await authService.initiateGoogleLogin();
    // Browser will redirect to Google
  } catch (error) {
    console.error('Login failed:', error);
  }
};
```

### Handling OAuth Callback
```typescript
import { authService } from '@/services/authService';
import { useSearchParams } from 'react-router-dom';

const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  
  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');
        
        if (error) {
          throw new Error(`OAuth error: ${error}`);
        }
        
        if (!code || !state) {
          throw new Error('Missing authorization code or state');
        }
        
        const user = await authService.handleOAuthCallback(code, state);
        navigate('/dashboard');
      } catch (error) {
        console.error('Callback failed:', error);
        navigate('/login?error=callback_failed');
      }
    };
    
    handleCallback();
  }, []);
  
  return <div>Processing login...</div>;
};
```

### Manual Token Refresh
```typescript
import { authService } from '@/services/authService';

const refreshTokenIfNeeded = async () => {
  try {
    if (authService.needsTokenRefresh()) {
      await authService.refreshAccessToken();
      console.log('Token refreshed successfully');
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
    // Handle logout
    authService.logout();
    window.location.href = '/login?reason=expired';
  }
};
```

## Error Scenarios & Handling

### Common Error Types
```typescript
enum AuthErrorType {
  INVALID_STATE = 'invalid_state',
  MISSING_VERIFIER = 'missing_verifier',
  TOKEN_EXCHANGE_FAILED = 'token_exchange_failed',
  USER_INFO_FAILED = 'user_info_failed',
  UNAUTHORIZED = 'unauthorized',
  REFRESH_FAILED = 'refresh_failed'
}
```

### Error Handling Patterns
```typescript
try {
  const user = await authService.handleOAuthCallback(code, state);
  // Success
} catch (error) {
  if (error.message.includes('not authorized')) {
    // User not in Portal Admins group
    navigate('/unauthorized');
  } else if (error.message.includes('Invalid state')) {
    // CSRF attack or corrupted flow
    navigate('/login?error=security');
  } else {
    // Generic error
    navigate('/login?error=auth_failed');
  }
}
```

## Security Considerations

### PKCE Implementation
- **Code Verifier**: 128 random bytes, base64url encoded
- **Code Challenge**: SHA256 hash of verifier, base64url encoded
- **Storage**: Verifier stored in sessionStorage (cleared after use)

### State Parameter
- **Generation**: 32 random bytes, base64url encoded
- **Validation**: Must match between auth initiation and callback
- **Storage**: Stored in sessionStorage

### Token Security
- **Access Token**: Short-lived (1 hour typical)
- **Refresh Token**: Long-lived, stored securely
- **Storage**: localStorage (consider httpOnly cookies for production)

### Session Management
- **Inactivity Timeout**: 30 minutes default
- **Token Refresh**: Automatic with 5-minute threshold
- **Logout**: Complete cleanup of all auth data

## Testing Considerations

### Unit Test Coverage
```typescript
// Test authentication state
expect(authService.isAuthenticated()).toBe(false);

// Test token validation
expect(authService.needsTokenRefresh()).toBe(true);

// Test logout cleanup
authService.logout();
expect(authService.getCurrentUser()).toBeNull();
```

### Integration Test Scenarios
1. Complete OAuth flow
2. Token refresh cycle
3. Session expiration handling
4. Error scenario recovery
5. Unauthorized user handling

## Related Files
- `src/services/authService.ts` - Main service implementation
- `src/utils/storage.ts` - Storage utilities
- `src/utils/pkce.ts` - PKCE generation utilities
- `src/components/features/auth/` - Auth components
- `src/pages/LoginPage.tsx` - Login page
- `src/pages/AuthCallbackPage.tsx` - OAuth callback handler
- `src/pages/UnauthorizedPage.tsx` - Unauthorized access page