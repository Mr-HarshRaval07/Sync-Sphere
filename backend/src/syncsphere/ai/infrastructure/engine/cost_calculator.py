import logging
from typing import Optional
from syncsphere.ai.domain.entities.model import AIModel
from syncsphere.ai.domain.value_objects import CostUsage

logger = logging.getLogger("syncsphere.ai.infrastructure.engine.cost_calculator")

class CostCalculator:
    """CostCalculator computes monetary pricing for inference token usages."""
    
    @staticmethod
    def calculate_cost(model: AIModel, prompt_tokens: int, completion_tokens: int) -> CostUsage:
        """Calculates input, output, and aggregate costs based on model parameters."""
        prompt_cost = (prompt_tokens / 1000.0) * model.cost_per_1k_input
        completion_cost = (completion_tokens / 1000.0) * model.cost_per_1k_output
        total = prompt_cost + completion_cost
        
        return CostUsage(
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total
        )
