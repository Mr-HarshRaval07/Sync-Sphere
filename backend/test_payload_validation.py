import json
from syncsphere.workflow.presentation.schemas import UpdateWorkflowRequest
import sys

payload = {
    "name": "test",
    "description": "desc",
    "variables": []
}

from syncsphere.workflow.presentation.schemas import CreateWorkflowRequest
try:
    req = CreateWorkflowRequest(**payload)
    print("VALID CREATE!")
except Exception as e:
    print("INVALID CREATE:", e)
