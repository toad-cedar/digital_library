from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.api.routers import documents, search, uploads, auth
from app.auth.casbin.bootstrap import bootstrap_policies
from app.config.settings import get_settings
from app.models import __all__
from app.schemas import __all__


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


app.include_router(documents.router, prefix="/api", tags=["Documents"]) 
app.include_router(search.router,    prefix="/api", tags=["Search"])
app.include_router(uploads.router,   prefix="/api", tags=["Uploads"])
app.include_router(auth.router,      prefix="/api", tags=["Authentication"])

# TODO: Дополнительные роутеры
# app.include_router(users.router,   prefix="/api",  tags=["Users"])
# app.include_router(admin.router,   prefix="/api/admin",   tags=["Admin Panel"])
# app.include_router(teacher.router, prefix="/api/teacher", tags=["Teacher Panel"])
# app.include_router(history.router, prefix="/api",  tags=["History"])
# app.include_router(favorites.router, prefix="/api", tags=["Favorites"])
# app.include_router(offline.router, prefix="/api",  tags=["Offline Library"])
# app.include_router(groups.router,  prefix="/api",  tags=["Groups"])


@app.get("/")
def read_root():
  return { "message": "API is working" }
