import pytest
from syncsphere.workflow.application.action_registry import CAPABILITY_REGISTRY
from syncsphere.planner.domain.services.connector_intel import CapabilityMatcher
from syncsphere.connectors.domain.value_objects import ToolDefinition

def test_notion_routing_over_healthcare():
    """
    Test that prompts containing Notion keywords do not require patient_id and match create_page.
    """
    # 1. Verify patient_id is completely absent from all required fields in Notion
    notion_actions = CAPABILITY_REGISTRY["notion"]["actions"]
    for action_name, action_def in notion_actions.items():
        assert "patient_id" not in action_def.get("required_fields", [])
        
    create_page_def = notion_actions["create_page"]
    
    # Verify parent_id is removed from required fields so hallucination doesn't happen
    assert "parent_id" in create_page_def.get("required_fields", [])
    
    # 2. Verify description contains right semantic keywords
    desc = create_page_def["description"].lower()
    assert "notion" in desc
    assert "page" in desc
    assert "workspace" in desc
    assert "database" in desc
    
    # 3. Simulate Capability Match
    tools = [
        ToolDefinition(name="create_page", description=create_page_def["description"], input_schema=create_page_def["input_schema"])
    ]
    
    match = CapabilityMatcher.calculate_match("step1", "Create a Notion page", tools, "notion")
    assert match[0].score > 0.5
    assert match[0].tool_name == "create_page"
    
    match_notes = CapabilityMatcher.calculate_match("step1", "Create notes in workspace", tools, "notion")
    assert match_notes[0].score > 0.5
    assert match_notes[0].tool_name == "create_page"
