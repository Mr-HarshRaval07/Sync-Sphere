import asyncio
import json
from syncsphere.core.config.settings import settings
from syncsphere.ai.infrastructure.providers.openrouter import OpenRouterProviderAdapter
from syncsphere.ai.domain.value_objects import InferenceSettings, StructuredOutputSchema

async def main():
    print("OPENROUTER KEY:", "***" + settings.openrouter_api_key[-4:] if settings.openrouter_api_key else "MISSING")
    
    provider = OpenRouterProviderAdapter()
    
    schema = StructuredOutputSchema(
        schema_name="Test",
        json_schema={"type": "object", "properties": {"success": {"type": "boolean"}}}
    )
    settings_obj = InferenceSettings()
    
    try:
        res = await provider.structured_output(
            model_name="google/gemini-2.5-flash", # or whatever is in settings
            messages=[{"role": "user", "content": "Hello"}],
            schema=schema,
            settings=settings_obj,
            api_key=settings.openrouter_api_key
        )
        print("Success:", res.success)
        print("Raw:", res.raw_output)
        print("Error:", res.error_message)
    except Exception as e:
        print("Exception:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
