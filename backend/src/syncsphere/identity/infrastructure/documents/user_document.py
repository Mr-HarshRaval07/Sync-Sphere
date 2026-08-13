from pydantic import BaseModel, Field
from typing import List, Optional
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument
# from syncsphere.identity.infrastructure.documents.user_document import UserDocument
class GitHubConnection(BaseModel):
    """Schema for tracking GitHub OAuth states."""
    connected: bool = Field(default=False, description="Is GitHub connected?")
    github_id: Optional[str] = Field(default=None, description="Unique GitHub internal user ID")
    github_username: Optional[str] = Field(default=None, description="GitHub profile username")
    access_token: Optional[str] = Field(default=None, description="Argon2/AES Encrypted access token string")

class SlackConnection(BaseModel):
    connected: bool = False
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    bot_user_id: Optional[str] = None
    access_token: Optional[str] = None

class UserPreferences(BaseModel):
    default_google_sheets_id: Optional[str] = None
    default_notion_db_id: Optional[str] = None

class UserDocument(BaseTenantDocument):
    """Beanie ODM representation of the User aggregate root."""
    email: str = Field(..., description="Lowercase unique email address")
    password_hash: str = Field(..., description="Secure password argon2 hash")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")
    role_ids: List[str] = Field(default_factory=list, description="Assigned role identifiers list")
    status: str = Field(default="ACTIVE", description="User status: ACTIVE, SUSPENDED, DEACTIVATED")
    
    # New connection field added here
    github: GitHubConnection = Field(default_factory=GitHubConnection, description="User GitHub connector parameters")
    slack: SlackConnection = Field(
        default_factory=SlackConnection,
        description="Slack connector information"
    )
    preferences: UserPreferences = Field(
        default_factory=UserPreferences,
        description="User-specific settings and overrides"
    )

    class Settings:
        name = "users"
        indexes = [
            "org_id",
            "email",
            ("org_id", "email"),
            "status"
        ]