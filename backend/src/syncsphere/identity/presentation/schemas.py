from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# ==============================================================================
# Authentication Schemas
# ==============================================================================
class UserPreferencesSchema(BaseModel):
    default_google_sheets_id: Optional[str] = None
    default_notion_db_id: Optional[str] = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    org_name: str = Field(..., min_length=2)
    org_slug: str = Field(..., min_length=2)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900

# ==============================================================================
# User & Profile Schemas
# ==============================================================================
class UserResponse(BaseModel):
    id: str
    org_id: str
    email: str
    first_name: str
    last_name: str
    role_ids: List[str]
    status: str
    preferences: Optional[UserPreferencesSchema] = None
    created_at: datetime
    updated_at: datetime

class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1)
    last_name: Optional[str] = Field(None, min_length=1)
    preferences: Optional[UserPreferencesSchema] = None

class InviteUserRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role_ids: List[str]

class UpdateUserRequest(BaseModel):
    role_ids: Optional[List[str]] = None
    status: Optional[str] = None

# ==============================================================================
# Organization Schemas
# ==============================================================================
class OrgResponse(BaseModel):
    id: str
    name: str
    slug: str
    billing_tier: str
    quotas: dict
    feature_flags: dict

# ==============================================================================
# Role & Permission Schemas
# ==============================================================================
class PermissionSchema(BaseModel):
    resource_type: str
    resource_id: str = "*"
    actions: List[str]

class CreateRoleRequest(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = ""
    permissions: List[PermissionSchema]

class RoleResponse(BaseModel):
    id: str
    org_id: str
    name: str
    description: str
    is_system_role: bool
    permissions: List[PermissionSchema]

class AssignRoleRequest(BaseModel):
    role_id: str

# ==============================================================================
# API Key Schemas
# ==============================================================================
class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1)
    scopes: List[str]
    expires_in_days: Optional[int] = None

class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    raw_key: str
    key_prefix: str
    scopes: List[str]
    expires_at: Optional[datetime]

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: List[str]
    expires_at: Optional[datetime]
    status: str
