# Authentication System Implementation

This document describes the authentication system implemented for the PurposePath Admin Portal.

## Overview

The authentication system uses Google OAuth 2.0 with PKCE (Proof Key for Code Exchange) flow to ensure secure authentication. Only users who are members of the "Portal Admins" group in the PurposePath.ai Google Workspace can access the admin portal.

## Components

### Services

#### `authService.ts`
- **Purpose**: Core authentication service handling OAuth flow
- **Key Features**:
  - Google OAuth PKCE flow implementation
  - Token management (storage, refresh, validation)
  - Portal Admins group membership validation via backend
  - Session management with automatic expiration handling

#### `sessionManager.ts`
- **Purpose**: Manages user sessions and automatic token refresh
- **Key Features**:
  - Automatic token refresh before expiration (5-minute threshold)
  - Inactivity monitoring (30-minute timeout)
  - Automatic logout on session expiration or inactivity

#### `apiClient.ts`
- **Purpose**: Axios HTTP client with authentication interceptors
- **Key Features**:
  - Automatic token attachment to requests
  - Token refresh on 401 responses
  - Request retry logic with exponential backoff
  - Comprehensive error handling and classification

### UI Components

#### `LoginPage.tsx`
- Google OAuth login button
- Error and info message display
- Logout reason handling (inactivity, expiration)

#### `AuthCallbackPage.tsx`
- Handles OAuth callback from Google
- Processes authorization code exchange
- Error handling and retry logic

#### `AuthGuard.tsx`
- Higher-order component for route protection
- Validates authentication status
- Redirects to login if not authenticated
- Manages session lifecycle

#### `UnauthorizedPage.tsx`
- Displays when user is not in Portal Admins group
- Clear messaging about access requirements

### Utilities

#### `storage.ts`
- Secure token storage using localStorage and sessionStorage
- PKCE flow state management
- Token expiration checking

#### `pkce.ts`
- PKCE code verifier and challenge generation
- SHA-256 hashing
- Base64 URL encoding

## Authentication Flow

### 1. Login Initiation
```
User clicks "Sign in with Google"
  → Generate PKCE pair (verifier + challenge)
  → Generate state for CSRF protection
  → Store verifier and state in sessionStorage
  → Redirect to Google OAuth
```

### 2. OAuth Callback
```
Google redirects back with code and state
  → Verify state matches stored value
  → Exchange code for tokens using verifier
  → Get user info from Google
  → Validate with backend (Portal Admins check)
  → Store tokens and user info
  → Redirect to dashboard
```

### 3. Session Management
```
On authenticated page load:
  → Start session manager
  → Monitor token expiration
  → Auto-refresh tokens when needed
  → Monitor user inactivity
  → Auto-logout after 30 minutes inactivity
```

### 4. API Requests
```
Every API request:
  → Attach access token to Authorization header
  → If 401 response, attempt token refresh
  → Retry original request with new token
  → If refresh fails, logout and redirect to login
```

## Configuration

### Environment Variables
Required in `.env` file:

```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_GOOGLE_REDIRECT_URI=http://localhost:5173/auth/callback
VITE_API_BASE_URL=https://api.purposepath.ai
VITE_AI_API_BASE_URL=https://ai.purposepath.ai
```

### Backend Requirements

The backend must implement the following endpoint:

**POST /auth/validate**
- Request body: `{ googleAccessToken: string, email: string }`
- Response: `{ success: boolean, data: AdminUser }`
- Validates Portal Admins group membership
- Returns 403 if user is not authorized

## Security Features

1. **PKCE Flow**: Prevents authorization code interception attacks
2. **State Parameter**: CSRF protection for OAuth flow
3. **Secure Storage**: Tokens stored in localStorage (consider httpOnly cookies for production)
4. **Automatic Token Refresh**: Reduces exposure window for access tokens
5. **Inactivity Timeout**: Automatic logout after 30 minutes of inactivity
6. **Request Retry Logic**: Handles transient network errors gracefully
7. **Error Classification**: Proper error handling for different failure scenarios

## Usage

### Protecting Routes
```tsx
import { AuthGuard } from './components/features/auth';

<Route
  path="/protected"
  element={
    <AuthGuard>
      <ProtectedComponent />
    </AuthGuard>
  }
/>
```

### Using API Client
```tsx
import { apiClient } from './services/apiClient';

// Tokens are automatically attached
const response = await apiClient.get('/admin/subscribers');
```

### Using React Query Hook
```tsx
import { useApiQuery } from './hooks/useApi';

const { data, isLoading, error } = useApiQuery(
  ['subscribers'],
  '/admin/subscribers'
);
```

### Getting Current User
```tsx
import { authService } from './services/authService';

const user = authService.getCurrentUser();
```

### Manual Logout
```tsx
import { authService } from './services/authService';

authService.logout();
navigate('/login');
```

## Error Handling

The system handles various error scenarios:

- **Network Errors**: Retry with exponential backoff
- **401 Unauthorized**: Attempt token refresh, logout if fails
- **403 Forbidden**: Display unauthorized message
- **Token Expiration**: Automatic refresh or redirect to login
- **Inactivity**: Automatic logout with reason message
- **Invalid OAuth State**: Security error, restart login flow

## Testing

To test the authentication system:

1. Start the development server: `npm run dev`
2. Navigate to `http://localhost:5173`
3. Click "Sign in with Google"
4. Complete Google OAuth flow
5. Backend should validate Portal Admins membership
6. On success, redirect to dashboard
7. On failure, show unauthorized page

## Future Enhancements

1. **HttpOnly Cookies**: Move token storage to httpOnly cookies for better security
2. **Remember Me**: Optional persistent sessions
3. **Multi-Factor Authentication**: Add MFA support
4. **Role-Based Access**: Different admin roles with varying permissions
5. **Audit Logging**: Log all authentication events
6. **Session Management UI**: View and revoke active sessions
