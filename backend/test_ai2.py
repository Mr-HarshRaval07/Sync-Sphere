import asyncio, json, os, logging
from syncsphere.core.dependency_injection.container import container
from syncsphere.ai.domain.value_objects import StructuredOutputSchema
from syncsphere.tasks.router import AIPlannedTaskSchema
from syncsphere.core.ai_service.policy import ModelSelectionPolicy

logging.basicConfig(level=logging.INFO)

async def test_ai_extraction():
    await container.init_repos()
    
    prompt = "Send an email from unconnected_friend@gmail.com to abc@gmail.com"
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert project management AI. Your job is to parse the user's intent into a structured task and recommend exactly which automated integrations should be run.\n\n"
                "## AVAILABLE INTEGRATIONS\n"
                "- gmail.send_email (Requires: 'to', 'subject', 'body'. Optional: 'google_email')\n"
                "## RULES\n"
                "1. DO NOT make the user manually fill in every field. Aggressively extract and generate parameters directly from the user's natural-language prompt whenever reasonably possible.\n"
                "6. VERY IMPORTANT: You must output a JSON object with exactly these top-level keys: 'task', 'integrations', 'missing_fields', 'clarification_question'. Do NOT output 'project_name' or 'task_decomposition'.\n"
                "7. The 'task' top-level key MUST be an OBJECT containing exactly these: 'title', 'description', 'assignee', 'assignee_email', 'priority', 'status', 'due_date'.\n"
                "8. For each integration in 'integrations', you MUST use exactly the keys 'action', 'selected', and 'config'. Do NOT use 'provider' or 'type'. The 'action' string must PERFECTLY match one of the action keys in the list. For Google Sheets append_row, 'values' MUST be a JSON array of specific values (e.g. [\"A\", \"B\"]), not a single comma-separated string.\n"
                "9. CRITICAL: If the user explicitly asks to use a specific account or workspace as the actor/sender (e.g. 'using friend@gmail.com', 'from dev-workspace'), you MUST extract and include that exact identifier in the config object under 'google_email' or 'slack_workspace'. NEVER assume the recipient is the acting account.\n"
                "10. VERY IMPORTANT: The 'google_email' parameter means THE AUTHORIZED SENDER ACCOUNT. NEVER put the recipient email here. If there is no explicitly specified sender, DO NOT output 'google_email' at all."
            )
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    schema = StructuredOutputSchema(
        schema_name="AIPlannedTaskSchema",
        json_schema=AIPlannedTaskSchema.model_json_schema()
    )

    result = await container.ai_gateway.structured_output(
        org_id="testorg",
        messages=messages,
        schema=schema,
        policy=ModelSelectionPolicy.FAST
    )
    
    print("\n\n====== RESULT ======")
    print(result.raw_output)

if __name__ == "__main__":
    asyncio.run(test_ai_extraction())
