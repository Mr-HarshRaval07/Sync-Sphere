import pytest
from unittest.mock import AsyncMock, MagicMock
from syncsphere.shared_kernel.types.result import Result
from syncsphere.core.dependency_injection.container import container
from syncsphere.planner.application.commands import (
    GenerateWorkflowCommand,
    ImproveWorkflowCommand,
    ExplainWorkflowCommand
)
from syncsphere.planner.application.queries import (
    PreviewWorkflowQuery,
    PreviewExecutionGraphQuery,
    EstimateExecutionCostQuery,
    EstimateExecutionTimeQuery
)
from syncsphere.connectors.domain.entities.connector import Connector
from syncsphere.connectors.domain.value_objects import ToolDefinition


from syncsphere.ai.domain.value_objects import StructuredOutputResult

@pytest.mark.asyncio
async def test_generate_workflow_pipeline_success():
    org_id = "org_test"
    user_id = "user_test"
    
    # 1. Setup mock connector with a tool to match the capability
    mock_connector = Connector(
        org_id=org_id,
        name="Slack Connector",
        transport_type="stdio",
        connection_config={}
    )
    mock_connector.tools = [
        ToolDefinition(name="post_message", description="Post slack messages to channels", input_schema={})
    ]
    await container.connector_repo.save(mock_connector)
    
    # 2. Mock AI Gateway structured output calls
    async def mock_structured_output(org_id, messages, schema, policy, settings=None, correlation_id=None):
        # Depending on schema name, return matching payload
        name = schema.schema_name
        if name == "IntentClassification":
            return StructuredOutputResult(
                success=True,
                parsed_object={
                    "category": "workflow_generation",
                    "confidence_score": 0.95,
                    "reasoning": "User requested generating workflow",
                    "primary_goal": "Post slack message notification"
                }
            )
        elif name == "EntityExtraction":
            return StructuredOutputResult(
                success=True,
                parsed_object={
                    "entities": [
                        {"name": "channel", "value": "general", "entity_type": "string", "confidence": 0.9}
                    ]
                }
            )
        elif name == "GoalExtraction":
            return StructuredOutputResult(
                success=True,
                parsed_object={
                    "goals": [
                        {"goal_id": "step_1", "description": "Decomposed slack post", "priority": 1, "dependencies": []}
                    ]
                }
            )
        elif name == "ConstraintExtraction":
            return StructuredOutputResult(
                success=True,
                parsed_object={
                    "constraints": []
                }
            )
        elif name == "TaskDecomposition":
            return StructuredOutputResult(
                success=True,
                parsed_object={
                    "steps": [
                        {
                            "step_id": "slack_step",
                            "name": "Slack Step",
                            "description": "Send notification",
                            "capability_required": "post_message",
                            "depends_on_steps": [],
                            "arguments": {"channel": "general", "message": "hello world"}
                        }
                    ]
                }
            )
        return StructuredOutputResult(success=False, error_message="Unknown schema")
        
    container.ai_gateway.structured_output = mock_structured_output
    
    # 3. Dispatch the command
    cmd = GenerateWorkflowCommand(
        org_id=org_id,
        user_id=user_id,
        prompt="Send hello world to slack general channel",
        strategy="simple"
    )
    
    res = await container.planner_service.generate_workflow(cmd)
    assert res.is_ok
    
    wf = res.value()
    assert wf.org_id == org_id
    assert wf.name == "Post slack message notification"
    assert len(wf.graph.nodes) == 2
    assert "slack_step" in wf.graph.nodes
    assert "approve_slack_step" in wf.graph.nodes
    
    # Check that a session and a trace was saved
    session_keys = list(container.planner_session_repo.store.keys())
    assert len(session_keys) == 1
    session_id = session_keys[0]
    session = container.planner_session_repo.store[session_id]
    assert session.generated_workflow_id == wf.id
    
    traces = await container.planner_trace_repo.list_by_session(session_id)
    assert len(traces) == 1
    assert traces[0].status == "success"
    assert traces[0].phases["intent_recognition"] is not None
    assert traces[0].phases["workflow_compilation"] is not None
    
    # Test preview_workflow query
    prev_query = PreviewWorkflowQuery(org_id=org_id, session_id=session_id)
    prev_res = await container.planner_service.preview_workflow(prev_query)
    assert prev_res.is_ok
    assert len(prev_res.value()["nodes"]) == 1
    
    # Test preview_execution_graph query
    exec_query = PreviewExecutionGraphQuery(org_id=org_id, session_id=session_id)
    exec_res = await container.planner_service.preview_execution_graph(exec_query)
    assert exec_res.is_ok
    assert "topological_order" in exec_res.value()
    
    # Test explain_workflow command
    explain_cmd = ExplainWorkflowCommand(org_id=org_id, session_id=session_id)
    explain_res = await container.planner_service.explain_workflow(explain_cmd)
    assert explain_res.is_ok
    assert "tool_selections" in explain_res.value()
    
    # Test estimate queries
    cost_query = EstimateExecutionCostQuery(org_id=org_id, session_id=session_id)
    cost_res = await container.planner_service.estimate_execution_cost(cost_query)
    assert cost_res.is_ok
    assert cost_res.value() > 0.0
    
    time_query = EstimateExecutionTimeQuery(org_id=org_id, session_id=session_id)
    time_res = await container.planner_service.estimate_execution_time(time_query)
    assert time_res.is_ok
    assert time_res.value() > 0.0
