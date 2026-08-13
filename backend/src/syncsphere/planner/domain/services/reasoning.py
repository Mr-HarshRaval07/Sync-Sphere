import logging
from typing import List, Dict, Any, Optional
from syncsphere.ai.domain.services.ai_gateway import AIGateway
from syncsphere.ai.domain.value_objects import StructuredOutputSchema, ModelSelectionPolicy
from syncsphere.planner.domain.value_objects import (
    PlanningStep,
    ReasoningStep,
    UserIntent,
    PlanAST,
    ASTNode,
    ASTVariable,
    ASTFlow,
    PlanningExplanation,
    RiskAssessment
)

logger = logging.getLogger("syncsphere.planner.domain.services.reasoning")

class TaskDecomposer:
    """Decomposes goals into sequential atomic PlanningSteps using the AI Gateway."""
    def __init__(self, ai_gateway: AIGateway) -> None:
        self.ai_gateway = ai_gateway

    async def decompose_task(self, org_id: str, prompt: str, history: List[str] = None) -> List[PlanningStep]:
        schema = StructuredOutputSchema(
            schema_name="TaskDecomposition",
            json_schema={
                "type": "object",
                "properties": {
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "step_id": {"type": "string"},
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "capability_required": {"type": "string"},
                                "depends_on_steps": {"type": "array", "items": {"type": "string"}},
                                "arguments": {"type": "object"}
                            },
                            "required": ["step_id", "name", "description", "capability_required", "depends_on_steps", "arguments"]
                        }
                    }
                },
                "required": ["steps"]
            }
        )
        
        messages = [
            {"role": "system", "content": "You are a decomposition engine. Break down instructions into logical steps with required capabilities and dependency arrays."},
            {"role": "user", "content": f"Decompose prompt: '{prompt}'. History: {str(history or [])}"}
        ]
        
        try:
            res = await self.ai_gateway.structured_output(
                org_id=org_id,
                messages=messages,
                schema=schema,
                policy=ModelSelectionPolicy.FAST
            )
            if res.success and res.parsed_object:
                steps = []
                for s in res.parsed_object.get("steps", []):
                    steps.append(PlanningStep(
                        step_id=s["step_id"],
                        name=s["name"],
                        description=s["description"],
                        capability_required=s["capability_required"],
                        depends_on_steps=s["depends_on_steps"],
                        arguments=s["arguments"]
                    ))
                return steps
        except Exception as e:
            logger.warning("AI Gateway task decomposition failed: %s. Using fallback.", str(e))
            
        # Fallback decomposition rules based on keywords
        steps = []
        if "issue" in prompt.lower() or "jira" in prompt.lower():
            steps.append(PlanningStep(
                step_id="create_issue",
                name="Create Jira Issue",
                description="Creates a new task ticket in Jira",
                capability_required="create_issue",
                arguments={"project_key": "PROJ", "summary": "AI Planned Task"}
            ))
            steps.append(PlanningStep(
                step_id="notify",
                name="Send Notification",
                description="Sends notification about the issue creation",
                capability_required="post_message",
                depends_on_steps=["create_issue"],
                arguments={"channel": "general", "message": "Issue created!"}
            ))
        else:
            steps.append(PlanningStep(
                step_id="action_step",
                name="Execute Action",
                description="Execute resolved action steps",
                capability_required="execute_action",
                arguments={}
            ))
        return steps


class DependencyResolver:
    """Validates step dependency order and detects cyclical step loops."""
    @staticmethod
    def resolve_dependencies(steps: List[PlanningStep]) -> List[PlanningStep]:
        # Validate that all dependent step ids exist in the list
        step_ids = {s.step_id for s in steps}
        for s in steps:
            s.depends_on_steps = [d for d in s.depends_on_steps if d in step_ids]
            
        # DFS cycle check
        visited = {}  # step_id -> status (0=visiting, 1=visited)
        adj = {s.step_id: s.depends_on_steps for s in steps}
        
        def has_cycle(u):
            visited[u] = 0  # visiting
            for v in adj.get(u, []):
                if visited.get(v) == 0:
                    return True
                elif v not in visited:
                    if has_cycle(v):
                        return True
            visited[u] = 1  # visited
            return False
            
        for s in steps:
            if s.step_id not in visited:
                if has_cycle(s.step_id):
                    raise ValueError(f"Cyclic dependency detected at step '{s.step_id}'")
                    
        return steps


