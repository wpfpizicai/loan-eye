# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import overview, competitor, industry

app = FastAPI(title="loan-eye API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(overview.router, prefix="/api/overview", tags=["overview"])
app.include_router(competitor.router, prefix="/api/competitor", tags=["competitor"])
app.include_router(industry.router, prefix="/api/industry", tags=["industry"])

@app.get("/health")
async def health():
    return {"status": "ok"}
