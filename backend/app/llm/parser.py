import json
import re


class LLMResponseParser:

    @staticmethod
    def parse_json(response: str):

        response = response.strip()

        response = re.sub(r"^```json", "", response)
        response = re.sub(r"^```", "", response)
        response = re.sub(r"```$", "", response)

        response = response.strip()

        start = response.find("{")
        end = response.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON object found.")

        response = response[start:end + 1]

        return json.loads(response)