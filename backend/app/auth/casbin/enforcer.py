import casbin
from app.auth.casbin.adapter import get_casbin_adapter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def get_enforcer() -> casbin.Enforcer:
  adapter = get_casbin_adapter()
  model_path = BASE_DIR / "model.conf"

  enforcer = casbin.Enforcer(str(model_path), adapter)
  enforcer.load_policy()

  return enforcer