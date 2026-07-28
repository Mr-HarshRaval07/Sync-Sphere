import logging
import uuid
from typing import Dict, Any, Optional
from syncsphere.shared_kernel.types.result import Result
from syncsphere.shared_kernel.domain.domain_exception import EntityNotFoundException
from syncsphere.planner.domain.entities.session import PlanningSession
from syncsphere.planner.domain.entities.trace import PlannerTrace
from syncsphere.planner.domain.value_objects import PlanningContext, PlannerFeedback
from syncsphere.planner.domain.repositories import PlanningSessionRepository, PlannerTraceRepository
from syncsphere.planner.domain.pipeline.base import PlanningPipeline
from syncsphere.planner.domain.events import (
    PlanningStarted,
    PlanningCompleted,
    PlanningRejected
)
from syncsphere.connectors.domain.repositories import ConnectorRepository
from syncsphere.ai.domain.repositories import AIModelRepository
from syncsphere.workflow.domain.repositories.workflow_repository import WorkflowRepository
from syncsphere.workflow.domain.repositories.workflow_version_repository import WorkflowVersionRepository
from syncsphere.workflow.domain.entities.workflow import Workflow
from syncsphere.planner.application.commands import (
    GenerateWorkflowCommand,
    ImproveWorkflowCommand,
    ExplainWorkflowCommand,
    OptimizeWorkflowCommand
)
from syncsphere.planner.application.queries import (
    PreviewWorkflowQuery,
    PreviewExecutionGraphQuery,
    ExplainPlanQuery,
    EstimateExecutionCostQuery,
    EstimateExecutionTimeQuery
)

logger = logging.getLogger("syncsphere.planner.application.services.planner_service")

