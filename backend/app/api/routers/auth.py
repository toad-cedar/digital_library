from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.config.security import create_access_token, hash_password, verify_password
from app.repos.user_repo import UserRepository
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, ApiResponse
from app.config.deps import get_current_user
from app.models.user_models import User


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", response_model=ApiResponse[dict])
async def register(
  user_data: RegisterRequest,
  db_session: AsyncSession = Depends(get_db_session)
):
  repo = UserRepository(db_session)
  if await repo.get_by_username(user_data.username) or await repo.get_by_email(user_data.email):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already registered")

  new_user = User(
    username=user_data.username,
    email=user_data.email,
    password_hash=hash_password(user_data.password)
  )
  created = await repo.create(new_user)
  await db_session.commit()
  await db_session.refresh(created)
  return ApiResponse(success=True, data={"user_id": created.id})

@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
  user_data: LoginRequest,
  db_session: AsyncSession = Depends(get_db_session)
):
  repo = UserRepository(db_session)
  user = await repo.get_by_email(user_data.email)
  if not user or not verify_password(user_data.password, user.password_hash):
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

  access_token = create_access_token(data={"sub": user.username})
  refresh_token = create_access_token(data={"sub": user.username}, expires_delta=None) # В продакшене генерировать отдельно
  return ApiResponse(success=True, data=TokenResponse(access_token=access_token, refresh_token=refresh_token))

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
  return ApiResponse(success=True, data={"message": "Logged out successfully"})