from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """
    Abstract base class for all external service connectors.
    Every external service (Jira, Slack, GitHub, etc.) should inherit from this.
    """

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection or validate credentials.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close any open resources.
        """
        pass

    @abstractmethod
    async def execute(
        self,
        action: str,
        payload: dict,
        context: dict[str, Any] | None = None,
    ) -> dict:
        """
        Execute an action on the external service.

        Parameters
        ----------
        action : str
            Name of the action to perform
            (e.g. create_issue, send_message).

        payload : dict
            Parameters required by the action.

        context : dict | None
            Results from previously executed workflow steps.
            Enables multi-step workflows where connectors can
            consume outputs from earlier connectors.

        Returns
        -------
        dict
            Result of the executed action.
        """
        pass