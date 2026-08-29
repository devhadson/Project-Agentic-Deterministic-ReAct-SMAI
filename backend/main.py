from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
