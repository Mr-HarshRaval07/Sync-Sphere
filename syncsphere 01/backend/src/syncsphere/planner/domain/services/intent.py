import logging
from typing import List, Dict, Any, Optional
from syncsphere.ai.domain.services.ai_gateway import AIGateway
from syncsphere.ai.domain.value_objects import StructuredOutputSchema, ModelSelectionPolicy
from syncsphere.planner.domain.value_objects import (
    UserIntent,
    IntentClassification,
    IntentConfidence,
    ExtractedEntity,
    WorkflowGoal,
    WorkflowConstraint
)

logger = logging.getLogger("syncsphere.planner.domain.services.intent")

class IntentClassifier:
    """Classifies user natural language prompts into workflow planner intentions."""
    def __init__(self, ai_gateway: AIGateway) -> None:
        self.ai_gateway = ai_gateway

    async def classify(self, org_id: str, prompt: str) -> IntentClassification:
        schema = StructuredOutputSchema(
            schema_name="IntentClassification",
            json_schema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": ["workflow_generation", "workflow_improvement", "workflow_explanation"]},
                    "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "reasoning": {"type": "string"},
                    "primary_goal": {"type": "string"}
                },
                "required": ["category", "confidence_score", "reasoning", "primary_goal"]
            }
        )
        
        messages = [
            {"role": "system", "content": "You are a specialized workflow intent classifier. Resolve user categories and primary goals."},
            {"role": "user", "content": f"Classify the following prompt: '{prompt}'"}
        ]
        
        try:
            res = await self.ai_gateway.structured_output(
                org_id=org_id,
                messages=messages,
                schema=schema,
                policy=ModelSelectionPolicy.FAST
            )
            if res.success and res.parsed_object:
                obj = res.parsed_object
                return IntentClassification(
                    category=obj["category"],
                    confidence=IntentConfidence(
                        confidence_score=obj["confidence_score"],
                        is_unambiguous=obj["confidence_score"] > 0.7,
                        reasoning=obj["reasoning"]
                    ),
                    primary_goal=obj["primary_goal"]
                )
        except Exception as e:
            logger.warning("AI Gateway structured intent classification failed: %s. Using fallback.", str(e))
            
        # Fallback implementation for offline/test context
        category = "workflow_generation"
        if "improve" in prompt.lower() or "update" in prompt.lower() or "optimize" in prompt.lower():
            category = "workflow_improvement"
        elif "explain" in prompt.lower() or "why" in prompt.lower() or "describe" in prompt.lower():
            category = "workflow_explanation"
            
        return IntentClassification(
            category=category,
            confidence=IntentConfidence(
                confidence_score=0.9,
                is_unambiguous=True,
                reasoning="Rule-based fallback parsing."
            ),
            primary_goal=prompt
        )


class EntityExtractor:
    """Extracts dynamic parameter values and entities from natural language prompts."""
    def __init__(self, ai_gateway: AIGateway) -> None:
        self.ai_gateway = ai_gateway

    async def extract(self, org_id: str, prompt: str) -> List[ExtractedEntity]:
        schema = StructuredOutputSchema(
            schema_name="EntityExtraction",
            json_schema={
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "value": {"type": "string"},
                                "entity_type": {"type": "string", "enum": ["string", "number", "boolean", "object", "array"]},
                                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                            },
                            "required": ["name", "value", "entity_type", "confidence"]
                        }
                    }
                },
                "required": ["entities"]
            }
        )
        
        messages = [
            {"role": "system", "content": "You are a parameter extractor. Extract variables, constants, emails, counts, and settings from requests."},
            {"role": "user", "content": f"Extract entities from: '{prompt}'"}
        ]
        
        try:
            res = await self.ai_gateway.structured_output(
                org_id=org_id,
                messages=messages,
                schema=schema,
                policy=ModelSelectionPolicy.FAST
            )
            if res.success and res.parsed_object:
                entities = []
                for item in res.parsed_object.get("entities", []):
                    entities.append(ExtractedEntity(
                        name=item["name"],
                        value=item["value"],
                        entity_type=item["entity_type"],
                        confidence=item["confidence"]
                    ))
                return entities
        except Exception as e:
            logger.warning("AI Gateway structured entity extraction failed: %s. Using fallback.", str(e))
            
        # Fallback mock extraction
        if "jira" in prompt.lower() or "issue" in prompt.lower():
            return [ExtractedEntity(name="project_key", value="PROJ", entity_type="string", confidence=0.85)]
        return []


