import logging
from syncsphere.runtime.domain.entities.session import ExecutionSession
from syncsphere.runtime.domain.value_objects import ExecutionState
from syncsphere.workflow.domain.entities.workflow import Workflow

logger = logging.getLogger("syncsphere.runtime.application.services.saga")

class SagaCoordinator:
    """Coordinates Saga transaction rollbacks by executing compensation steps in reverse topological order."""
    
    @staticmethod
    async def run_compensation(
        session: ExecutionSession,
        workflow: Workflow,
        step_executor
    ) -> bool:
        """
        Runs compensation nodes for all completed steps in reverse order.
        Returns True if rollback completed successfully.
        """
        logger.info("Saga rollback initiated for execution session: %s", session.id)
        session.transition_to(ExecutionState.COMPENSATING)
        
        # Get completed step IDs in reverse topological order
        completed_ids = []
        # Sort based on execution completion time if available, or reverse topological order
        if session.execution_ast:
            topo = session.execution_ast.topological_order
            completed_ids = [nid for nid in reversed(topo) if nid in session.steps and session.steps[nid].status == ExecutionState.COMPLETED]
        else:
            completed_ids = [nid for nid, step in session.steps.items() if step.status == ExecutionState.COMPLETED]
            
        success = True
        for node_id in completed_ids:
            node = workflow.graph.nodes.get(node_id)
            if not node or not node.compensation_policy or not node.compensation_policy.compensation_node_id:
                continue
                
            comp_node_id = node.compensation_policy.compensation_node_id
            logger.info("Executing compensation step: %s for failed step: %s", comp_node_id, node_id)
            
            try:
                # Execute the compensation step (e.g. tool call)
                # Map compensation step variables if needed
                comp_step = session.steps.get(comp_node_id)
                if not comp_step:
                    # Initialize step if missing
                    from syncsphere.runtime.domain.value_objects import ExecutionStep
                    comp_step = ExecutionStep(
                        node_id=comp_node_id,
                        name=f"Compensate {node.name}",
                        type="tool_call"
                    )
                    session.steps[comp_node_id] = comp_step
                
                res = await step_executor.execute(session, comp_node_id)
                if res.get("status") == "failed":
                    logger.error("Compensation step '%s' failed.", comp_node_id)
                    success = False
                    break
                else:
                    session.record_step_completion(comp_node_id, res.get("outputs", {}))
            except Exception as e:
                logger.exception("Compensation step '%s' encountered an exception: %s", comp_node_id, e)
                success = False
                break
                
        if success:
            logger.info("Saga rollback completed successfully.")
            session.transition_to(ExecutionState.COMPLETED) # Mark finished (compensated)
            return True
        else:
            logger.error("Saga rollback failed.")
            session.transition_to(ExecutionState.FAILED)
            return False
