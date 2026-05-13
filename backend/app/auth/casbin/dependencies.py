from collections.abc import Callable
from fastapi import Depends, status, HTTPException

from app.auth.casbin.service import CasbinService
from app.config.deps import get_current_user
from app.models.user_models import User


def require_permission(permission: str) -> Callable[[User], None]:
  """Запрашивает разрешение

  Args:
      permission (str): Строка в формате [resource].[action]

  Raises:
      ValueError: Если `permission` не в виде [resource].[action]
      HTTPException: HTTP_403_FORBIDDEN - `permission` не прошло `enforce`

  Returns:
      Callable[[User], None]
  """
  parts = permission.split('.')
  if len(parts) != 2:
    raise ValueError('Permission must be in \'resource.action\' format')
  resource, action = parts

  async def dependency(current_user: User = Depends(get_current_user)) -> None:
    allowed = CasbinService.enforce(
      subject=str(current_user.id),
      resource=resource,
      action=action,
    )
    if not allowed:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permission denied",
      )
  return dependency