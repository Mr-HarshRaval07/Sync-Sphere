from app.llm.parser import LLMResponseParser
from app.llm.factory import get_llm
from app.schemas.workflow import WorkflowPlan


class Planner:

    def __init__(self):
        self.llm = get_llm()

    async def create_plan(self, user_request: str) -> WorkflowPlan:

        prompt = f"""
        You are Sync Sphere's Workflow Planner.

        Your job is ONLY to convert a user's request into JSON.

        Rules:

        1. Return ONLY valid JSON.
        2. Do NOT wrap JSON inside markdown.
        3. Service names MUST be lowercase.
        4. Allowed services:
        - jira
        - slack
        - github
        - google_sheets

        5. Every step MUST contain

        step
        service
        action
        parameters

        6. Step numbering starts from 1.

        Example:

        {{
            "steps":[
                {{
                    "step":1,
                    "service":"jira",
                    "action":"create_issue",
                    "parameters":{{
                        "summary":"Login Bug"
                    }}
                }}
            ]
        }}

        User Request:

        {user_request}
        """
        response = await self.llm.generate(prompt)

        data = LLMResponseParser.parse_json(response)

        return WorkflowPlan.model_validate(data)