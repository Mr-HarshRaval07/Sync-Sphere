from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import logging

class WorkerStrategy(ABC):
    """Abstract interface defining step execution strategy."""
    @abstractmethod
    async def execute_node(self, session, node_id: str, step_executor) -> Dict[str, Any]:
        """Runs the node execution task using the designated strategy."""
        pass

class LocalWorkerStrategy(WorkerStrategy):
    """Executes the step sequentially on the local thread."""
    async def execute_node(self, session, node_id: str, step_executor) -> Dict[str, Any]:
        return await step_executor.execute(session, node_id)

class AsyncWorkerStrategy(WorkerStrategy):
    """Executes the step asynchronously in the standard event loop, allowing concurrency."""
    async def execute_node(self, session, node_id: str, step_executor) -> Dict[str, Any]:
        # Simple async wrapper simulating concurrent scheduling
        task = asyncio.create_task(step_executor.execute(session, node_id))
        return await task

class FutureDistributedWorkerStrategy(WorkerStrategy):
    """Placeholder stub for running steps across an external distributed worker cluster."""
    async def execute_node(self, session, node_id: str, step_executor) -> Dict[str, Any]:
        logging.info("FutureDistributedWorkerStrategy: Dispatching to external worker queue.")
        return await step_executor.execute(session, node_id)

class ExecutionDispatcher:
    """Delegates step execution to the selected WorkerStrategy based on policy/settings."""
    
    def __init__(
        self,
        local_strategy: LocalWorkerStrategy,
        async_strategy: AsyncWorkerStrategy,
        distributed_strategy: FutureDistributedWorkerStrategy
    ) -> None:
        self.local_strategy = local_strategy
        self.async_strategy = async_strategy
        self.distributed_strategy = distributed_strategy

    def select_strategy(self, policy_name: str) -> WorkerStrategy:
        if policy_name == "SafeExecution":
            return self.local_strategy
        elif policy_name == "AggressiveParallelExecution":
            return self.async_strategy
        elif policy_name == "LowMemoryExecution":
            return self.local_strategy
        # Default policy: BalancedExecution
        return self.async_strategy