class PlannerApplicationService:
    """Application Service coordinating user intentions, strategy execution pipeline, compiling and validation."""
    
    def __init__(
        self,
        session_repo: PlanningSessionRepository,
        trace_repo: PlannerTraceRepository,
        pipeline: PlanningPipeline,
        connector_repo: ConnectorRepository,
        model_repo: AIModelRepository,
        workflow_repo: WorkflowRepository,
        version_repo: WorkflowVersionRepository,
        event_bus: Any
    ) -> None:
        self.session_repo = session_repo
        self.trace_repo = trace_repo
        self.pipeline = pipeline
        self.connector_repo = connector_repo
        self.model_repo = model_repo
        self.workflow_repo = workflow_repo
        self.version_repo = version_repo
        self.event_bus = event_bus

    async def generate_workflow(self, cmd: GenerateWorkflowCommand) -> Result[Workflow, Exception]:
        session_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        corr_id = cmd.correlation_id or f"plan-{uuid.uuid4()}"
        
        session = PlanningSession(
            id=session_id,
            org_id=cmd.org_id,
            user_id=cmd.user_id
        )
        session.add_prompt(cmd.prompt)
        
        trace = PlannerTrace(
            id=trace_id,
            org_id=cmd.org_id,
            session_id=session_id
        )
        
        await self.event_bus.publish(PlanningStarted(
            org_id=cmd.org_id,
            session_id=session_id,
            correlation_id=corr_id
        ))
        
        # Load PlanningContext details
        connectors = await self.connector_repo.list_by_org(cmd.org_id)
        models = await self.model_repo.list_by_org(cmd.org_id)
        
        context = PlanningContext(
            org_id=cmd.org_id,
            available_connectors=connectors,
            available_models=models,
            history=session.prompt_history
        )
        
        try:
            workflow, version, execution_plan = await self.pipeline.execute(
                session=session,
                prompt=cmd.prompt,
                context=context,
                strategy_name=cmd.strategy,
                trace=trace
            )
            
            # Persist artifacts
            await self.workflow_repo.save(workflow)
            await self.version_repo.save(version)
            await self.session_repo.save(session)
            await self.trace_repo.save(trace)
            
            await self.event_bus.publish(PlanningCompleted(
                org_id=cmd.org_id,
                session_id=session_id,
                correlation_id=corr_id,
                workflow_id=workflow.id,
                active_version=version.version
            ))
            
            return Result.ok(workflow)
        except Exception as e:
            logger.error("Planning execution failed: %s", str(e), exc_info=True)
            trace.fail(str(e), duration_ms=0.0)
            await self.trace_repo.save(trace)
            await self.event_bus.publish(PlanningRejected(
                org_id=cmd.org_id,
                session_id=session_id,
                correlation_id=corr_id,
                rejection_reason=str(e)
            ))
            return Result.fail(e)

    async def improve_workflow(self, cmd: ImproveWorkflowCommand) -> Result[Workflow, Exception]:
        session = await self.session_repo.get_by_id(cmd.session_id)
        if not session or session.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("SESSION_NOT_FOUND", "Planning session not found."))
            
        session.add_prompt(cmd.feedback)
        session.add_feedback(PlannerFeedback(adjustment_instruction=cmd.feedback))
        
        trace_id = str(uuid.uuid4())
        trace = PlannerTrace(
            id=trace_id,
            org_id=cmd.org_id,
            session_id=session.id
        )
        
        connectors = await self.connector_repo.list_by_org(cmd.org_id)
        models = await self.model_repo.list_by_org(cmd.org_id)
        
        context = PlanningContext(
            org_id=cmd.org_id,
            available_connectors=connectors,
            available_models=models,
            history=session.prompt_history
        )
        
        existing_wf_id = session.generated_workflow_id
        
        try:
            workflow, version, execution_plan = await self.pipeline.execute(
                session=session,
                prompt=cmd.feedback,
                context=context,
                strategy_name="simple", # use simple strategy for refinement
                trace=trace
            )
            
            if existing_wf_id:
                workflow.id = existing_wf_id
                session.update_generated_workflow(existing_wf_id)
                
            # Overwrite or save new workflow/version
            await self.workflow_repo.save(workflow)
            await self.version_repo.save(version)
            await self.session_repo.save(session)
            await self.trace_repo.save(trace)
            
            return Result.ok(workflow)
        except Exception as e:
            trace.fail(str(e), duration_ms=0.0)
            await self.trace_repo.save(trace)
            return Result.fail(e)

    async def explain_workflow(self, cmd: ExplainWorkflowCommand) -> Result[Dict[str, Any], Exception]:
        session = await self.session_repo.get_by_id(cmd.session_id)
        if not session or session.org_id != cmd.org_id:
            return Result.fail(EntityNotFoundException("SESSION_NOT_FOUND", "Planning session not found."))
            
        if not session.explanation:
            return Result.ok({})
            
        return Result.ok(session.explanation.model_dump())

    async def preview_workflow(self, query: PreviewWorkflowQuery) -> Result[Dict[str, Any], Exception]:
        session = await self.session_repo.get_by_id(query.session_id)
        if not session or session.org_id != query.org_id:
            return Result.fail(EntityNotFoundException("SESSION_NOT_FOUND", "Planning session not found."))
            
        if not session.current_ast:
            return Result.ok({})
            
        return Result.ok(session.current_ast.model_dump())

    async def preview_execution_graph(self, query: PreviewExecutionGraphQuery) -> Result[Dict[str, Any], Exception]:
        session = await self.session_repo.get_by_id(query.session_id)
        if not session or session.org_id != query.org_id:
            return Result.fail(EntityNotFoundException("SESSION_NOT_FOUND", "Planning session not found."))
            
        if not session.generated_workflow_id:
            return Result.ok({})
            
        workflow = await self.workflow_repo.get_by_id(session.generated_workflow_id)
        if not workflow:
            return Result.fail(EntityNotFoundException("WORKFLOW_NOT_FOUND", "Associated workflow not found."))
            
        # Re-compile to get execution plan
        from syncsphere.workflow.infrastructure.dag.compiler import WorkflowCompiler as SharedCompiler
        plan = SharedCompiler.compile(workflow)
        return Result.ok(plan.model_dump())

    async def estimate_execution_cost(self, query: EstimateExecutionCostQuery) -> Result[float, Exception]:
        session = await self.session_repo.get_by_id(query.session_id)
        if not session or session.org_id != query.org_id:
            return Result.fail(EntityNotFoundException("SESSION_NOT_FOUND", "Planning session not found."))
            
        return Result.ok(session.metrics.total_cost if session.metrics else 0.0)

    async def estimate_execution_time(self, query: EstimateExecutionTimeQuery) -> Result[float, Exception]:
        session = await self.session_repo.get_by_id(query.session_id)
        if not session or session.org_id != query.org_id:
            return Result.fail(EntityNotFoundException("SESSION_NOT_FOUND", "Planning session not found."))
            
        return Result.ok(session.metrics.planning_time_ms if session.metrics else 0.0)
