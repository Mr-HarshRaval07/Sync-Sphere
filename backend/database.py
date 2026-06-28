import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

for env_path in (BASE_DIR / ".env", ROOT_DIR / ".env"):
    if env_path.exists():
        load_dotenv(env_path, override=False)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "syncsphere")
FALLBACK_PATH = BASE_DIR / "fallback_db.json"
USING_FALLBACK = False


def _load_fallback_data():
    if not FALLBACK_PATH.exists():
        return {"tasks": []}

    try:
        with open(FALLBACK_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"tasks": []}
        if "tasks" not in data:
            data["tasks"] = []
        return data
    except Exception:
        return {"tasks": []}


def _save_fallback_data(data):
    FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FALLBACK_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeCollection:
    def __init__(self, data, name):
        self.data = data

        self.name = name

    def insert_one(self, document):
        document = document.copy()
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
        self.data[self.name].append(document)
        _save_fallback_data(self.data)
        return FakeInsertResult(document["_id"])

    def find(self, filter_, projection=None):
        results = [doc.copy() for doc in self.data.get(self.name, [])]
        if projection and projection.get("_id") == 0:
            for doc in results:
                doc.pop("_id", None)
        return results

    def update_one(self, filter_, update):
        for doc in self.data.get(self.name, []):
            if all(doc.get(key) == value for key, value in filter_.items()):
                if "$set" in update:
                    doc.update(update["$set"])
                    _save_fallback_data(self.data)
                return

    def delete_one(self, filter_):
        items = self.data.get(self.name, [])
        for index, doc in enumerate(items):
            if all(doc.get(key) == value for key, value in filter_.items()):
                items.pop(index)
                _save_fallback_data(self.data)
                return


class FakeDb:
    def __init__(self):
        self._data = _load_fallback_data()
        self.tasks = FakeCollection(self._data, "tasks")

    def list_collection_names(self):
        return [name for name, items in self._data.items() if items]


def get_db_status():
    return {
        "using_fallback": USING_FALLBACK,
        "mongo_uri": MONGO_URI,
        "db_name": DB_NAME,
    }


try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000)
    client.admin.command("ping")
    db = client[DB_NAME]
    print(f"MongoDB connected to {MONGO_URI}")
except PyMongoError as exc:
    USING_FALLBACK = True
    print(f"Warning: MongoDB not available, using fallback storage: {exc}")
    db = FakeDb()
except Exception as exc:
    USING_FALLBACK = True
    print(f"Warning: Unexpected database error, using fallback storage: {exc}")
    db = FakeDb()