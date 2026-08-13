from typing import List, Optional, Dict, Any
from syncsphere.shared_kernel.domain.aggregate_root import AggregateRoot
from syncsphere.planner.domain.value_objects import (
    UserIntent,
    PlanAST,
    PlanningExplanation,
    PlanningMetrics,
    PlannerFeedback
)

class PlanningSession(AggregateRoot):
    """
    PlanningSession represents an interactive workspace for a user or tenant
    collaborating with the planner to design, optimize, or explain workflows.
    """
    
    def __init__(
        self,
        org_id: str,
        user_id: str,
        prompt_history: Optional[List[str]] = None,
        current_intent: Optional[UserIntent] = None,
        current_ast: Optional[PlanAST] = None,
        generated_workflow_id: Optional[str] = None,
        explanation: Optional[PlanningExplanation] = None,
        metrics: Optional[PlanningMetrics] = None,
        feedback_history: Optional[List[PlannerFeedback]] = None,
        id: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(id=id, **kwargs)
        self.org_id = org_id
        self.user_id = user_id
        self.prompt_history = prompt_history or []
        self.current_intent = current_intent
        self.current_ast = current_ast
        self.generated_workflow_id = generated_workflow_id
        self.explanation = explanation
        self.metrics = metrics or PlanningMetrics()
        self.feedback_history = feedback_history or []

    def add_prompt(self, prompt: str) -> None:
        """Appends a prompt string to the session history."""
        self.prompt_history.append(prompt)

    def update_intent(self, intent: UserIntent) -> None:
        """Binds the parsed intent payload to the active session state."""
        self.current_intent = intent

    def update_ast(self, ast: PlanAST) -> None:
        """Binds the intermediate PlanAST representation to the active session."""
        self.current_ast = ast

    def update_generated_workflow(self, workflow_id: str) -> None:
        """Saves the final workflow aggregate association id."""
        self.generated_workflow_id = workflow_id

    def add_feedback(self, feedback: PlannerFeedback) -> None:
        """Logs user corrections or guidance to the conversation memory."""
        self.feedback_history.append(feedback)
