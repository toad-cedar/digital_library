ROLE_USER      = "user"
ROLE_TEACHER   = "teacher"
ROLE_MODERATOR = "moderator"
ROLE_ADMIN     = "admin" 

# Формат кортежа: (role, resource, action)
DEFAULT_POLICIES: list[tuple[str, str, str]] = [
  (ROLE_USER, "document", "read"),
  (ROLE_USER, "upload", "create"),
  (ROLE_USER, "document", "report"),

  (ROLE_TEACHER, "group", "create"),
  (ROLE_TEACHER, "group", "manage"),
  (ROLE_TEACHER, "document", "report"),

  (ROLE_MODERATOR, "moderation", "approve"),
  (ROLE_MODERATOR, "moderation", "reject"),

  (ROLE_ADMIN, "document", "delete"),
  (ROLE_ADMIN, "user", "block"),
  (ROLE_ADMIN, "user", "manage_roles"),
  (ROLE_ADMIN, "admin", "panel"),
]