class GoalExtractor:
    """Decomposes overall prompts into distinct target sub-goals."""
    def __init__(self, ai_gateway: AIGateway) -> None:
        self.ai_gateway = ai_gateway

    async def extract_goals(self, org_id: str, prompt: str) -> List[WorkflowGoal]:
        schema = StructuredOutputSchema(
            schema_name="GoalExtraction",
            json_schema={
                "type": "object",
                "properties": {
                    "goals": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "goal_id": {"type": "string"},
                                "description": {"type": "string"},
                                "priority": {"type": "integer"},
                                "dependencies": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["goal_id", "description", "priority", "dependencies"]
                        }
                    }
                },
                "required": ["goals"]
            }
        )
        
        messages = [
            {"role": "system", "content": "You are a goal decomposer. Break down user instructions into ordered goals."},
            {"role": "user", "content": f"Decompose: '{prompt}'"}
        ]
        
        try:
            res = await self.ai_gateway.structured_output(
                org_id=org_id,
                messages=messages,
                schema=schema,
                policy=ModelSelectionPolicy.FAST
            )
            if res.success and res.parsed_object:
                goals = []
                for g in res.parsed_object.get("goals", []):
                    goals.append(WorkflowGoal(
                        goal_id=g["goal_id"],
                        description=g["description"],
                        priority=g["priority"],
                        dependencies=g["dependencies"]
                    ))
                return goals
        except Exception as e:
            logger.warning("AI Gateway goal extraction failed: %s. Using fallback.", str(e))
            
        return [
            WorkflowGoal(goal_id="step_1", description="Process input user action", priority=1),
            WorkflowGoal(goal_id="step_2", description="Notify completion", priority=2, dependencies=["step_1"])
        ]


class ConstraintExtractor:
    """Extracts limits, timeout constraints, retries, or security approvals."""
    def __init__(self, ai_gateway: AIGateway) -> None:
        self.ai_gateway = ai_gateway

    async def extract_constraints(self, org_id: str, prompt: str) -> List[WorkflowConstraint]:
        schema = StructuredOutputSchema(
            schema_name="ConstraintExtraction",
            json_schema={
                "type": "object",
                "properties": {
                    "constraints": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "constraint_type": {"type": "string", "enum": ["budget", "retry", "approval", "timeout"]},
                                "value": {"type": "string"},
                                "severity": {"type": "string", "enum": ["critical", "advisory"]}
                            },
                            "required": ["constraint_type", "value", "severity"]
                        }
                    }
                },
                "required": ["constraints"]
            }
        )
        
        messages = [
            {"role": "system", "content": "Extract safety limits, approval needs, or cost constraints from requests."},
            {"role": "user", "content": f"Extract constraints from: '{prompt}'"}
        ]
        
        try:
            res = await self.ai_gateway.structured_output(
                org_id=org_id,
                messages=messages,
                schema=schema,
                policy=ModelSelectionPolicy.FAST
            )
            if res.success and res.parsed_object:
                constraints = []
                for c in res.parsed_object.get("constraints", []):
                    constraints.append(WorkflowConstraint(
                        constraint_type=c["constraint_type"],
                        value=c["value"],
                        severity=c["severity"]
                    ))
                return constraints
        except Exception as e:
            logger.warning("AI Gateway constraint extraction failed: %s. Using fallback.", str(e))
            
        return []


class ConversationAnalyzer:
    """Analyzes conversational histories to retrieve feedback adjustments."""
    def __init__(self, ai_gateway: AIGateway) -> None:
        self.ai_gateway = ai_gateway

    async def analyze_history(self, org_id: str, history: List[str]) -> Optional[str]:
        if not history:
            return None
        messages = [
            {"role": "system", "content": "You are a user feedback analyzer. Review chat history to identify adjustments requests for the workflow generator plan."},
            {"role": "user", "content": f"Review history: {str(history)}"}
        ]
        try:
            res = await self.ai_gateway.generate_chat(
                org_id=org_id,
                messages=messages,
                policy=ModelSelectionPolicy.FAST
            )
            return res.message_content
        except Exception:
            return None
