from fastapi import APIRouter
from database import db
from models.task import Task

router = APIRouter()

# create
@router.post("/tasks")
def create_task(task: Task):
    print("Received task:",task)  # Debugging line to print the received task

    result=db.tasks.insert_one(task.dict())
    print("inserted id",result.inserted_id)  # Debugging line to print the inserted ID

    return {
        "message": "Task Created"
    }

# read
@router.get("/tasks")
def get_tasks():

    tasks = list(
        db.tasks.find(
            {},
            {"_id": 0}
        )
    )

    return tasks

# update
@router.put("/tasks/{title}")
def update_task(title: str):

    db.tasks.update_one(
        {"title": title},
        {
            "$set": {
                "status": "Completed"
            }
        }
    )

    return {
        "message": "Task Updated"
    }

# delete
@router.delete("/tasks/{title}")
def delete_task(title: str):

    db.tasks.delete_one(
        {"title": title}
    )

    return {
        "message": "Task Deleted"
    }