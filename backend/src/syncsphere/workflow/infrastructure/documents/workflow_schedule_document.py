from pydantic import Field
from typing import Optional
from datetime import datetime
from syncsphere.shared_kernel.infrastructure.mongodb.base_document import BaseTenantDocument


class WorkflowScheduleDocument(BaseTenantDocument):
    """Beanie ODM document for persisted workflow schedules."""
    workflow_id: str = Field(..., description="Reference to the workflow being scheduled")
    workflow_name: Optional[str] = Field(default=None)

    schedule_type: str = Field(default="once", description="once|hourly|every_x_hours|daily|weekly|monthly|cron")
    cron_expression: Optional[str] = Field(default=None, description="Raw cron expression for advanced schedules")

    start_date: Optional[str] = Field(default=None, description="ISO date string for first run")
    end_date: Optional[str] = Field(default=None, description="ISO date string for last run (optional)")
    time_of_day: Optional[str] = Field(default=None, description="HH:MM 24hr time for daily/weekly/monthly")
    timezone: str = Field(default="UTC")
    interval_hours: Optional[int] = Field(default=None, description="For every_x_hours type")
    day_of_week: Optional[int] = Field(default=None, description="0=Mon..6=Sun for weekly schedules")
    day_of_month: Optional[int] = Field(default=None, description="1-31 for monthly schedules")

    # Use boolean enabled instead of string status to match requests, or we can map it via status
    enabled: bool = Field(default=True, description="Whether the schedule is active")
    next_run_at: Optional[datetime] = Field(default=None)
    last_run_at: Optional[datetime] = Field(default=None)
    run_count: int = Field(default=0)

    created_by: Optional[str] = Field(default=None, description="User ID who created the schedule")

    class Settings:
        name = "scheduled_workflows"
        indexes = [
            "org_id",
            "workflow_id",
            ("org_id", "enabled"),
        ]
