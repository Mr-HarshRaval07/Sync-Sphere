import logging
from typing import List, Dict, Any, Optional
from syncsphere.connectors.domain.repositories import ConnectorRepository
from syncsphere.connectors.domain.value_objects import ToolDefinition
from syncsphere.planner.domain.value_objects import (
    ConnectorCandidate,
    ToolCandidate,
    CapabilityMatch
)

logger = logging.getLogger("syncsphere.planner.domain.services.connector_intel")

class ConnectorDiscoveryService:
    """Discovers active connectors configured within an organization boundary."""
    def __init__(self, connector_repo: ConnectorRepository) -> None:
        self.connector_repo = connector_repo

    async def get_active_connectors(self, org_id: str) -> List[Any]:
        """Lists active and healthy connectors in the org context."""
        connectors = await self.connector_repo.list_by_org(org_id)
        # Filter only enabled connectors
        return [c for c in connectors if c.is_enabled]


class CapabilityMatcher:
    """Matches a planning step's capability requirement against active tool signatures."""
    @staticmethod
    def calculate_match(step_id: str, requirement: str, tools: List[ToolDefinition], connector_id: str) -> List[ToolCandidate]:
        """Evaluates description and keyword overlaps to score tool candidates."""
        candidates = []
        req_words = set(requirement.lower().replace("_", " ").split())
        
        for tool in tools:
            # Check overlap on name and description
            name_words = set(tool.name.lower().replace("_", " ").split())
            desc_words = set(tool.description.lower().replace("_", " ").split())
            
            overlap_name = len(req_words.intersection(name_words))
            overlap_desc = len(req_words.intersection(desc_words))
            
            score = 0.0
            if overlap_name > 0:
                score += 0.6 + (0.4 * (overlap_name / max(len(req_words), 1)))
            if overlap_desc > 0:
                score += 0.2 * (overlap_desc / max(len(desc_words), 1))
                
            # Direct match check
            if tool.name.lower() == requirement.lower().replace(" ", "_"):
                score = 1.0
                
            if score > 0.1:
                candidates.append(ToolCandidate(
                    tool_name=tool.name,
                    connector_id=connector_id,
                    score=min(score, 1.0),
                    description_match_score=min(score, 1.0)
                ))
                
        return sorted(candidates, key=lambda c: c.score, reverse=True)


class ConnectorRanker:
    """Ranks connectors based on aggregated candidate tool matching confidence."""
    @staticmethod
    def rank_connectors(candidates: List[ConnectorCandidate]) -> List[ConnectorCandidate]:
        return sorted(candidates, key=lambda c: c.score, reverse=True)


class ToolSelector:
    """Selects the best available tool for a planning step using the discovery repository."""
    def __init__(self, discovery_service: ConnectorDiscoveryService) -> None:
        self.discovery_service = discovery_service

    async def select_best_tool(self, org_id: str, step_id: str, capability_required: str) -> CapabilityMatch:
        active_connectors = await self.discovery_service.get_active_connectors(org_id)
        
        best_tool: Optional[ToolCandidate] = None
        best_conn_candidate: Optional[ConnectorCandidate] = None
        
        for conn in active_connectors:
            candidates = CapabilityMatcher.calculate_match(step_id, capability_required, conn.tools, conn.id)
            if candidates:
                top_candidate = candidates[0]
                if not best_tool or top_candidate.score > best_tool.score:
                    best_tool = top_candidate
                    best_conn_candidate = ConnectorCandidate(
                        connector_id=conn.id,
                        name=conn.name,
                        score=top_candidate.score
                    )
                    
        if best_tool and best_conn_candidate:
            return CapabilityMatch(
                step_id=step_id,
                best_connector=best_conn_candidate,
                best_tool=best_tool,
                confidence=best_tool.score,
                match_explanation=f"Selected tool '{best_tool.tool_name}' on connector '{best_conn_candidate.name}' with match score {best_tool.score}"
            )
            
        return CapabilityMatch(
            step_id=step_id,
            confidence=0.0,
            match_explanation=f"No matching tool found for capability '{capability_required}'"
        )


class ToolRanker:
    """Ranks tool candidates."""
    @staticmethod
    def rank_tools(candidates: List[ToolCandidate]) -> List[ToolCandidate]:
        return sorted(candidates, key=lambda c: c.score, reverse=True)


class CompatibilityValidator:
    """Validates parameters mapping compatibility against JSON schema requirements."""
    @staticmethod
    def validate_schema(arguments: Dict[str, Any], tool_definition: ToolDefinition) -> bool:
        # Static validation checking if required fields exist
        required_fields = tool_definition.input_schema.get("required", [])
        for field in required_fields:
            if field not in arguments:
                return False
        return True
