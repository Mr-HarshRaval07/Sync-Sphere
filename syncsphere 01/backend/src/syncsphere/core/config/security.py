from pydantic import BaseModel, SecretStr, field_validator

class SecurityConfig(BaseModel):
    """Cryptographic, JWT, and hashing security settings."""
    jwt_secret: SecretStr = SecretStr("supersecretjwtkeythatisthirtytwobyteslongtobesecure")
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl: int = 900
    jwt_refresh_token_ttl: int = 604800
    
    # 32-byte url-safe base64 key
    master_encryption_key: SecretStr = SecretStr("z7pQYv_3e8q56_u-j-2W1S3K6L8_9x1v_3e8q56_u-I=")

    @field_validator("master_encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: SecretStr) -> SecretStr:
        val = v.get_secret_value()
        if val and len(val) < 32:
            raise ValueError("Master encryption key must be at least 32 characters long.")
        return v
