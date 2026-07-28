import logging
from typing import Any, Dict, List, Optional
from syncsphere.connectors.domain.repositories import ConnectorRepository

logger = logging.getLogger("syncsphere.approval.application.services.notification")

class NotificationService:
    """
    Notification adapter that delegates all message routing (Slack, Email, Discord, Webhook, etc.)
    to the active MCP Connector Framework instead of invoking external endpoints directly.
    """
    
    def __init__(self, connector_repo: ConnectorRepository, connector_service) -> None:
        self.connector_repo = connector_repo
        self.connector_service = connector_service

    async def send_approval_requested_notification(
        self,
        org_id: str,
        approval_id: str,
        user_ids: List[str],
        title: str
    ) -> None:
        """Sends notifications to all assigned approvers using their resolved preferred transport channels."""
        for user_id in user_ids:
            # Resolve user profile details and preference
            # For dynamic implementation we assume fallback to Slack or Email based on ID suffix/pattern
            pref = "slack"
            user_address = f"slack_channel_{user_id}"
            
            if "@" in user_id or "email" in user_id:
                pref = "email"
                user_address = user_id if "@" in user_id else f"{user_id}@syncsphere.local"
            elif "discord" in user_id:
                pref = "discord"
                user_address = f"discord_uid_{user_id}"
            elif "webhook" in user_id:
                pref = "webhook"
                user_address = f"http://localhost:8080/webhooks/approvals"
                
            msg = f"Approval Request Awaiting Decision: '{title}'. ID: {approval_id}"
            await self._dispatch_via_connector(org_id, pref, user_address, msg, approval_id)

    async def _dispatch_via_connector(
        self,
        org_id: str,
        pref: str,
        address: str,
        message: str,
        approval_id: str
    ) -> None:
        """Looks up the target connector in the registry and calls its corresponding MCP tool."""
        # Find active connector matching name prefix
        connectors = await self.connector_repo.list_by_org(org_id)
        target_connector = None
        for conn in connectors:
            if pref in conn.name.lower():
                target_connector = conn
                break
                
        if not target_connector:
            logger.warning(
                "No active MCP connector found for channel preference '%s' in org %s. Log notification fallback: %s to %s",
                pref, org_id, message, address
            )
            return
            
        # Map arguments based on connector transport specification
        tool_name = "post_message"
        args = {}
        if pref == "slack":
            tool_name = "post_message"
            args = {"channel": address, "text": message}
        elif pref == "email":
            tool_name = "send_email"
            args = {"to": address, "subject": "SyncSphere Approval Request", "body": message}
        elif pref == "discord":
            tool_name = "send_message"
            args = {"channel_id": address, "message": message}
        elif pref == "webhook":
            tool_name = "trigger_webhook"
            args = {"url": address, "payload": {"message": message, "approval_id": approval_id, "status": "pending"}}
            
        logger.info("Dispatching notification to connector '%s' via tool '%s'", target_connector.name, tool_name)
        try:
            await self.connector_service.execute_tool(
                org_id=org_id,
                connector_id=target_connector.id,
                tool_name=tool_name,
                arguments=args
            )
        except Exception as e:
            logger.exception("Failed to dispatch notification to connector %s", target_connector.id)
