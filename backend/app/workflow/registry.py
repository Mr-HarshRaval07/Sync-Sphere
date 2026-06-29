from app.connectors.base import BaseConnector


class ConnectorRegistry:

    def __init__(self):
        self._connectors: dict[str, BaseConnector] = {}

    def register(self, name: str, connector: BaseConnector):
        self._connectors[name] = connector

    def get(self, name: str) -> BaseConnector:
        if name not in self._connectors:
            raise ValueError(f"Connector '{name}' is not registered.")

        return self._connectors[name]