import os


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).lower() in ("1", "true", "yes", "on")


def load_config():
    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY", "lucky-guess"),
        "DEBUG": _bool(os.environ.get("FLASK_DEBUG"), default=True),
        "SESSION_COOKIE_NAME": os.environ.get("SESSION_COOKIE_NAME", "ksp_session"),
        "DATABASE_PATH": os.environ.get("DATABASE_PATH", "instance/users.db"),
        "UPLOAD_DIR": os.environ.get("UPLOAD_DIR", "uploads"),
        "MAX_CONTENT_LENGTH": int(os.environ.get("MAX_UPLOAD_MB", "16")) * 1024 * 1024,
        "APP_BASE_URL": os.environ.get("APP_BASE_URL", "http://localhost:5000"),
        "MONGO_URI": os.environ.get("MONGO_URI", "mongodb://mongo:27017/ksp"),
        "REDIS_URL": os.environ.get("REDIS_URL", "redis://redis:6379/0"),
        "SMTP_HOST": os.environ.get("SMTP_HOST", "mailhog"),
        "SMTP_PORT": int(os.environ.get("SMTP_PORT", "1025")),
        "SMTP_FROM": os.environ.get("SMTP_FROM", "no-reply@ksp.local"),
        "LDAP_URI": os.environ.get("LDAP_URI", "ldap://openldap:1389"),
        "LDAP_BIND_DN": os.environ.get("LDAP_BIND_DN", "cn=admin,dc=ksp,dc=local"),
        "LDAP_BIND_PASSWORD": os.environ.get("LDAP_BIND_PASSWORD", "adminpassword"),
        "LDAP_BASE_DN": os.environ.get("LDAP_BASE_DN", "ou=people,dc=ksp,dc=local"),
        "OIDC_ISSUER": os.environ.get("OIDC_ISSUER", "http://dex:5556/dex"),
        "OIDC_CLIENT_ID": os.environ.get("OIDC_CLIENT_ID", "ksp-web"),
        "OIDC_CLIENT_SECRET": os.environ.get("OIDC_CLIENT_SECRET", "ksp-web-secret"),
        "OIDC_REDIRECT_BASE": os.environ.get("OIDC_REDIRECT_BASE", "http://localhost:5000"),
    }
