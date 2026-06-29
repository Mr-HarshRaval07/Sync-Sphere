from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    return {
        "message": "Sync Sphere API"
    }