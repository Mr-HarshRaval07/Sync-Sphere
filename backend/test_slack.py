# test_slack.py
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.integrations.slack import send_slack_message


def main():
    result = send_slack_message(channel="#all-janhvi", message="Sync Sphere is working 🚀")
    print("Slack test completed.")
    if result.get("ok"):
        print("Slack posting succeeded.")
    else:
        print("Slack posting failed:", result)
    return result


if __name__ == "__main__":
    main()