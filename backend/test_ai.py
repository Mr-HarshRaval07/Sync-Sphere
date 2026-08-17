import asyncio, json, os, logging
from syncsphere.core.dependency_injection.container import container
from syncsphere.tasks.schemas import PlanWithAIRequest, StructuredOutputSchema, AIPlannedTaskSchema
from syncsphere.core.ai_service.adapters import OpenRouterProviderAdapter
from syncsphere.core.ai_service.policy import ModelSelectionPolicy

logging.basicConfig(level=logging.INFO)

async def test_ai_extraction():
    await container.init_repos()
    
    body = PlanWithAIRequest(prompt="Send an email from unconnected_friend@gmail.com to abc@gmail.com")
    
    # Mirroring router.py
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert project management AI. Your job is to parse the user's intent into a structured task and recommend exactly which automated integrations should be run.\n\n"
                "## AVAILABLE INTEGRATIONS\n"
                "- gmail.send_email (Requires: 'to', 'subject', 'body'. Optional: 'google_email')\n"
                "- slack.send_message (Requires: 'slack_channel', 'message'. Optional: 'slack_workspace')\n"
                "- google_calendar.create_event (Requires: 'summary', 'start_datetime', 'end_datetime', 'timezone')\n"
                "- google_sheets.append_row (Requires: 'spreadsheet_id', 'range', 'values')\n"
                "- github.create_issue (Requires: 'repo', 'title', 'body')\n\n"
                "## CONNECTION STATUS\n"
                "- Google (Gmail/Calendar/Sheets): Connected\n"
                "- Slack: Connected\n"
                "- GitHub: Connected\n\n"
                "## RULES\n"
                "1. DO NOT make the user manually fill in every field. Aggressively extract and generate parameters directly from the user's natural-language prompt whenever reasonably possible.\n"
                "2. For Slack, automatically generate the 'message'. For GitHub, automatically generate 'title' and 'body'. For Gmail, automatically generate 'subject' and 'body' if you understand the intent.\n"
                "3. ONLY add elements to 'missing_fields' if the information is critically missing (like a recipient email address, calendar ID, a Slack channel, or GitHub repository).\n"
                "4. CRITICAL: DO NOT INVENT PLACEHOLDER OR FAKE DATA. For example, never output '#general' for a Slack channel or 'your_email@domain.com' unless the user explicitly requested it. If missing, leave it out of the config dict and append the field name to 'missing_fields'.\n"
                "5. Automatically recommend the best integrations based only on intent. Do not blindly add all of them. ONLY select integrations that are explicitly available in the AVAILABLE INTEGRATIONS list.\n"
                "6. VERY IMPORTANT: You must output a JSON object with exactly these top-level keys: 'task', 'integrations', 'missing_fields', 'clarification_question'. Do NOT output 'project_name' or 'task_decomposition'.\n"
                "7. The 'task' top-level key MUST be an OBJECT containing exactly these: 'title', 'description', 'assignee', 'assignee_email', 'priority', 'status', 'due_date'.\n"
                "8. For each integration in 'integrations', you MUST use exactly the keys 'action', 'selected', and 'config'. Do NOT use 'provider' or 'type'. The 'action' string must PERFECTLY match one of the action keys in the list. For Google Sheets append_row, 'values' MUST be a JSON array of specific values (e.g. [\"A\", \"B\"]), not a single comma-separated string.\n"
                "9. CRITICAL: If the user explicitly asks to use a specific account or workspace as the actor/sender (e.g. 'using friend@gmail.com', 'from dev-workspace'), you MUST extract and include that exact identifier in the config object under 'google_email' or 'slack_workspace'. NEVER assume the recipient is the acting account.\n"
                "10. VERY IMPORTANT: The 'google_email' parameter means THE AUTHORIZED SENDER ACCOUNT. NEVER put the recipient email here. If there is no explicitly specified sender, DO NOT output 'google_email' at all."
            )
        },
        {
            "role": "user",
            "content": body.prompt
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
