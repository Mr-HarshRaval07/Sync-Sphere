from app.connectors.base import BaseConnector


class MockConnector(BaseConnector):

    async def connect(self):
        print("Connected")

    async def disconnect(self):
        print("Disconnected")

    async def execute(self, action: str, payload: dict):
        print(f"Executing {action}")
        print(payload)

        return {
            "status": "success",
            "action": action
        }