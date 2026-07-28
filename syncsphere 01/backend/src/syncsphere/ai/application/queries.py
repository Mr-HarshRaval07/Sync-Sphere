from typing import Optional
from syncsphere.shared_kernel.types.contracts import BaseQuery

class ListModelsQuery(BaseQuery):
    org_id: str

class GetModelQuery(BaseQuery):
    org_id: str
    model_id: str

class GetPromptQuery(BaseQuery):
    org_id: str
    name: str

class ListProvidersQuery(BaseQuery):
    org_id: str

class GetProviderHealthQuery(BaseQuery):
    org_id: str
    provider_id: str