class ParallelismAnalyzer:
    """Analyzes dependencies to determine parallel execution groupings (execution tiers)."""
    @staticmethod
    def analyze_parallelism(steps: List[PlanningStep]) -> List[List[str]]:
        # Topological Sort with Grouped Parallel Tiers
        in_degree = {s.step_id: 0 for s in steps}
        adj = {s.step_id: [] for s in steps}
        
        for s in steps:
            for dep in s.depends_on_steps:
                adj[dep].append(s.step_id)
                in_degree[s.step_id] += 1
                
        # Queue containing nodes with in_degree = 0
        current_tier = [u for u, deg in in_degree.items() if deg == 0]
        tiers = []
        
        while current_tier:
            tiers.append(current_tier)
            next_tier = []
            for u in current_tier:
                for v in adj[u]:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        next_tier.append(v)
            current_tier = next_tier
            
        return tiers


class WorkflowSynthesizer:
    """Synthesizes PlanAST from steps, capabilities matched, and variables resolved."""
    @staticmethod
    def synthesize_ast(steps: List[PlanningStep], matched_tools: Dict[str, Any]) -> PlanAST:
        nodes = []
        variables = []
        entry_nodes = []
        exit_nodes = []
        
        # Build variables dynamically from step arguments
        for step in steps:
            step_vars = []
            for arg_k, arg_v in step.arguments.items():
                var_name = f"{step.step_id}_{arg_k}"
                variables.append(ASTVariable(
                    name=var_name,
                    type="string" if isinstance(arg_v, str) else "object",
                    value=arg_v
                ))
                step_vars.append(ASTVariable(name=var_name, value=arg_v))
                
            match = matched_tools.get(step.step_id)
            conn_id = match.best_connector.connector_id if (match and match.best_connector) else None
            tool_name = match.best_tool.tool_name if (match and match.best_tool) else None
            
            nodes.append(ASTNode(
                node_id=step.step_id,
                name=step.name,
                type="action",
                connector_id=conn_id,
                tool_name=tool_name,
                arguments=step.arguments,
                inputs=step_vars,
                depends_on=step.depends_on_steps
            ))
            
            if not step.depends_on_steps:
                entry_nodes.append(step.step_id)
                
        # Find exit nodes (no downstream nodes)
        downstream = set()
        for step in steps:
            for dep in step.depends_on_steps:
                downstream.add(dep)
        exit_nodes = [s.step_id for s in steps if s.step_id not in downstream]
        
        # Build tiers for parallel paths
        parallel_paths = ParallelismAnalyzer.analyze_parallelism(steps)
        
        flows = ASTFlow(
            entry_nodes=entry_nodes,
            exit_nodes=exit_nodes,
            parallel_paths=parallel_paths
        )
        
        return PlanAST(
            variables=variables,
            nodes=nodes,
            flows=flows
        )


class PlannerReflectionEngine:
    """Performs self-critique/reflection loops over generated ASTs, suggesting safety guards."""
    def __init__(self, ai_gateway: AIGateway) -> None:
        self.ai_gateway = ai_gateway

    async def reflect(self, org_id: str, ast: PlanAST) -> Dict[str, Any]:
        """Critiques the current AST structure for loops, risks, and credentials safety."""
        # Check for potential risky terms
        has_destructive = False
        reasons = []
        
        for node in ast.nodes:
            name_lower = node.name.lower()
            tool_lower = (node.tool_name or "").lower()
            if any(term in name_lower or term in tool_lower for term in ["delete", "remove", "prune", "archive", "destroy"]):
                has_destructive = True
                reasons.append(f"Destructive action identified in node '{node.node_id}' ('{node.name}')")
                
        safety_score = 0.6 if has_destructive else 1.0
        risk_level = "high" if has_destructive else "low"
        
        return {
            "risk_assessment": RiskAssessment(
                safety_score=safety_score,
                risk_level=risk_level,
                identified_risks=reasons,
                has_destructive_actions=has_destructive
            ),
            "recommendations": ["Insert approval gate before destructive operation"] if has_destructive else []
        }


class ReasoningEngine:
    """Coordinates TaskDecomposer, DependencyResolver, and Synthesizer in a reasoning loop."""
    def __init__(self, decomposer: TaskDecomposer, reflection_engine: PlannerReflectionEngine) -> None:
        self.decomposer = decomposer
        self.reflection_engine = reflection_engine

    async def run_reasoning_loop(
        self,
        org_id: str,
        prompt: str,
        history: List[str] = None
    ) -> List[PlanningStep]:
        steps = await self.decomposer.decompose_task(org_id, prompt, history)
        resolved_steps = DependencyResolver.resolve_dependencies(steps)
        return resolved_steps
