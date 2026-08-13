import asyncio
import signal
import sys
from syncsphere.core.lifecycle.startup import run_startup
from syncsphere.core.lifecycle.shutdown import run_shutdown
from syncsphere.shared_kernel.infrastructure.logging.logger import get_logger, configure_logging

# Configure logging at worker entrypoint
configure_logging()
logger = get_logger("syncsphere.workers.main")

class BackgroundWorker:
    """
    Main runner for SyncSphere background workers.
    Subscribes to Redis task queues and executes DAG orchestration workflows.
    """
    
    def __init__(self) -> None:
        self.running = False

    async def start(self) -> None:
        """Starts the worker event loop."""
        logger.info("Starting background worker node...")
        
        # Bootstrap dependencies using lifecycle startup
        from syncsphere.identity.infrastructure.documents import (
            OrgDocument,
            RoleDocument,
            UserDocument,
            ApiKeyDocument,
            RefreshTokenDocument,
        )
        from syncsphere.connectors.infrastructure.documents import (
            ConnectorDocument,
            ConnectorCredentialDocument,
        )
        from syncsphere.workflow.infrastructure.documents import (
            WorkflowDocument,
            WorkflowVersionDocument,
            WorkflowTemplateDocument,
        )
        await run_startup([
            OrgDocument,
            RoleDocument,
            UserDocument,
            ApiKeyDocument,
            RefreshTokenDocument,
            ConnectorDocument,
            ConnectorCredentialDocument,
            WorkflowDocument,
            WorkflowVersionDocument,
            WorkflowTemplateDocument,
        ])
        
        self.running = True
        
        # Register OS signals for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self.shutdown(s)))

        # Worker loop
        while self.running:
            logger.debug("Worker tick: Polling for background tasks...")
            await asyncio.sleep(10)

    async def shutdown(self, sig: signal.Signals) -> None:
        """Gracefully disconnects and stops the worker loop."""
        logger.info("Received exit signal: %s. Initiating graceful shutdown...", sig.name)
        self.running = False
        
        # Disconnect databases using lifecycle shutdown
        await run_shutdown()
        
        logger.info("Background worker node stopped.")
        sys.exit(0)

if __name__ == "__main__":
    worker = BackgroundWorker()
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        logger.info("Worker process terminated manually.")
