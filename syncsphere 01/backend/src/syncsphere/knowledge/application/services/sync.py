import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from syncsphere.knowledge.domain.entities.source import KnowledgeSource
from syncsphere.knowledge.domain.entities.sync_job import ConnectorSyncJob
from syncsphere.knowledge.domain.repositories import KnowledgeSourceRepository
from syncsphere.knowledge.application.pipeline.knowledge import KnowledgePipeline
from syncsphere.connectors.application.services.connector_service import ConnectorApplicationService

logger = logging.getLogger("syncsphere.knowledge.application.services.sync")

class ConnectorSyncService:
    """
    ConnectorSyncService coordinates replication jobs syncing document nodes
    from external MCP Connector endpoints (Jira, Slack, SQL DBs) into local indexes.
    """
    
    def __init__(
        self,
        source_repo: KnowledgeSourceRepository,
        connector_service: ConnectorApplicationService,
        knowledge_pipeline: KnowledgePipeline
    ) -> None:
        self.source_repo = source_repo
        self.connector_service = connector_service
        self.knowledge_pipeline = knowledge_pipeline

    async def run_sync(
        self,
        org_id: str,
        source_id: str,
        sync_type: str = "incremental"
    ) -> ConnectorSyncJob:
        """Triggers an external connector sync, executes remote tool query, and updates indexes."""
        source = await self.source_repo.get_by_id(source_id)
        if not source or source.org_id != org_id:
            raise ValueError(f"Knowledge source '{source_id}' not found.")
            
        connector_id = source.config.get("connector_id")
        tool_name = source.config.get("tool_name", "fetch_data")
        
        job = ConnectorSyncJob(
            org_id=org_id,
            source_id=source_id,
            sync_type=sync_type,
            connector_id=connector_id,
            id=str(uuid.uuid4())
        )
        
        job.start()
        logger.info("Starting connector sync job '%s' for source '%s'", job.id, source_id)
        
        try:
            # 1. Prepare arguments based on sync_type
            args = source.config.get("arguments", {}).copy()
            if sync_type == "incremental" and source.last_sync_at:
                args["modified_since"] = source.last_sync_at.isoformat()
                
            # 2. Invoke MCP connector tool to query external data
            raw_text = "No data fetched from connector."
            if connector_id:
                res = await self.connector_service.execute_tool(
                    org_id=org_id,
                    connector_id=connector_id,
                    tool_name=tool_name,
                    arguments=args
                )
                if res.is_fail:
                    raise res.error()
                    
                tool_res = res.value()
                # Parse text blocks from content
                text_blocks = []
                for block in tool_res.content:
                    if block.get("type") == "text":
                        text_blocks.append(block.get("text", ""))
                if text_blocks:
                    raw_text = "\n".join(text_blocks)
            else:
                # Local configuration test fallback
                raw_text = source.config.get("text", "Simulated local connector sync content.")
                
            # 3. Process retrieved content through indexing pipeline
            await self.knowledge_pipeline.execute(org_id, source, raw_content=raw_text)
            
            job.complete(records_count=1)
            logger.info("Connector sync job '%s' finished successfully.", job.id)
            return job
            
        except Exception as e:
            logger.exception("Connector sync job failed for source: %s", source_id)
            job.fail(str(e))
            return job

    async def handle_webhook(
        self,
        org_id: str,
        source_id: str,
        payload: Dict[str, Any]
    ) -> None:
        """Handles incoming webhooks, immediately updating local knowledge indices in-place."""
        source = await self.source_repo.get_by_id(source_id)
        if not source or source.org_id != org_id:
            raise ValueError(f"Knowledge source '{source_id}' not found.")
            
        logger.info("Processing webhook sync for source: %s", source_id)
        # Webhook payload content extraction
        content = payload.get("text") or payload.get("content") or str(payload)
        
        # Execute the knowledge pipeline in-place
        await self.knowledge_pipeline.execute(org_id, source, raw_content=content)
