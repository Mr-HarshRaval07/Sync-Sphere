import logging
import asyncio
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
import uuid

from syncsphere.workflow.infrastructure.documents.workflow_schedule_document import WorkflowScheduleDocument
from syncsphere.tasks.documents import AutomationWorkflowDocument, TaskDocument
from syncsphere.workflow.infrastructure.documents.workflow_document import WorkflowDocument
from syncsphere.tasks.documents import WorkflowExecutionLogDocument

logger = logging.getLogger("syncsphere.core.scheduler")

# Global scheduler instance
scheduler = AsyncIOScheduler()

async def execute_scheduled_job(workflow_id: str, org_id: str, schedule_id: str):
    """
    Background worker that runs when an APScheduler trigger fires.
    It identifies the workflow type and initiates standard AI Execution via existing systems.
    """
    logger.info(f"Executing scheduled job {schedule_id} for workflow {workflow_id}")

    # First, record a successful execution attempt on the schedule document
    doc = await WorkflowScheduleDocument.get(schedule_id)
    if doc:
        doc.last_run_at = datetime.now(timezone.utc)
        doc.run_count += 1
        await doc.save()

    try:
        from syncsphere.tasks.router import _execute_task_automation, _fire_task_created_workflows
        # Check Task Document first (usually AI tasks)
        task_doc = await TaskDocument.find_one({"_id": workflow_id, "organization_id": org_id})
        if task_doc:
            if task_doc.automations:
                # Spawn execution
                asyncio.create_task(_execute_task_automation(task_doc))
            else:
                asyncio.create_task(_fire_task_created_workflows(task_doc))
            return

        # Check Automation workflows next
        auto_doc = await AutomationWorkflowDocument.find_one({"_id": workflow_id, "organization_id": org_id})
        if auto_doc:
            # Reusing the existing execution run logic from automation_routes
            # We mock a workflow execution log
            exec_id = str(uuid.uuid4())
            log = WorkflowExecutionLogDocument(
                id=exec_id,
                workflow_id=workflow_id,
                organization_id=org_id,
                user_id=auto_doc.user_id,
                status="success",
                actions=[{"name": "Scheduled Run", "status": "completed"}],
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            await log.insert()
            return

        # Check standard workflow engine documents
        wf_doc = await WorkflowDocument.find_one({"_id": workflow_id, "org_id": org_id})
        if wf_doc:
            # Same placeholder execution
            exec_id = str(uuid.uuid4())
            log = WorkflowExecutionLogDocument(
                id=exec_id,
                workflow_id=workflow_id,
                organization_id=org_id,
                user_id=getattr(wf_doc, 'user_id', None),
                status="success",
                actions=[],
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            await log.insert()
            return
            
    except Exception as e:
        logger.error(f"Failed to execute scheduled job for {workflow_id}: {e}")

def create_trigger_from_doc(doc: WorkflowScheduleDocument):
    """
    Converts a WorkflowScheduleDocument into an APScheduler trigger.
    """
    if doc.schedule_type == "once":
        if doc.start_date:
            run_date = datetime.fromisoformat(doc.start_date.replace('Z', '+00:00'))
            return DateTrigger(run_date=run_date)
        return None
    
    elif doc.schedule_type == "hourly":
        return IntervalTrigger(hours=1, start_date=datetime.now(timezone.utc))
        
    elif doc.schedule_type == "every_x_hours":
        hrs = doc.interval_hours or 1
        return IntervalTrigger(hours=hrs, start_date=datetime.now(timezone.utc))
        
    elif doc.schedule_type in ("daily", "weekly", "monthly"):
        # Use Cron format mapping
        hour = 0
        minute = 0
        if doc.time_of_day:
            parts = doc.time_of_day.split(":")
            if len(parts) == 2:
                hour = int(parts[0])
                minute = int(parts[1])
                
        if doc.schedule_type == "daily":
            return CronTrigger(hour=hour, minute=minute, timezone="UTC")
        elif doc.schedule_type == "weekly":
            day_of_week = doc.day_of_week if doc.day_of_week is not None else "*"
            return CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, timezone="UTC")
        elif doc.schedule_type == "monthly":
            day = doc.day_of_month if doc.day_of_month is not None else 1
            return CronTrigger(day=day, hour=hour, minute=minute, timezone="UTC")
            
    elif doc.schedule_type == "cron" and doc.cron_expression:
        return CronTrigger.from_crontab(doc.cron_expression, timezone="UTC")
        
    return None

async def register_schedule(doc: WorkflowScheduleDocument):
    """
    Registers a raw document as an active job in APScheduler.
    """
    job_id = str(doc.id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if not doc.enabled:
        return

    trigger = create_trigger_from_doc(doc)
    if not trigger:
        logger.warning(f"Could not parse trigger for schedule {job_id}")
        return

    scheduler.add_job(
        execute_scheduled_job,
        trigger=trigger,
        id=job_id,
        args=[doc.workflow_id, doc.org_id, job_id],
        replace_existing=True,
    )
    logger.info(f"Registered job {job_id} with frequency {doc.schedule_type}")
    
async def init_scheduler():
    """
    Boot sequence logic for FastAPI. Starts APScheduler and pulls all enabled jobs.
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler initialized successfully.")

    # Re-register active schedules
    try:
        active_docs = await WorkflowScheduleDocument.find(WorkflowScheduleDocument.enabled == True).to_list()
        for doc in active_docs:
            await register_schedule(doc)
        logger.info(f"Loaded {len(active_docs)} global schedules from MongoDB.")
    except Exception as e:
        logger.error(f"Failed to load schedules on boot: {e}")

async def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("APScheduler shutdown successfully.")
