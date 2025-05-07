import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.endpoints import router as google_meridian_router

from app.config import settings


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(google_meridian_router, prefix='/meridian')


if __name__ == "__main__":
    uvicorn.run(app="app.main:app", reload=True, port=settings.PORT, host=settings.HOST)
