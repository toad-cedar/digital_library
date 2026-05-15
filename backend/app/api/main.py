from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.api.routers import documents, search, uploads, auth
from app.auth.casbin.bootstrap import bootstrap_policies
from app.config.settings import get_settings
from app.models import *
from app.schemas import *


@asynccontextmanager
async def lifespan(app: FastAPI):
  await asyncio.to_thread(bootstrap_policies)
  yield

app = FastAPI(
  title="Электронная библиотека для технических специальностей", 
  version="0.1.0", 
  lifespan=lifespan,
)
app.add_middleware(
  CORSMiddleware,
  allow_origins=get_settings().ALLOWED_ORIGINS,
  allow_credentials=True,
  allow_methods=["*"], # GET, POST, PUT, DELETE, PATCH, OPTIONS
  allow_headers=["*"], # Authorization, Content-Type и т.д.
)

app.include_router(auth.router, prefix="", tags=["Authentication"])
app.include_router(documents.router, prefix="", tags=["Documents"])
app.include_router(search.router, prefix="", tags=["Search"])
app.include_router(uploads.router, prefix="", tags=["Uploads"])

# TODO: Дополнительные роутеры
# app.include_router(moderation.router, prefix="", tags=["Moderation"])
# app.include_router(favorites.router, prefix="", tags=["Favorites"])
# app.include_router(groups.router, prefix="", tags=["Groups"])
# app.include_router(offline.router, prefix="", tags=["Offline"])
# app.include_router(notifications.router, prefix="", tags=["Notifications"])
# app.include_router(users.router, prefix="", tags=["Users"])
# app.include_router(admin.router, prefix="", tags=["Admin"])


@app.get("/", tags=["Health"])
def read_root():
  return {"success": True, "data": {"message": "API is working"}}
