import secrets
import hashlib
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt, get_org_id
from syncsphere.shared_kernel.infrastructure.logging.logger import get_logger
from syncsphere.identity.infrastructure.documents.developer_api_key_document import DeveloperApiKeyDocument
from bson import ObjectId

router = APIRouter(prefix="/developer-keys", tags=["Developer Keys"])
logger = get_logger("developer_keys_routes")

class CreateApiKeyRequest(BaseModel):
    name: str

class CreateApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    key: str  # Only returned once
    created_at: datetime
    status: str

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    status: str

def get_hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

@router.post("", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    req: CreateApiKeyRequest,
    payload: dict = Depends(verify_jwt),
    org_id: str = Depends(get_org_id)
):
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not found in payload")
    
    # Generate secure random key
    raw_key = f"sk_live_{secrets.token_urlsafe(24)}"
    key_hash = get_hash(raw_key)
    
    doc = DeveloperApiKeyDocument(
        org_id=org_id,
        user_id=user_id,
        name=req.name,
        key_hash=key_hash,
        key_prefix=raw_key[:12],
        status="ACTIVE"
    )
    await doc.insert()
    
    return CreateApiKeyResponse(
        id=str(doc.id),
        name=doc.name,
        key_prefix=doc.key_prefix,
        key=raw_key,
        created_at=doc.created_at,
        status=doc.status
    )

@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    payload: dict = Depends(verify_jwt),
    org_id: str = Depends(get_org_id)
):
    user_id = payload.get("sub")
    keys = await DeveloperApiKeyDocument.find(
        DeveloperApiKeyDocument.org_id == org_id,
        DeveloperApiKeyDocument.user_id == user_id
    ).to_list()
    
    return [
        ApiKeyResponse(
            id=str(k.id),
            name=k.name,
            key_prefix=k.key_prefix,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            expires_at=k.expires_at,
            status=k.status
        )
        for k in keys
    ]

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    payload: dict = Depends(verify_jwt),
    org_id: str = Depends(get_org_id)
):
    user_id = payload.get("sub")
    try:
        oid = ObjectId(key_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid key id")
        
    doc = await DeveloperApiKeyDocument.find_one(
        DeveloperApiKeyDocument.id == oid,
        DeveloperApiKeyDocument.org_id == org_id,
        DeveloperApiKeyDocument.user_id == user_id
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Key not found")
        
    doc.status = "REVOKED"
    await doc.save()
