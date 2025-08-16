import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    authentication, students, counselors, appointments, time_slots,
    public, reset_password, study_plan, notifications, admin
)
from app.database import Base, engine
from app import models  

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Academic Counseling API")

def parse_origins(value: str) -> list[str]:

    v = (value or "").strip()
    if not v:
        return []
    if v == "*":
        return ["*"]
    return [o.strip() for o in v.split(",") if o.strip()]


origins = parse_origins(os.getenv("CORS_ORIGINS", ""))
frontend_url = os.getenv("FRONTEND_URL", "").strip()
if frontend_url and frontend_url not in origins:
    origins.append(frontend_url)

if not origins:
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",

    ]

allow_all = (len(origins) == 1 and origins[0] == "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,       
)

app.include_router(authentication.router)
app.include_router(students.router)
app.include_router(counselors.router)
app.include_router(appointments.router)
app.include_router(time_slots.router)
app.include_router(public.router)
app.include_router(reset_password.router)
app.include_router(study_plan.router)
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(admin.router)


@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
