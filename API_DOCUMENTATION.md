# GitLite VCS API Documentation

**Base URL**: `http://localhost:8000`

**Authentication**: Bearer Token (JWT) in Authorization header

---

## 📋 Table of Contents
1. [Authentication Endpoints](#authentication-endpoints)
2. [Repository Endpoints](#repository-endpoints)
3. [File Management Endpoints](#file-management-endpoints)
4. [Data Models](#data-models)

---

## 🔐 Authentication Endpoints

### 1. Login (Unified)
**POST** `/auth/login`

Automatically handles both signin and signup. If user exists, signs them in. If not, creates a new account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "username": "johndoe",           // Optional, required for new signups
  "full_name": "John Doe"           // Optional
}
```

**Response (200 OK)**:
```json
{
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "full_name": "John Doe",
    "username": "johndoe",
    "created_at": "2025-10-22T10:30:00Z"
  },
  "session": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh-token-string",
    "expires_in": 3600,
    "token_type": "bearer"
  },
  "action": "signin"  // or "signup"
}
```

---

### 2. Sign Out
**POST** `/auth/signout`

🔒 **Requires Authentication**

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response (200 OK)**:
```json
{
  "message": "Successfully signed out"
}
```

---

### 3. Refresh Token
**POST** `/auth/refresh`

**Request Body**:
```json
{
  "refresh_token": "your-refresh-token"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "new-access-token",
  "refresh_token": "new-refresh-token",
  "expires_in": 3600,
  "token_type": "bearer"
}
```

---

### 4. Get Current User
**GET** `/auth/me`

🔒 **Requires Authentication**

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response (200 OK)**:
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "bio": "Developer and tech enthusiast",
  "avatar_url": "https://example.com/avatar.jpg",
  "created_at": "2025-10-22T10:30:00Z"
}
```

---

### 5. Update Profile
**PUT** `/auth/me`

🔒 **Requires Authentication**

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body** (all fields optional):
```json
{
  "username": "newusername",
  "full_name": "New Full Name",
  "bio": "Updated bio",
  "avatar_url": "https://example.com/new-avatar.jpg"
}
```

**Response (200 OK)**:
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "username": "newusername",
  "full_name": "New Full Name",
  "bio": "Updated bio",
  "avatar_url": "https://example.com/new-avatar.jpg"
}
```

---

### 6. Get User by ID
**GET** `/auth/user/{user_id}`

Get public user profile (no authentication required).

**Response (200 OK)**:
```json
{
  "id": "uuid-string",
  "username": "johndoe",
  "full_name": "John Doe",
  "bio": "Developer",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

---

## 📁 Repository Endpoints

### 1. Create Repository
**POST** `/repositories`

🔒 **Requires Authentication**

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "name": "my-project",
  "description": "My awesome project"  // Optional
}
```

**Response (200 OK)**:
```json
{
  "id": 1,
  "name": "my-project",
  "description": "My awesome project",
  "owner_id": "uuid-string",
  "created_at": "2025-10-22T10:30:00Z",
  "updated_at": "2025-10-22T10:30:00Z"
}
```

---

### 2. Get Repository
**GET** `/repositories/{repo_id}`

**Response (200 OK)**:
```json
{
  "id": 1,
  "name": "my-project",
  "description": "My awesome project",
  "owner_id": "uuid-string",
  "created_at": "2025-10-22T10:30:00Z",
  "updated_at": "2025-10-22T10:30:00Z"
}
```

---

### 3. Update Repository
**PUT** `/repositories/{repo_id}`

🔒 **Requires Authentication** (must be owner)

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body** (all fields optional):
```json
{
  "name": "updated-project-name",
  "description": "Updated description"
}
```

**Response (200 OK)**:
```json
{
  "id": 1,
  "name": "updated-project-name",
  "description": "Updated description",
  "owner_id": "uuid-string",
  "created_at": "2025-10-22T10:30:00Z",
  "updated_at": "2025-10-22T11:00:00Z"
}
```

---

### 4. Delete Repository
**DELETE** `/repositories/{repo_id}`

🔒 **Requires Authentication** (must be owner)

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response (200 OK)**:
```json
{
  "message": "Repository deleted successfully"
}
```

---

### 5. Get Repository Stats
**GET** `/repositories/{repo_id}/stats`

**Response (200 OK)**:
```json
{
  "total_files": 42,
  "total_size": 1048576,
  "total_versions": 156,
  "last_activity": "2025-10-22T15:45:00Z"
}
```

---

### 6. Get Repository Activity
**GET** `/repositories/{repo_id}/activity?limit=20`

**Query Parameters**:
- `limit` (optional, default: 20): Number of recent activities to return

**Response (200 OK)**:
```json
[
  {
    "file_id": 5,
    "filename": "main.py",
    "version_number": 3,
    "commit_message": "Fixed bug in authentication",
    "created_at": "2025-10-22T15:45:00Z"
  },
  {
    "file_id": 7,
    "filename": "README.md",
    "version_number": 2,
    "commit_message": "Updated documentation",
    "created_at": "2025-10-22T14:30:00Z"
  }
]
```

---

### 7. Compare Repository States
**POST** `/repositories/{repo_id}/compare`

Compare repository states between two dates.

**Request Body**:
```json
{
  "state1_date": "2025-10-20T10:00:00Z",
  "state2_date": "2025-10-22T10:00:00Z"
}
```

**Response (200 OK)**:
```json
{
  "repository_id": 1,
  "state1_date": "2025-10-20T10:00:00Z",
  "state2_date": "2025-10-22T10:00:00Z",
  "changes": [
    {
      "file_id": 5,
      "filename": "main.py",
      "version_at_state1": 1,
      "version_at_state2": 3
    },
    {
      "file_id": 7,
      "filename": "README.md",
      "version_at_state1": null,
      "version_at_state2": 2
    }
  ]
}
```

---

## 📄 File Management Endpoints

### 1. Create File
**POST** `/repositories/{repo_id}/files`

**Request Body**:
```json
{
  "filename": "main.py",
  "content_text": "print('Hello World')",  // For text files
  "content_binary": null,                   // For binary files (base64)
  "commit_message": "Initial commit",       // Optional
  "mime_type": "text/plain"                 // Optional, default: text/plain
}
```

**Response (200 OK)**:
```json
{
  "id": 5,
  "repository_id": 1,
  "filename": "main.py",
  "created_at": "2025-10-22T10:30:00Z",
  "updated_at": "2025-10-22T10:30:00Z",
  "current_version": 1
}
```

---

### 2. List Files in Repository
**GET** `/repositories/{repo_id}/files`

**Response (200 OK)**:
```json
[
  {
    "id": 5,
    "repository_id": 1,
    "filename": "main.py",
    "created_at": "2025-10-22T10:30:00Z",
    "updated_at": "2025-10-22T15:45:00Z",
    "current_version": 3
  },
  {
    "id": 7,
    "repository_id": 1,
    "filename": "README.md",
    "created_at": "2025-10-22T11:00:00Z",
    "updated_at": "2025-10-22T14:30:00Z",
    "current_version": 2
  }
]
```

---

### 3. Get File Details
**GET** `/repositories/{repo_id}/files/{file_id}`

**Response (200 OK)**:
```json
{
  "id": 5,
  "repository_id": 1,
  "filename": "main.py",
  "created_at": "2025-10-22T10:30:00Z",
  "updated_at": "2025-10-22T15:45:00Z",
  "current_version": 3,
  "content_text": "print('Hello World')\nprint('Version 3')",
  "content_binary": null,
  "mime_type": "text/plain",
  "file_size": 45
}
```

---

### 4. Update File
**PUT** `/repositories/{repo_id}/files/{file_id}`

Creates a new version of the file.

**Request Body**:
```json
{
  "content_text": "print('Updated code')",  // For text files
  "content_binary": null,                    // For binary files
  "commit_message": "Updated implementation"
}
```

**Response (200 OK)**:
```json
{
  "id": 5,
  "repository_id": 1,
  "filename": "main.py",
  "created_at": "2025-10-22T10:30:00Z",
  "updated_at": "2025-10-22T16:00:00Z",
  "current_version": 4,
  "content_text": "print('Updated code')",
  "content_binary": null,
  "mime_type": "text/plain",
  "file_size": 21
}
```

---

### 5. Delete File
**DELETE** `/repositories/{repo_id}/files/{file_id}`

**Response (200 OK)**:
```json
{
  "message": "File deleted successfully"
}
```

---

### 6. List File Versions
**GET** `/repositories/{repo_id}/files/{file_id}/versions`

**Response (200 OK)**:
```json
[
  {
    "id": 15,
    "file_id": 5,
    "version_number": 3,
    "parent_version_id": 14,
    "created_at": "2025-10-22T15:45:00Z",
    "commit_message": "Fixed bug",
    "content_hash": "sha256-hash",
    "file_size": 45,
    "mime_type": "text/plain"
  },
  {
    "id": 14,
    "file_id": 5,
    "version_number": 2,
    "parent_version_id": 13,
    "created_at": "2025-10-22T14:00:00Z",
    "commit_message": "Added feature",
    "content_hash": "sha256-hash",
    "file_size": 38,
    "mime_type": "text/plain"
  },
  {
    "id": 13,
    "file_id": 5,
    "version_number": 1,
    "parent_version_id": null,
    "created_at": "2025-10-22T10:30:00Z",
    "commit_message": "Initial commit",
    "content_hash": "sha256-hash",
    "file_size": 20,
    "mime_type": "text/plain"
  }
]
```

---

### 7. Get Specific File Version
**GET** `/repositories/{repo_id}/files/{file_id}/versions/{version}`

**Response (200 OK)**:
```json
{
  "id": 14,
  "file_id": 5,
  "version_number": 2,
  "parent_version_id": 13,
  "created_at": "2025-10-22T14:00:00Z",
  "commit_message": "Added feature",
  "content_hash": "sha256-hash",
  "file_size": 38,
  "mime_type": "text/plain",
  "content_text": "print('Hello World')\nprint('New feature')",
  "content_binary": null
}
```

---

### 8. Compare File Versions (Diff)
**GET** `/repositories/{repo_id}/files/{file_id}/diff/{v1}/{v2}`

**Response (200 OK)**:
```json
{
  "file_id": 5,
  "filename": "main.py",
  "version1": 1,
  "version2": 3,
  "diff": "--- Version 1\n+++ Version 3\n@@ -1 +1,2 @@\n print('Hello World')\n+print('Version 3')"
}
```

---

## 📊 Data Models

### UserSignUp / Login Request
```typescript
{
  email: string;           // Valid email format
  password: string;        // Min 6 characters
  username?: string;       // Optional
  full_name?: string;      // Optional
}
```

### UserResponse
```typescript
{
  id: string;              // UUID
  email: string;
  username?: string;
  full_name?: string;
  bio?: string;
  avatar_url?: string;
  created_at: string;      // ISO 8601 datetime
}
```

### TokenResponse
```typescript
{
  access_token: string;
  token_type: string;      // "bearer"
  expires_in: number;      // Seconds
  refresh_token: string;
  user: UserResponse;
}
```

### RepositoryCreate
```typescript
{
  name: string;
  description?: string;
}
```

### RepositoryResponse
```typescript
{
  id: number;
  name: string;
  description?: string;
  owner_id: string;        // UUID
  created_at: string;      // ISO 8601 datetime
  updated_at: string;      // ISO 8601 datetime
}
```

### FileCreate
```typescript
{
  filename: string;
  content_text?: string;   // For text files
  content_binary?: bytes;  // For binary files
  commit_message?: string;
  mime_type?: string;      // Default: "text/plain"
}
```

### FileResponse
```typescript
{
  id: number;
  repository_id: number;
  filename: string;
  created_at: string;
  updated_at: string;
  current_version: number;
}
```

### FileDetailResponse
```typescript
{
  id: number;
  repository_id: number;
  filename: string;
  created_at: string;
  updated_at: string;
  current_version: number;
  content_text?: string;
  content_binary?: bytes;
  mime_type?: string;
  file_size?: number;
}
```

### FileVersionResponse
```typescript
{
  id: number;
  file_id: number;
  version_number: number;
  parent_version_id?: number;
  created_at: string;
  commit_message?: string;
  content_hash?: string;
  file_size?: number;
  mime_type?: string;
}
```

### RepositoryStats
```typescript
{
  total_files: number;
  total_size: number;       // Bytes
  total_versions: number;
  last_activity?: string;   // ISO 8601 datetime
}
```

### ActivityItem
```typescript
{
  file_id: number;
  filename: string;
  version_number: number;
  commit_message?: string;
  created_at: string;
}
```

---

## 🔑 Authentication Flow

1. **Login**: `POST /auth/login` → Get `access_token`
2. **Use Token**: Add header `Authorization: Bearer <access_token>` to protected endpoints
3. **Refresh**: When token expires, use `POST /auth/refresh` with `refresh_token`
4. **Logout**: `POST /auth/signout`

---

## ❌ Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Error message describing what went wrong"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to perform this action"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## 🌐 CORS

CORS is enabled for all origins (`*`). In production, configure specific origins.

---

## 📝 Notes

- All datetime fields use ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`
- Binary content should be base64 encoded
- File size is in bytes
- Authentication tokens expire after 3600 seconds (1 hour)
- Use refresh token to get new access token without re-login

---

## 🚀 Quick Start Example (JavaScript/TypeScript)

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123',
    username: 'johndoe',
    full_name: 'John Doe'
  })
});
const { session } = await loginResponse.json();
const token = session.access_token;

// Create Repository
const repoResponse = await fetch('http://localhost:8000/repositories', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    name: 'my-project',
    description: 'My awesome project'
  })
});
const repo = await repoResponse.json();

// Create File
const fileResponse = await fetch(`http://localhost:8000/repositories/${repo.id}/files`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    filename: 'main.py',
    content_text: 'print("Hello World")',
    commit_message: 'Initial commit'
  })
});
const file = await fileResponse.json();

// Get File Versions
const versionsResponse = await fetch(
  `http://localhost:8000/repositories/${repo.id}/files/${file.id}/versions`,
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);
const versions = await versionsResponse.json();
```

---

**API Version**: 1.0.0  
**Last Updated**: October 22, 2025
