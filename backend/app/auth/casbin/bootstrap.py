from app.auth.casbin.enforcer import get_enforcer
from app.auth.casbin.policies import DEFAULT_POLICIES


def bootstrap_policies() -> None:
  enforcer = get_enforcer()

  new_policies = [p for p in DEFAULT_POLICIES if not enforcer.has_policy(*p)]
  if new_policies:
    enforcer.add_policies(new_policies)
    enforcer.save_policy()