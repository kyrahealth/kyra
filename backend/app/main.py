from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.admin import router as admin_router
from .api.v1.auth import router as auth_router
from .api.v1.chat import router as chat_router
from .api.v1.preview import router as preview_router


app = FastAPI(title="MedHelp Chatbot – Pre‑Beta")

# --- CORS: allow your Vite dev server ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Alternative Vite port
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",  # Alternative localhost
        "http://127.0.0.1:5174",  # Alternative localhost
        "http://127.0.0.1:3000",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(preview_router)



@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
