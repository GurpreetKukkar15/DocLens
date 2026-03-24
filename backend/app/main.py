from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="DocLens",
    description="Multi-document research and theme identification system",
    version="1.0.0"
)

# Allow React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register all routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to DocLens API"}