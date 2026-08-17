from syncsphere.shared_kernel.types.contracts import BaseQuery

class ListWorkflowsQuery(BaseQuery):
    """Query to list workflows within organization."""
    org_id: str
    page: int = 1
    page_size: int = 20


class GetWorkflowQuery(BaseQuery):
    """Query to retrieve a single workflow profile details."""
    org_id: str
    workflow_id: str


class CompileWorkflowQuery(BaseQuery):
    """Query to compile and validate the workflow DAG into an ExecutionPlan."""
    org_id: str
    workflow_id: str


class ExportWorkflowQuery(BaseQuery):
    """Query to export a workflow configuration in JSON schema format."""
    org_id: str
    workflow_id: str
