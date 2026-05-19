from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.audit_logs import router as audit_logs_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.cameras import router as cameras_router
from backend.api.routes.dispatch import router as dispatch_router
from backend.api.routes.incidents import router as incidents_router
from backend.api.routes.operators import router as operators_router
from backend.api.routes.websocket import router as websocket_router
from backend.api.routes.suspects import router as suspects_router


app = FastAPI(
    title="AN-EYE Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes.
app.include_router(auth_router)
app.include_router(audit_logs_router)
app.include_router(cameras_router)
app.include_router(dispatch_router)
app.include_router(incidents_router)
app.include_router(operators_router)
app.include_router(websocket_router)
app.include_router(suspects_router)


@app.get("/")
async def root():
    return {
        "message": "AN-EYE Backend Running",
    }
