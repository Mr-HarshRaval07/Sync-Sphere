import asyncio
import os
import sys
import json

sys.path.append(os.path.abspath('src'))

from syncsphere.core.config.settings import settings
from syncsphere.ai.domain.value_objects import InferenceSettings, StructuredOutputSchema
from syncsphere.ai.infrastructure.providers.openrouter import OpenRouterProviderAdapter
from syncsphere.tasks.router import AIPlannedTaskSchema

async def main():
    out = []
    try:
        api_key = settings.ai.llm_api_key.get_secret_value()
        provider = OpenRouterProviderAdapter()
        settings_obj = InferenceSettings(temperature=0.0)
        
        schema = StructuredOutputSchema(
            schema_name="AIPlannedTaskSchema",
            json_schema=AIPlannedTaskSchema.model_json_schema()
        )
        
        out.append(f"Testing direct OpenRouter chat completion with model: {settings.ai.llm_model} and REAL schema")
        
        system_instruction = (
            "You are the SyncSphere AI workflow planner.\n\n"
            "Return ONLY valid JSON.\n"
            "Do not use Markdown.\n"
            "Do not wrap the JSON in ```json blocks.\n"
            "The JSON must follow this schema exactly:\n\n"
            f"{json.dumps(schema.json_schema, indent=2)}"
        )
        
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": "Send a Slack message saying SyncSphere test."}
        ]
        
        res = await provider.generate_chat(
            model_name=settings.ai.llm_model,
            messages=messages,
            settings=settings_obj,
            api_key=api_key
        )
        
        raw_text = res.message_content.strip()
        out.append("RAW RESPONSE:")
        out.append(raw_text)
        
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()
            
        try:
            parsed = json.loads(raw_text)
            out.append("JSON VALIDATION: PASS")
            out.append(json.dumps(parsed, indent=2))
        except json.JSONDecodeError as e:
            out.append(f"JSON VALIDATION: FAIL - {e}")
            
    except Exception as e:
        out.append(f"DIRECT OPENROUTER TEST:\nFAIL (Exception) - {e}")

    with open("diag_schema_test.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(out))

if __name__ == "__main__":
    asyncio.run(main())
