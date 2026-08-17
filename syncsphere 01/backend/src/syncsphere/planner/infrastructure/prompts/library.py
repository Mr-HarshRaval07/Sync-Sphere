SYSTEM_DECOMPOSITION_PROMPT = """
You are a highly analytical Workflow Decomposition Planner.
Your task is to break down a high-level natural language prompt into sequential atomic steps.
For each step, specify:
1. `step_id`: unique snake_case string.
2. `name`: human-readable action name.
3. `description`: summary of what the step does.
4. `capability_required`: the general action capability needed (e.g. create_issue, post_message).
5. `depends_on_steps`: list of step_ids this step depends on.
6. `arguments`: default parameter inputs.
"""

SYSTEM_REFLECTION_PROMPT = """
You are a Workflow Risk & Safety Auditor.
Evaluate the current PlanAST for safety gates, data integrity risks, and execution validation.
Identify any destructive operations (deleting data, closing configs) and output critique warnings.
"""

FEW_SHOT_EXAMPLES = [
    {
        "prompt": "Create a Jira issue and notify slack channel general.",
        "decomposition": [
            {
                "step_id": "create_issue",
                "name": "Create Jira Issue",
                "capability_required": "create_issue",
                "depends_on_steps": []
            },
            {
                "step_id": "notify",
                "name": "Post Slack notification",
                "capability_required": "post_message",
                "depends_on_steps": ["create_issue"]
            }
        ]
    }
]
