import asyncio
import os
import sys

sys.path.append(os.path.abspath('src'))

from syncsphere.core.config.settings import settings
from syncsphere.ai.domain.value_objects import InferenceSettings, StructuredOutputSchema
from syncsphere.ai.infrastructure.providers.openrouter import OpenRouterProviderAdapter

async def main():
    out = []
    
    out.append("==================================================")
    out.append("STEP 4: VERIFY CONFIGURATION")
    out.append("==================================================")
    
    api_key = settings.ai.llm_api_key.get_secret_value()
    out.append("SYNCSPHERE_LLM_API_KEY = " + ("SET" if api_key and api_key != "mock-api-key-for-local-dev" else "MISSING or DEFAULT"))
    out.append(f"Provider (.env) = {settings.ai.llm_provider}")
    out.append(f"Model (.env) = {settings.ai.llm_model}")

    out.append("\n==================================================")
    out.append("STEP 5: DIRECT OPENROUTER TEST")
    out.append("==================================================")
    try:
        provider = OpenRouterProviderAdapter()
        settings_obj = InferenceSettings(temperature=0.0)
        schema = StructuredOutputSchema(
            schema_name="TestSchema",
            json_schema={"type": "object", "properties": {"success": {"type": "boolean"}}}
        )
        
        out.append(f"Testing direct OpenRouter chat completion with model: {settings.ai.llm_model}")
        
        res = await provider.structured_output(
            model_name=settings.ai.llm_model,
            messages=[{"role": "user", "content": "Say hello."}],
            schema=schema,
            settings=settings_obj,
            api_key=api_key
        )
        
        if res.success:
            out.append("DIRECT OPENROUTER TEST:\nPASS")
            out.append(f"Raw Output: {res.raw_output}")
        else:
            out.append("DIRECT OPENROUTER TEST:\nFAIL")
            out.append(f"Error Message: {res.error_message}")
    except Exception as e:
        out.append("DIRECT OPENROUTER TEST:\nFAIL (Exception)")
        out.append(f"Exception: {type(e).__name__} - {str(e)}")

    with open("diag_clean.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out))

if __name__ == "__main__":
    asyncio.run(main())
