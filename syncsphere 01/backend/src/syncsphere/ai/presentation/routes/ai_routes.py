import logging
from fastapi import APIRouter, Request, Depends, status
from typing import List, Dict, Any

from syncsphere.shared_kernel.infrastructure.http.responses import ResponseEnvelope, ResponseMeta
from syncsphere.shared_kernel.infrastructure.http.dependencies import verify_jwt
from syncsphere.ai.presentation.schemas import (
    ProviderRegisterRequest,
    ModelRegisterRequest,
    PromptRegisterRequest,
    PromptUpdateRequest,
    ChatGenerationRequest,
    CompletionGenerationRequest,
    EmbeddingGenerationRequest,
    PromptCompilationRequest,
)

logger = logging.getLogger("syncsphere.ai.presentation.routes.ai_routes")

router = APIRouter(prefix="/ai", tags=["AI Infrastructure"])


@router.post(
    "/providers",
    response_model=ResponseEnvelope[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Model Provider"
)
async def register_provider(
    request: Request,
    body: ProviderRegisterRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    # Encrypt the API key before registering it
    api_key_encrypted = ""
    if body.api_key:
        api_key_encrypted = container.secret_provider.encrypt(body.api_key, org_id)

    result = await container.ai_service.register_provider(
        org_id=org_id,
        name=body.name,
        api_key_encrypted=api_key_encrypted,
        api_url_override=body.api_url_override,
        priority_level=body.priority_level,
        config_meta=body.config_meta
    )
    if result.is_fail:
        raise result.error()

    provider = result.value()
    return {
        "data": {
            "id": provider.id,
            "name": provider.name,
            "priority": provider.priority.priority_level,
            "status": provider.status.value
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.post(
    "/models",
    response_model=ResponseEnvelope[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Model under a Provider"
)
async def register_model(
    request: Request,
    body: ModelRegisterRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.ai_service.register_model(
        org_id=org_id,
        provider_id=body.provider_id,
        name=body.name,
        display_name=body.display_name,
        capabilities=body.capabilities,
        context_window=body.context_window,
        max_output_tokens=body.max_output_tokens,
        cost_per_1k_input=body.cost_per_1k_input,
        cost_per_1k_output=body.cost_per_1k_output
    )
    if result.is_fail:
        raise result.error()

    model = result.value()
    return {
        "data": {
            "id": model.id,
            "name": model.name,
            "display_name": model.display_name,
            "status": model.status.value
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.post(
    "/models/{model_id}/enable",
    response_model=ResponseEnvelope[dict],
    summary="Enable an inactive model"
)
async def enable_model(
    request: Request,
    model_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.ai_service.enable_model(org_id, model_id)
    if result.is_fail:
        raise result.error()

    return {
        "data": {"id": model_id, "status": "active"},
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.post(
    "/models/{model_id}/disable",
    response_model=ResponseEnvelope[dict],
    summary="Disable an active model"
)
async def disable_model(
    request: Request,
    model_id: str,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.ai_service.disable_model(org_id, model_id)
    if result.is_fail:
        raise result.error()

    return {
        "data": {"id": model_id, "status": "inactive"},
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.post(
    "/prompts",
    response_model=ResponseEnvelope[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new versioned Prompt Template"
)
async def create_prompt(
    request: Request,
    body: PromptRegisterRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    # Parse variables DTO list
    from syncsphere.ai.domain.value_objects import PromptVariable
    vars_list = [PromptVariable(**v) for v in body.variables]

    result = await container.prompt_service.create_prompt(
        org_id=org_id,
        name=body.name,
        system_template=body.system_template,
        user_template=body.user_template,
        description=body.description,
        variables=vars_list
    )
    if result.is_fail:
        raise result.error()

    prompt = result.value()
    return {
        "data": {
            "id": prompt.id,
            "name": prompt.name,
            "description": prompt.description,
            "latest_version": prompt.latest_version
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.put(
    "/prompts/{name}",
    response_model=ResponseEnvelope[dict],
    summary="Create a new snapshot version of an existing Prompt Template"
)
async def update_prompt(
    request: Request,
    name: str,
    body: PromptUpdateRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.prompt_service.update_prompt(
        org_id=org_id,
        name=name,
        system_template=body.system_template,
        user_template=body.user_template,
        description=body.description
    )
    if result.is_fail:
        raise result.error()

    version = result.value()
    return {
        "data": {
            "prompt_template_id": version.prompt_template_id,
            "version": version.version,
            "hash": version.hash
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.post(
    "/prompts/{name}/compile",
    response_model=ResponseEnvelope[dict],
    summary="Compile and render a prompt template with variables"
)
async def compile_prompt(
    request: Request,
    name: str,
    body: PromptCompilationRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    result = await container.prompt_engine.compile(
        org_id=org_id,
        template_name=name,
        variables=body.variables,
        version_num=body.version_num
    )
    if result.is_fail:
        raise result.error()

    val = result.value()
    return {
        "data": val,
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.post(
    "/chat",
    response_model=ResponseEnvelope[dict],
    summary="Generate a chat response using gateway and selection policies"
)
async def generate_chat(
    request: Request,
    body: ChatGenerationRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = body.correlation_id or getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    # Map message DTOs to raw dictionaries for AIGateway
    messages = [{"role": msg.role, "content": msg.content} for msg in body.messages]

    response = await container.ai_gateway.generate_chat(
        org_id=org_id,
        messages=messages,
        policy=body.policy,
        settings=body.settings,
        correlation_id=correlation_id
    )

    return {
        "data": {
            "content": response.message_content,
            "role": response.role,
            "model": response.model_name,
            "provider": response.provider_name,
            "usage": {
                "prompt_tokens": response.token_usage.prompt_tokens,
                "completion_tokens": response.token_usage.completion_tokens,
                "total_tokens": response.token_usage.total_tokens
            }
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.post(
    "/completion",
    response_model=ResponseEnvelope[dict],
    summary="Generate a text completion using gateway and selection policies"
)
async def generate_completion(
    request: Request,
    body: CompletionGenerationRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = body.correlation_id or getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    response = await container.ai_gateway.generate_completion(
        org_id=org_id,
        prompt=body.prompt,
        policy=body.policy,
        settings=body.settings,
        correlation_id=correlation_id
    )

    return {
        "data": {
            "text": response.text,
            "model": response.model_name,
            "provider": response.provider_name,
            "usage": {
                "prompt_tokens": response.token_usage.prompt_tokens,
                "completion_tokens": response.token_usage.completion_tokens,
                "total_tokens": response.token_usage.total_tokens
            }
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }


@router.post(
    "/embeddings",
    response_model=ResponseEnvelope[dict],
    summary="Generate text embeddings using gateway"
)
async def generate_embeddings(
    request: Request,
    body: EmbeddingGenerationRequest,
    claims: dict = Depends(verify_jwt)
) -> dict:
    from syncsphere.core.dependency_injection.container import container
    correlation_id = body.correlation_id or getattr(request.state, "correlation_id", None)
    org_id = claims["org"]

    vectors = await container.ai_gateway.generate_embedding(
        org_id=org_id,
        input_texts=body.input_texts,
        correlation_id=correlation_id
    )

    return {
        "data": {
            "embeddings": vectors
        },
        "meta": ResponseMeta(request_id=correlation_id)
    }
