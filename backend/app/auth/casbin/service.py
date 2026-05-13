from app.auth.casbin.enforcer import get_enforcer


class CasbinService:
  @staticmethod
  def enforce(subject: str, resource: str, action: str) -> bool:
    return get_enforcer.enforce(
      subject,
      resource,
      action,
    )

  @staticmethod
  def add_role_for_user(user_id: str, role_name: str) -> None:
    get_enforcer.add_role_for_user(
      user_id,
      role_name,
    )

  @staticmethod
  def delete_role_for_user(user_id: str, role_name: str) -> None:
    get_enforcer.delete_role_for_user(
      user_id,
      role_name,
    )